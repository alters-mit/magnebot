from typing import List, Dict
from abc import ABC, abstractmethod
from overrides import final
import numpy as np
from scipy.spatial import cKDTree
from ikpy.chain import Chain
from ikpy.utils import geometry
from tdw.tdw_utils import TDWUtils
from tdw.robot_data.joint_type import JointType
from magnebot.ikpy.link import OriginLink, URDFLink, Link
from magnebot.arm import Arm
from magnebot.arm_joint import ArmJoint
from magnebot.ik.orientation_mode import OrientationMode
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.ik.orientation import Orientation, ORIENTATIONS
from magnebot.action_status import ActionStatus
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.image_frequency import ImageFrequency
from magnebot.actions.arm_motion import ArmMotion
from magnebot.paths import IK_ORIENTATIONS_LEFT_PATH, IK_ORIENTATIONS_RIGHT_PATH
from magnebot.constants import TORSO_MAX_Y, TORSO_MIN_Y, COLUMN_Y


class IKMotion(ArmMotion, ABC):
    # The orientations in the cloud of IK targets. Each orientation corresponds to a position in self._ik_positions.
    _CACHED_IK_ORIENTATIONS: Dict[Arm, np.array] = dict()
    for arm, ik_path in zip([Arm.left, Arm.right], [IK_ORIENTATIONS_LEFT_PATH, IK_ORIENTATIONS_RIGHT_PATH]):
        if not ik_path.exists():
            continue
        _CACHED_IK_ORIENTATIONS[arm] = np.load(str(ik_path.resolve()))

    def __init__(self, arm: Arm, orientation_mode: OrientationMode, target_orientation: TargetOrientation,
                 static: MagnebotStatic, dynamic: MagnebotDynamic, image_frequency: ImageFrequency):
        """
        :param arm: [The arm used for this action.](../arm.md)
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        :param image_frequency: [How image data will be captured during the image.](../image_frequency.md)
        """

        super().__init__(arm=arm, static=static, dynamic=dynamic, image_frequency=image_frequency)
        # The action immediately ends if the Magnebot is tipping.
        has_tipped, is_tipping = self._is_tipping()
        if has_tipped or is_tipping:
            self.status = ActionStatus.tipping
        self._arm_is_articulating: bool = False
        self._auto_orientation = orientation_mode == OrientationMode.auto and target_orientation == TargetOrientation.auto
        # If orientation modes or auto, keep the list of possible orientations empty for now. When the position is set, the list will be filled.
        if self._auto_orientation:
            self._orientations: List[Orientation] = list()
        else:
            self._orientations: List[Orientation] = [Orientation(orientation_mode=orientation_mode,
                                                                 target_orientation=target_orientation)]
        # The current index for self._orientations.
        self._orientation_index: int = 0
        self._arm_articulation_commands: List[List[dict]] = list()

    def _set_start_arm_articulation_commands(self, allow_column: bool, fixed_torso_prismatic: bool, do_prismatic_first: bool, arrived_at: float = 0.125) -> None:
        self._arm_articulation_commands.clear()
        # Get the relative target position.
        target = self._get_ik_target_position()
        # If the target is too far away, fail immediately.
        distance = np.linalg.norm(target - np.array([0, target[1], 0]))
        if distance > 0.99:
            self.status = ActionStatus.cannot_reach
            return
        # Build the list of possible orientations.
        if self._auto_orientation and len(self._orientations) == 0:
            self._orientations = IKMotion._get_ik_orientations(target=target, arm=self._arm)
        # There is no valid orientation solution.
        if self._orientation_index >= len(self._orientations):
            self.status = ActionStatus.cannot_reach
            return

        # Get the initial angles of each joint. The first angle is always 0 (the origin link).
        initial_angles = self._get_initial_angles(arm=self._arm)

        # Generate an IK chain.
        chain = Chain(name=self._arm.name, links=self._get_ik_links(allow_column=allow_column))

        orientation_mode = self._orientations[self._orientation_index].orientation_mode
        target_orientation = self._orientations[self._orientation_index].target_orientation
        # Get the IK solution.
        ik = chain.inverse_kinematics(target_position=target,
                                      initial_position=initial_angles,
                                      orientation_mode=str(orientation_mode) if isinstance(orientation_mode.value, str) else None,
                                      target_orientation=np.array(target_orientation.value) if isinstance(target_orientation.value, list) else None)
        self._orientation_index += 1
        # Get the forward kinematics matrix of the IK solution.
        transformation_matrices = chain.forward_kinematics(ik, full_kinematics=True)
        # Convert the matrix into positions (this is pulled from ikpy).
        nodes = []
        for (index, link) in enumerate(chain.links):
            (node, orientation) = geometry.from_transformation_matrix(transformation_matrices[index])
            nodes.append(node)
        # Check if the last position on the node is very close to the target.
        # If so, this IK solution is expected to succeed.
        end_node = np.array(nodes[-1][:-1])
        d = np.linalg.norm(end_node - target)
        if d > arrived_at:
            self.status = ActionStatus.cannot_reach
            return
        angles = list()
        torso_prismatic = 0
        # For the purposes of getting the angles, remove the origin link and the magnet.
        ik_angles = ik[1:-1]
        # Convert all of the angles or positions.
        for i, angle in enumerate(ik_angles):
            # This is the torso.
            if i == 1:
                if fixed_torso_prismatic is not None:
                    torso_prismatic = fixed_torso_prismatic
                    angles.append(fixed_torso_prismatic)
                else:
                    # Convert the torso value to a percentage and then to a joint position.
                    torso_prismatic = ArmMotion._y_position_to_torso_position(y_position=angle)
                    angles.append(torso_prismatic)
            # Append all other angles normally.
            else:
                angles.append(float(np.rad2deg(angle)))
        if fixed_torso_prismatic is not None:
            torso_prismatic = fixed_torso_prismatic
        # Slide the torso to the desired height.
        if do_prismatic_first:
            torso_id = self.static.arm_joints[ArmJoint.torso]
            self._arm_articulation_commands.append([{"$type": "set_prismatic_target",
                                                     "joint_id": torso_id,
                                                     "target": torso_prismatic,
                                                     "id": self.static.robot_id}])
            self._arm_articulation_commands.append(self._get_ik_commands(angles=angles, torso=False))
        # Move all joints at once (including the torso prismatic joint).
        else:
            self._arm_articulation_commands.append(self._get_ik_commands(angles=angles, torso=True))

    @staticmethod
    def _get_ik_orientations(target: np.array, arm: Arm) -> List[Orientation]:
        """
        Try to automatically choose an orientation for an IK solution.
        Our best-guess approach is to load a numpy array of known IK orientation solutions per position,
        find the position in the array closest to `target`, and use that IK orientation solution.

        For more information: https://notebook.community/Phylliade/ikpy/tutorials/Orientation
        And: https://github.com/alters-mit/magnebot/blob/main/doc/arm_articulation.md

        :param arm: The arm doing the motion.
        :param target: The target position.

        :return: A list of best guesses for IK orientation. The first element in the list is almost always the best option. The other elements are neighboring options.
        """

        # Get the index of the nearest position using scipy, and use that index to get the corresponding orientation.
        # Source: https://stackoverflow.com/questions/52364222/find-closest-similar-valuevector-inside-a-matrix
        # noinspection PyArgumentList
        orientations = [IKMotion._CACHED_IK_ORIENTATIONS[arm][cKDTree(IKMotion._CACHED_IK_ORIENTATIONS).query(target, k=1)[1]]]

        # If we couldn't find a solution, assume that there isn't one and return an empty list.
        if orientations[0] < 0:
            return []

        # Append other orientation options that are nearby.
        # noinspection PyArgumentList
        orientations.extend(list(set([IKMotion._CACHED_IK_ORIENTATIONS[arm][i] for i in
                                      cKDTree(IKMotion._CACHED_IK_ORIENTATIONS).query(target, k=9)[1] if
                                      IKMotion._CACHED_IK_ORIENTATIONS[arm][i] not in orientations])))
        return [ORIENTATIONS[o] for o in orientations if o >= 0]

    @final
    def _get_ik_commands(self, angles: np.array, torso: bool) -> List[dict]:
        """
        Convert target angles to TDW commands and append them to `_next_frame_commands`.

        :param angles: The target angles in degrees.
        :param torso: If True, add torso commands.
        """

        # Convert the IK solution into TDW commands, using the expected joint and axis order.
        commands = []
        i = 0
        joint_order_index = 0
        while i < len(angles):
            joint_name = ArmMotion._JOINT_ORDER[self._arm][joint_order_index]
            joint_id = self.static.arm_joints[joint_name]
            joint_type = self.static.joints[joint_id].joint_type
            # If this is a revolute joint, the next command includes only the next angle.
            if joint_type == JointType.revolute:
                commands.append({"$type": "set_revolute_target",
                                 "joint_id": joint_id,
                                 "target": angles[i],
                                 "id": self.static.robot_id})
                i += 1
            # If this is a spherical joint, the next command includes the next 3 angles.
            elif joint_type == JointType.spherical:
                commands.append({"$type": "set_spherical_target",
                                 "joint_id": joint_id,
                                 "target": {"x": angles[i], "y": angles[i + 1], "z": angles[i + 2]},
                                 "id": self.static.robot_id})
                i += 3
            elif joint_type == JointType.prismatic:
                # Sometimes, we want the torso at its current position.
                if torso:
                    commands.append({"$type": "set_prismatic_target",
                                     "joint_id": joint_id,
                                     "target": angles[i],
                                     "id": self.static.robot_id})
                i += 1
            else:
                raise Exception(f"Joint type not defined: {joint_type} for {joint_name}.")
            # Increment to the next joint in the order.
            joint_order_index += 1
        return commands

    def _get_initial_angles(self, arm: Arm) -> np.array:
        """
        :param arm: The arm.

        :return: The angles of the arm in the current state.
        """

        # Get the initial angles of each joint.
        # The first angle is always 0 (the origin link).
        initial_angles = [0]
        for j in ArmMotion._JOINT_ORDER[arm]:
            j_id = self.status.arm_joints[j]
            initial_angles.extend(self.dynamic.joints[j_id].angles)
        # Add the magnet.
        initial_angles.append(0)
        return np.radians(initial_angles)

    def _get_ik_links(self, allow_column: bool) -> List[Link]:
        """
        :param allow_column: If True, allow the column to twist.

        :return: A list of IK links for a chain.
        """

        links: List[Link] = [OriginLink()]
        if allow_column:
            links.append(URDFLink(name="column",
                                  translation_vector=np.array([0, COLUMN_Y, 0]),
                                  orientation=np.array([0, 0, 0]),
                                  rotation=np.array([0, 1, 0]),
                                  bounds=(np.deg2rad(-179), np.deg2rad(179))))
        else:
            links.append(URDFLink(name="column",
                                  translation_vector=np.array([0, COLUMN_Y, 0]),
                                  orientation=np.array([0, 0, 0]),
                                  rotation=None))
        links.extend([URDFLink(name="torso",
                               translation_vector=np.array([0, 0, 0]),
                               orientation=np.array([0, 0, 0]),
                               rotation=np.array([0, 1, 0]),
                               is_revolute=False,
                               use_symbolic_matrix=False,
                               bounds=(TORSO_MIN_Y, TORSO_MAX_Y)),
                      URDFLink(name="shoulder_pitch",
                               translation_vector=np.array([0.215 * (-1 if self._arm == Arm.left else 1), 0.059, 0.019]),
                               orientation=np.array([0, 0, 0]),
                               rotation=np.array([1, 0, 0]),
                               bounds=(np.deg2rad(-150), np.deg2rad(70))),
                      URDFLink(name="shoulder_roll",
                               translation_vector=np.array([0, 0, 0]),
                               orientation=np.array([0, 0, 0]),
                               rotation=np.array([0, 1, 0]),
                               bounds=(np.deg2rad(-70 if self._arm == Arm.left else -45),
                                       np.deg2rad(45 if self._arm == Arm.left else 70))),
                      URDFLink(name="shoulder_yaw",
                               translation_vector=np.array([0, 0, 0]),
                               orientation=np.array([0, 0, 0]),
                               rotation=np.array([0, 0, 1]),
                               bounds=(np.deg2rad(-110 if self._arm == Arm.left else -20),
                                       np.deg2rad(20 if self._arm == Arm.left else 110))),
                      URDFLink(name="elbow_pitch",
                               translation_vector=np.array([0.033 * (-1 if self._arm == Arm.left else 1), -0.33, 0]),
                               orientation=np.array([0, 0, 0]),
                               rotation=np.array([-1, 0, 0]),
                               bounds=(np.deg2rad(-90), np.deg2rad(145))),
                      URDFLink(name="wrist_pitch",
                               translation_vector=np.array([0, -0.373, 0]),
                               orientation=np.array([0, 0, 0]),
                               rotation=np.array([-1, 0, 0]),
                               bounds=(np.deg2rad(-90), np.deg2rad(90))),
                      URDFLink(name="wrist_roll",
                               translation_vector=np.array([0, 0, 0]),
                               orientation=np.array([0, 0, 0]),
                               rotation=np.array([0, -1, 0]),
                               bounds=(np.deg2rad(-90), np.deg2rad(90))),
                      URDFLink(name="wrist_yaw",
                               translation_vector=np.array([0, 0, 0]),
                               orientation=np.array([0, 0, 0]),
                               rotation=np.array([0, 0, 1]),
                               bounds=(np.deg2rad(-15), np.deg2rad(15))),
                      URDFLink(name="magnet",
                               translation_vector=np.array([0, -0.095, 0]),
                               orientation=np.array([0, 0, 0]),
                               rotation=None)])
        return links

    @abstractmethod
    def _get_ik_target_position(self) -> np.array:
        """
        :return: The target position for the IK motion RELATIVE to the Magnebot.
        """

        raise Exception()