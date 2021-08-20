from typing import Dict, List
from tdw.add_ons.agents.robot_data.robot_static import RobotStatic
from magnebot.arm import Arm
from magnebot.wheel import Wheel
from magnebot.arm_joint import ArmJoint


class MagnebotStatic(RobotStatic):
    """
    Static data for the Magnebot. See: `Magnebot.magnebot_static`

    ```python
    from magnebot import Magnebot

    m = Magnebot()
    m.init_scene()
    print(m.magnebot_static.magnets)
    ```
    """

    def __init__(self, robot_id: int, resp: List[bytes]):
        super().__init__(robot_id=robot_id, resp=resp)
        """:field
        The name and ID of each arm joint. Key = The [`ArmJoint` enum value](arm_joint.md). Value = The object ID.
        """
        self.arm_joints: Dict[ArmJoint, int] = dict()
        """:field
        The object IDs of each wheel. Key = The [`Wheel` enum value](wheel.md).
        """
        self.wheels: Dict[Wheel, int] = dict()
        """:field
        The object IDs of each magnet. Key = The [enum value of the `Arm`](arm.md) attached to the magnet.
        """
        self.magnets: Dict[Arm, int] = dict()
        """:field
        The ID of the Magnebot's avatar.
        """
        self.avatar_id: str = str(robot_id)

        for joint_name in self.joint_names:
            joint_id = self.joint_names[joint_name]
            if "wheel" in joint_name:
                self.wheels[Wheel[joint_name]] = joint_id
            elif "magnet" in joint_name:
                self.magnets[Arm.left if "left" in joint_name else Arm.right] = joint_id
            elif self.joints[joint_id].root:
                continue
            else:
                self.arm_joints[ArmJoint[joint_name]] = joint_id
