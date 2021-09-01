from typing import List
from tdw.robot_data.joint_type import JointType
from magnebot.arm_joint import ArmJoint
from magnebot.action_status import ActionStatus
from magnebot.actions.arm_motion import ArmMotion


class ResetArm(ArmMotion):
    """
    Reset an arm to its neutral position.
    """

    def get_initialization_commands(self, resp: List[bytes]) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp)
        commands.append({"$type": "set_prismatic_target",
                         "joint_id": self.static.arm_joints[ArmJoint.torso],
                         "target": 1,
                         "id": self.static.robot_id})
        # Reset every arm joint after the torso.
        for joint_name in ArmMotion._JOINT_ORDER[self._arm][1:]:
            joint_id = self.static.arm_joints[joint_name]
            joint_type = self.static.joints[joint_id].joint_type
            if joint_type == JointType.revolute:
                # Set the revolute joints to 0 except for the elbow, which should be held at a right angle.
                commands.append({"$type": "set_revolute_target",
                                 "joint_id": joint_id,
                                 "target": 0 if "elbow" not in joint_name.name else 90,
                                 "id": self.static.robot_id})
            elif joint_type == JointType.spherical:
                commands.append({"$type": "set_spherical_target",
                                 "joint_id": joint_id,
                                 "target": {"x": 0, "y": 0, "z": 0},
                                 "id": self.static.robot_id})
        return commands

    def get_ongoing_commands(self, resp: List[bytes]) -> List[dict]:
        if not self._joints_are_moving():
            self.status = ActionStatus.success
        return []
