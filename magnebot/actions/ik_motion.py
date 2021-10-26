from typing import List, Dict
from abc import ABC, abstractmethod
from overrides import final
import numpy as np
from scipy.spatial import cKDTree
from ikpy.chain import Chain
from ikpy.utils import geometry
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
from magnebot.actions.arm_motion import ArmMotion
from magnebot.paths import IK_ORIENTATIONS_LEFT_PATH, IK_ORIENTATIONS_RIGHT_PATH, IK_POSITIONS_PATH
from magnebot.constants import TORSO_MAX_Y, TORSO_MIN_Y, COLUMN_Y, DEFAULT_TORSO_Y


class IKMotion(ArmMotion, ABC):
    """
    Abstract base class for arm motions that utilize IK.
    """

    # The orientations in the cloud of IK targets. Each orientation corresponds to a position in self._ik_positions.
    _CACHED_IK_ORIENTATIONS: Dict[Arm, np.array] = dict()
    for arm, ik_path in zip([Arm.left, Arm.right], [IK_ORIENTATIONS_LEFT_PATH, IK_ORIENTATIONS_RIGHT_PATH]):
        if not ik_path.exists():
            continue
        _CACHED_IK_ORIENTATIONS[arm] = np.load(str(ik_path.resolve()))
    _CACHED_IK_POSITIONS: np.array = np.load(str(IK_POSITIONS_PATH.resolve()))
    # Cached IK chains.
    _IK_CHAINS: Dict[Arm, Chain] = dict()
    # When sliding the torso first (i.e. to reach an object above the Magnebot's shoulder height), slide it slightly higher than the target.
    _EXTRA_TORSO_HEIGHT: float = 0.05

    def __init__(self, arm: Arm, orientation_mode: OrientationMode, target_orientation: TargetOrientation,
                 dynamic: MagnebotDynamic):
        """
        :param arm: [The arm used for this action.](../arm.md)
        :param orientation_mode: [The orientation mode.](../ik/orientation_mode.md)
        :param target_orientation: [The target orientation.](../ik/target_orientation.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        """

        # Cache the IK chains.
        if len(IKMotion._IK_CHAINS) == 0:
            IKMotion._IK_CHAINS = {Arm.left: Chain(name=Arm.left.name, links=IKMotion._get_ik_links(Arm.left)),
                                   Arm.right: Chain(name=Arm.right.name, links=IKMotion._get_ik_links(Arm.right))}

        super().__init__(arm=arm)
        # The action immediately ends if the Magnebot is tipping.
        has_tipped, is_tipping = self._is_tipping(dynamic=dynamic)
        if has_tipped or is_tipping:
            self.status = ActionStatus.tipping
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
        self._slide_torso: bool = False

    def _set_start_arm_articulation_commands(self, static: MagnebotStatic, dynamic: MagnebotDynamic, arrived_at: float = 0.125) -> None:
        """
        Set the lists of commands for arm articulation.

        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        :param arrived_at: If the magnet is this distance from the target, it has arrived.
        """

        self._slide_torso = False
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
            self.status = self._get_fail_status()
            return

        # Get the initial angles of each joint. The first angle is always 0 (the origin link).
        initial_angles = self._get_initial_angles(arm=self._arm, dynamic=dynamic, static=static)
        orientation_mode = self._orientations[self._orientation_index].orientation_mode
        target_orientation = self._orientations[self._orientation_index].target_orientation
        # Get the IK solution.
        ik = IKMotion._IK_CHAINS[self._arm].inverse_kinematics(target_position=target,
                                                               initial_position=initial_angles,
                                                               orientation_mode=orientation_mode.value if isinstance(
                                                                   orientation_mode.value, str) else None,
                                                               target_orientation=np.array(
                                                                   target_orientation.value) if isinstance(
                                                                   target_orientation.value, list) else None)
        # Increment the orientation index for the next attempt.
        self._orientation_index += 1
        # Get the forward kinematics matrix of the IK solution.
        transformation_matrices = IKMotion._IK_CHAINS[self._arm].forward_kinematics(ik, full_kinematics=True)
        # Convert the matrix into positions (this is pulled from ikpy).
        nodes = []
        for (index, link) in enumerate(IKMotion._IK_CHAINS[self._arm].links):
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
                # Convert the torso value to a percentage and then to a joint position.
                torso_prismatic = self._y_position_to_torso_position(y_position=angle)
                angles.append(torso_prismatic)
            # Append all other angles normally.
            else:
                angles.append(float(np.rad2deg(angle)))
        # Slide the torso to the desired height.
        if target[1] > DEFAULT_TORSO_Y:
            torso_id = static.arm_joints[ArmJoint.torso]
            self._arm_articulation_commands.append([{"$type": "set_prismatic_target",
                                                     "joint_id": torso_id,
                                                     "target": torso_prismatic + IKMotion._EXTRA_TORSO_HEIGHT,
                                                     "id": static.robot_id}])
            self._arm_articulation_commands.append(self._get_ik_commands(angles=angles, static=static))
            self._slide_torso = True
        # Move all joints at once (including the torso prismatic joint).
        else:
            self._arm_articulation_commands.append(self._get_ik_commands(angles=angles, static=static))

    def _evaluate_arm_articulation(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        """
        Continue an arm articulation motion.

        :param resp: The response from the build.
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)

        :return: A list of commands to continue or stop the motion.
        """

        if self.status != ActionStatus.ongoing:
            return []
        num_commands = len(self._arm_articulation_commands)
        # Move the torso first.
        if num_commands == 2 and self._slide_torso:
            return self._arm_articulation_commands.pop(0)
        elif num_commands == 1:
            # Wait until the torso stops moving.
            if self._slide_torso:
                # Start moving everything else.
                if not dynamic.joints[static.arm_joints[ArmJoint.torso]].moving:
                    commands = [{"$type": "set_prismatic_target",
                                 "joint_id": static.arm_joints[ArmJoint.torso],
                                 "target": self._y_position_to_torso_position(float(
                                     np.radians(dynamic.joints[static.arm_joints[ArmJoint.torso]].angles[0]))),
                                 "id": static.robot_id}]
                    commands.extend(self._arm_articulation_commands.pop(0))
                    return commands
                else:
                    return []
            # Star moving everything at once.
            else:
                return self._arm_articulation_commands.pop(0)
        elif num_commands == 0:
            # Stop the arms.
            if not self._joints_are_moving(static=static, dynamic=dynamic):
                if self._is_success(resp=resp, static=static, dynamic=dynamic):
                    self.status = ActionStatus.success
                else:
                    # Try again. Possibly fail.
                    self._set_start_arm_articulation_commands(static=static, dynamic=dynamic)
            # Continue the action.
            else:
                # Succeed during the action.
                if self._is_success(resp=resp, static=static, dynamic=dynamic):
                    self.status = ActionStatus.success
            return []
        else:
            raise Exception(f"Invalid commands: {self._arm_articulation_commands}")

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
        orientations = [IKMotion._CACHED_IK_ORIENTATIONS[arm][cKDTree(IKMotion._CACHED_IK_POSITIONS).query(target, k=1)[1]]]

        # If we couldn't find a solution, assume that there isn't one and return an empty list.
        if orientations[0] < 0:
            return []

        # Append other orientation options that are nearby.
        # noinspection PyArgumentList
        orientations.extend(list(set([IKMotion._CACHED_IK_ORIENTATIONS[arm][i] for i in
                                      cKDTree(IKMotion._CACHED_IK_POSITIONS).query(target, k=9)[1] if
                                      IKMotion._CACHED_IK_ORIENTATIONS[arm][i] not in orientations])))
        return [ORIENTATIONS[o] for o in orientations if o >= 0]

    @final
    def _get_ik_commands(self, angles: np.array, static: MagnebotStatic) -> List[dict]:
        """
        Convert target angles to TDW commands and append them to `_next_frame_commands`.

        :param angles: The target angles in degrees.
        :param static: [The static Magnebot data.](../magnebot_static.md)
        """

        # Convert the IK solution into TDW commands, using the expected joint and axis order.
        commands = []
        i = 0
        joint_order_index = 0
        while i < len(angles):
            joint_name = ArmMotion.JOINT_ORDER[self._arm][joint_order_index]
            joint_id = static.arm_joints[joint_name]
            joint_type = static.joints[joint_id].joint_type
            # If this is a revolute joint, the next command includes only the next angle.
            if joint_type == JointType.revolute:
                commands.append({"$type": "set_revolute_target",
                                 "joint_id": joint_id,
                                 "target": angles[i],
                                 "id": static.robot_id})
                i += 1
            # If this is a spherical joint, the next command includes the next 3 angles.
            elif joint_type == JointType.spherical:
                commands.append({"$type": "set_spherical_target",
                                 "joint_id": joint_id,
                                 "target": {"x": angles[i], "y": angles[i + 1], "z": angles[i + 2]},
                                 "id": static.robot_id})
                i += 3
            elif joint_type == JointType.prismatic:
                commands.append({"$type": "set_prismatic_target",
                                 "joint_id": joint_id,
                                 "target": angles[i],
                                 "id": static.robot_id})
                i += 1
            else:
                raise Exception(f"Joint type not defined: {joint_type} for {joint_name}.")
            # Increment to the next joint in the order.
            joint_order_index += 1
        return commands

    @staticmethod
    def _get_ik_links(arm: Arm) -> List[Link]:
        """
        :param arm: The arm.

        :return: A list of IK links for a chain.
        """

        return [OriginLink(),
                URDFLink(name="column",
                         translation_vector=np.array([0, COLUMN_Y, 0]),
                         orientation=np.array([0, 0, 0]),
                         rotation=np.array([0, 1, 0]),
                         bounds=(np.deg2rad(-179), np.deg2rad(179))),
                URDFLink(name="torso",
                         translation_vector=np.array([0, 0, 0]),
                         orientation=np.array([0, 0, 0]),
                         rotation=np.array([0, 1, 0]),
                         is_revolute=False,
                         use_symbolic_matrix=False,
                         bounds=(TORSO_MIN_Y, TORSO_MAX_Y)),
                URDFLink(name="shoulder_pitch",
                         translation_vector=np.array([0.215 * (-1 if arm == Arm.left else 1), 0.059, 0.019]),
                         orientation=np.array([0, 0, 0]),
                         rotation=np.array([1, 0, 0]),
                         bounds=(np.deg2rad(-150), np.deg2rad(70))),
                URDFLink(name="shoulder_roll",
                         translation_vector=np.array([0, 0, 0]),
                         orientation=np.array([0, 0, 0]),
                         rotation=np.array([0, 1, 0]),
                         bounds=(np.deg2rad(-70 if arm == Arm.left else -45),
                                 np.deg2rad(45 if arm == Arm.left else 70))),
                URDFLink(name="shoulder_yaw",
                         translation_vector=np.array([0, 0, 0]),
                         orientation=np.array([0, 0, 0]),
                         rotation=np.array([0, 0, 1]),
                         bounds=(np.deg2rad(-110 if arm == Arm.left else -20),
                                 np.deg2rad(20 if arm == Arm.left else 110))),
                URDFLink(name="elbow_pitch",
                         translation_vector=np.array([0.033 * (-1 if arm == Arm.left else 1), -0.33, 0]),
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
                         rotation=None)]

    @abstractmethod
    def _get_ik_target_position(self) -> np.array:
        """
        :return: The target position for the IK motion RELATIVE to the Magnebot.
        """

        raise Exception()

    @abstractmethod
    def _is_success(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> bool:
        """
        :param resp: The response from the build.
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)

        :return: True if the action was successful.
        """

        raise Exception()

    @abstractmethod
    def _get_fail_status(self) -> ActionStatus:
        """
        :return: The failure action status.
        """

        raise Exception()
