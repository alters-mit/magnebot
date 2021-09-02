from typing import List, Dict
from abc import ABC
from overrides import final
import numpy as np
from tdw.robot_data.joint_type import JointType
from tdw.tdw_utils import TDWUtils
from magnebot.arm import Arm
from magnebot.arm_joint import ArmJoint
from magnebot.actions.action import Action
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.image_frequency import ImageFrequency


class ArmMotion(Action, ABC):
    """
    Abstract base class for arm motions.
    """

    # The order in which joint angles will be set.
    _JOINT_ORDER: Dict[Arm, List[ArmJoint]] = {Arm.left: [ArmJoint.column,
                                                          ArmJoint.torso,
                                                          ArmJoint.shoulder_left,
                                                          ArmJoint.elbow_left,
                                                          ArmJoint.wrist_left],
                                               Arm.right: [ArmJoint.column,
                                                           ArmJoint.torso,
                                                           ArmJoint.shoulder_right,
                                                           ArmJoint.elbow_right,
                                                           ArmJoint.wrist_right]}

    def __init__(self, arm: Arm, static: MagnebotStatic, dynamic: MagnebotDynamic, image_frequency: ImageFrequency):
        """
        :param arm: [The arm used for this action.](../arm.md)
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        :param image_frequency: [How image data will be captured during the image.](../image_frequency.md)
        """

        super().__init__(static=static, dynamic=dynamic, image_frequency=image_frequency)
        # The arm used for the action.
        self._arm: Arm = arm

    def get_initialization_commands(self, resp: List[bytes]) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp)
        # Make the Magnebot immovable.
        if not self.dynamic.immovable:
            commands.append({"$type": "set_immovable",
                             "immovable": True,
                             "id": self.static.robot_id})
        return commands

    def get_end_commands(self, resp: List[bytes]) -> List[dict]:
        commands = super().get_end_commands(resp=resp)
        commands.extend(self._get_stop_arm_commands())
        return commands

    def _get_stop_arm_commands(self) -> List[dict]:
        """
        :return: A list of commands to stop the arm's joints.
        """

        commands = []
        for arm_joint in ArmMotion._JOINT_ORDER[self._arm]:
            joint_id = self.static.arm_joints[arm_joint]
            angles = self.dynamic.joints[joint_id].angles
            joint_type = self.static.joints[joint_id].joint_type
            if joint_type == JointType.fixed_joint:
                continue
            # Set the target to the angle of the first (and only) revolute drive.
            elif joint_type == JointType.revolute:
                commands.append({"$type": "set_revolute_target",
                                 "joint_id": joint_id,
                                 "target": float(angles[0]),
                                 "id": self.static.robot_id})
            # Convert the current prismatic "angle" back into "radians".
            elif joint_type == JointType.prismatic:
                commands.append({"$type": "set_prismatic_target",
                                 "joint_id": joint_id,
                                 "target": float(np.radians(angles[0])),
                                 "id": self.static.robot_id})
            # Set each spherical drive axis.
            elif joint_type == JointType.spherical:
                commands.append({"$type": "set_spherical_target",
                                 "target": TDWUtils.array_to_vector3(angles),
                                 "joint_id": joint_id,
                                 "id": self.static.robot_id})
            else:
                raise Exception(f"Cannot stop joint type {joint_type}")
        return commands

    @final
    def _joints_are_moving(self) -> bool:
        """
        :return: True if these joints are still moving.
        """

        for arm_joint in ArmMotion._JOINT_ORDER[self._arm]:
            if self.dynamic.joints[self.static.arm_joints[arm_joint]].moving:
                return True
        return False
