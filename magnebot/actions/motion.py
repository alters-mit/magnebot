from typing import List, Dict, Tuple
from abc import ABC
from overrides import final
import numpy as np
from tdw.tdw_utils import TDWUtils
from magnebot.actions.action import Action
from magnebot.actions.image_frequency import ImageFrequency
from magnebot.action_status import ActionStatus
from magnebot.arm_joint import ArmJoint
from magnebot.joint_type import JointType
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.constants import TORSO_MAX_Y, TORSO_MIN_Y


class Motion(Action, ABC):
    """
    These actions are motions such as turning or arm articulation.
    """

    # The type of each joint.
    _JOINT_TYPES: Dict[ArmJoint, JointType] = {ArmJoint.column: JointType.revolute,
                                               ArmJoint.torso: JointType.prismatic,
                                               ArmJoint.shoulder_left: JointType.spherical,
                                               ArmJoint.elbow_left: JointType.revolute,
                                               ArmJoint.wrist_left: JointType.spherical,
                                               ArmJoint.shoulder_right: JointType.spherical,
                                               ArmJoint.elbow_right: JointType.revolute,
                                               ArmJoint.wrist_right: JointType.spherical}

    def __init__(self, static: MagnebotStatic, dynamic: MagnebotDynamic, image_frequency: ImageFrequency):
        """
        :param static: [The static Magnebot data.](magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](magnebot_dynamic.md)
        :param image_frequency: [How image data will be captured during the image.](image_frequency.md)
        """

        super().__init__(static=static, dynamic=dynamic, image_frequency=image_frequency)
        # The number of times we've attempted a joint motion.
        self.__num_motion_attempts: int = 0

    @final
    def _do_joint_motion(self, joint_ids: List[int] = None) -> ActionStatus:
        """
        Wait until the joints have stopped moving.

        :param joint_ids: The joint IDs to listen for. If None, listen for all joint IDs.

        :return: An `ActionStatus` indicating if the arms stopped moving and if so, why.
        """

        if joint_ids is None:
            joint_ids = list(self.static.arm_joints.values())
        for joint_id in joint_ids:
            if self.dynamic.joints[joint_id].moving:
                return ActionStatus.ongoing
        return ActionStatus.success

    @final
    def _stop_joints(self, joint_ids: List[int] = None) -> List[dict]:
        """
        Set the target angle of joints to their current angles.

        :param joint_ids: The joints to stop. If empty, stop all arm joints.
        
        :return: A list of commands to stop joint movement.
        """

        if joint_ids is None:
            joint_ids = list(self.static.arm_joints.values())
        commands = []
        for joint_id in joint_ids:
            joint_name = self.static.joints[joint_id].name
            arm_joint = ArmJoint[joint_name]
            joint_axis = Motion._JOINT_TYPES[arm_joint]
            # Set the arm joints to their current positions.
            if joint_axis == JointType.revolute:
                commands.append({"$type": "set_revolute_target",
                                 "id": self.static.robot_id,
                                 "joint_id": joint_id,
                                 "target": float(self.dynamic.joints[joint_id].angles[0])})
            elif joint_axis == JointType.spherical:
                commands.append({"$type": "set_spherical_target",
                                 "id": self.static.robot_id,
                                 "joint_id": joint_id,
                                 "target": TDWUtils.array_to_vector3(self.dynamic.joints[joint_id].angles[joint_id])})
            elif joint_axis == JointType.prismatic:
                commands.append({"$type": "set_spherical_target",
                                 "id": self.static.robot_id,
                                 "joint_id": joint_id,
                                 "target": float(np.radians(self.dynamic.joints[joint_id].angles[joint_id]))})
        return commands

    @final
    def _is_tipping(self) -> Tuple[bool, bool]:
        """
        :return: Tuple: True if the Magnebot has tipped over; True if the Magnebot is tipping.
        """

        bottom_top_distance = np.linalg.norm(np.array([self.dynamic.transform.position[0],
                                                       self.dynamic.transform.position[2]]) -
                                             np.array([self.dynamic.top[0], self.dynamic.top[2]]))
        return bottom_top_distance > 1.7, bottom_top_distance > 0.4

    @staticmethod
    def _y_position_to_torso_position(y_position: float) -> float:
        """
        :param y_position: A y positional value in meters.

        :return: A corresponding joint position value for the torso prismatic joint.
        """

        # Convert the torso value to a percentage and then to a joint position.
        p = (y_position * (TORSO_MAX_Y - TORSO_MIN_Y)) + TORSO_MIN_Y
        return float(p * 1.5)
