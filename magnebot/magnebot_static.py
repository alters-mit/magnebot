from typing import Dict
from tdw.output_data import StaticRobot
from magnebot.body_part_static import BodyPartStatic
from magnebot.arm import Arm
from magnebot.arm_joint import ArmJoint
from magnebot.wheel import Wheel


class MagnebotStatic:
    """
    Static data for the Magnebot. See: `Magnebot.magnebot_static`

    ```python
    from magnebot import Magnebot

    m = Magnetbot()
    m.init_scene(scene="2a", layout=1)
    print(m.magnebot_static.magnets)
    ```

    ***

    ## Fields

    - `body_parts` [Static body part info](body_part_static.md) for each body part. Key = the body part object ID.

    ```python
    from magnebot import Magnebot

    m = Magnetbot()
    m.init_scene(scene="2a", layout=1)

    # Print the object ID and segmentation color of each body part.
    for b_id in m.magnebot_static.body_parts:
        print(b_id, m.magnebot_static.body_parts[b_id].segmentation_color)
    ```

    - `arm_joints` The object of each arm joint. Key = The [arm](arm.md).
      Value = A dictionary of [`ArmJoint` enum values](arm_joint.md) and their object IDs.

    ```python
    from magnebot import Magnebot, Arm, ArmJoint


    m = Magnetbot()
    m.init_scene(scene="2a", layout=1)

    # Print the object ID of the left shoulder.
    print(m.magnebot_static.arm_joints[Arm.left][ArmJoint.shoulder])
    ```

    - `wheels` The object IDs of each wheel. Key = the name of the wheel as an [`Wheel` enum value](wheel.md).
    - `magnets` The object IDs of each magnet. Key = the [`Arm`](arm.md) attached to the magnet.

    ***

    ## Functions

    """

    def __init__(self, static_robot: StaticRobot):
        self.body_parts: Dict[int, BodyPartStatic] = dict()
        self.arm_joints: Dict[Arm, Dict[ArmJoint, int]] = {Arm.left: dict(),
                                                           Arm.right: dict()}
        self.wheels: Dict[Wheel, int] = dict()
        self.magnets: Dict[Arm, int] = dict()

        for i in range(static_robot.get_num_joints()):
            body_part_id = static_robot.get_joint_id(i)
            # Cache the body parts.
            self.body_parts[body_part_id] = BodyPartStatic(sr=static_robot, index=i)
            # Cache the wheels.
            body_part_name = static_robot.get_joint_name(i)
            if "wheel" in body_part_name:
                self.wheels[Wheel[body_part_name]] = body_part_id
            elif "magnet" in body_part_name:
                self.magnets[Arm.left if "left" in body_part_name else Arm.right] = body_part_id
            else:
                self.arm_joints[Arm.left if "left" in body_part_name else Arm.right][ArmJoint[body_part_name]] \
                    = body_part_id
