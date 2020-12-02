from typing import Dict
from tdw.output_data import StaticRobot
from magnebot.body_part_static import BodyPartStatic
from magnebot.arm import Arm
from magnebot.wheel import Wheel
from magnebot.arm_joint import ArmJoint


class MagnebotStatic:
    """
    Static data for the Magnebot. See: `Magnebot.magnebot_static`

    ```python
    from magnebot import Magnebot

    m = Magnebot()
    m.init_scene(scene="2a", layout=1)
    print(m.magnebot_static.magnets)
    ```
    """

    def __init__(self, static_robot: StaticRobot):
        """
        :param static_robot: Static robot output data.
        """

        """:field
        [Static body part info](body_part_static.md) for each body part. Key = The body part object ID.
        
        ```python
        from magnebot import Magnebot

        m = Magnebot()
        m.init_scene(scene="2a", layout=1)

        # Print the object ID and segmentation color of each body part.
        for b_id in m.magnebot_static.body_parts:
            print(b_id, m.magnebot_static.body_parts[b_id].segmentation_color)
        ```
        """
        self.body_parts: Dict[int, BodyPartStatic] = dict()

        """:field
        The object of each arm joint. Key = The [`ArmJoint` enum value](arm_joint.md). Value = The object ID.
        
        ```python
        from magnebot import Magnebot, ArmJoint

        m = Magnebot()
        m.init_scene(scene="2a", layout=1)
        
        # Print the object ID and segmentation color of the left shoulder.
        b_id = m.magnebot_static.arm_joints[ArmJoint.shoulder_left]
        color = m.magnebot_static.body_parts[b_id].segmentation_color
        print(b_id, color)
        ```
        """
        self.arm_joints: Dict[ArmJoint, int] = dict()

        """:field
        The object IDs of each wheel. Key = The [`Wheel` enum value](wheel.md).
        
        ```python
        from magnebot import Magnebot, Wheel

        m = Magnebot()
        m.init_scene(scene="2a", layout=1)

        # Print the object ID and segmentation color of the left back wheel.
        b_id = m.magnebot_static.wheels[Wheel.wheel_left_back]
        color = m.magnebot_static.body_parts[b_id].segmentation_color
        print(b_id, color)
        ```
        """
        self.wheels: Dict[Wheel, int] = dict()
        """:field
        The object IDs of each magnet. Key = The [enum value of the `Arm`](arm.md) attached to the magnet.
        
        ```python
        from magnebot import Magnebot, Arm

        m = Magnebot()
        m.init_scene(scene="2a", layout=1)

        # Print the object ID and the segmentation color of the left magnet.
        b_id = m.magnebot_static.magnets[Arm.left]
        color = m.magnebot_static.body_parts[b_id].segmentation_color
        print(b_id, color)
        ```
        """
        self.magnets: Dict[Arm, int] = dict()

        for i in range(static_robot.get_num_joints()):
            body_part_id = static_robot.get_joint_id(i)
            # Cache the body parts.
            self.body_parts[body_part_id] = BodyPartStatic(sr=static_robot, index=i)
            # Cache the wheels.
            body_part_name = static_robot.get_joint_name(i)
            if "wheel" in body_part_name:
                self.wheels[Wheel[body_part_name]] = body_part_id
            else:
                self.arm_joints[ArmJoint[body_part_name]] = body_part_id
        # Cache the magnets.
        for i in range(static_robot.get_num_non_moving()):
            body_part_name = static_robot.get_non_moving_name(i)
            if "magnet" in body_part_name:
                self.magnets[Arm.left if "left" in body_part_name else Arm.right] = static_robot.get_non_moving_id(i)
