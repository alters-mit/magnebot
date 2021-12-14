from typing import Dict, List
from tdw.robot_data.robot_static import RobotStatic
from magnebot.arm import Arm
from magnebot.wheel import Wheel
from magnebot.arm_joint import ArmJoint


class MagnebotStatic(RobotStatic):
    """
    Static data for the Magnebot.

    With a [`Magnebot` agent](magnebot.md):

    ```python
    from tdw.controller import Controller
    from tdw.tdw_utils import TDWUtils
    from magnebot.magnebot import Magnebot

    m = Magnebot(robot_id=0, position={"x": 0.5, "y": 0, "z": -1})
    c = Controller()
    c.add_ons.append(m)
    c.communicate(TDWUtils.create_empty_room(12, 12))
    for magnet in m.static.magnets:
        magnet_id = m.static.magnets[magnet]
        print(magnet, magnet_id)
    c.communicate({"$type": "terminate"})
    ```

    With a single-agent [`MagnebotController`](magnebot_controller.md):

    ```python
    from magnebot import MagnebotController

    m = MagnebotController()
    m.init_scene()
    for magnet in m.magnebot.static.magnets:
        magnet_id = m.magnebot.static.magnets[magnet]
        print(magnet, magnet_id)
    m.end()
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
        The ID of the Magnebot's avatar (camera). This is used internally for API calls.
        """
        self.avatar_id: str = str(robot_id)

        for joint_name in self.joint_ids_by_name:
            joint_id = self.joint_ids_by_name[joint_name]
            if "wheel" in joint_name:
                self.wheels[Wheel[joint_name]] = joint_id
            elif "magnet" in joint_name:
                self.magnets[Arm.left if "left" in joint_name else Arm.right] = joint_id
            elif self.joints[joint_id].root:
                continue
            else:
                self.arm_joints[ArmJoint[joint_name]] = joint_id
