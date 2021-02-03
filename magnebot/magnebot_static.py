from typing import Dict, Tuple
from tdw.output_data import StaticRobot
from magnebot.joint_static import JointStatic
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
        [Static joint info](joint_static.md) for each joint, including the column, torso, wheels, and arm joints.
        Key = The body part object ID.
        
        ```python
        from magnebot import Magnebot

        m = Magnebot()
        m.init_scene(scene="2a", layout=1)

        # Print the object ID and segmentation color of each joint.
        for b_id in m.magnebot_static.joints:
            print(b_id, m.magnebot_static.joints[b_id].segmentation_color)
        ```
        """
        self.joints: Dict[int, JointStatic] = dict()

        """:field
        A dictionary of the object IDs of every part of the Magnebot. Includes everything in `self.joints` as well as non-moving parts.
        
        Key = the unique ID of the body part. Value = The segmentation color of the body part.
        
        Each body part has a different segmentation color:
        
        ![](images/magnebot_segmentation.png)
        
        
        ```python
        from magnebot import Magnebot

        m = Magnebot()
        m.init_scene(scene="2a", layout=1)

        # Print the object ID and segmentation color of each body part.
        for b_id in m.magnebot_static.body_parts:
            print(b_id, m.magnebot_static.body_parts[b_id])
        ```
        """
        self.body_parts: Dict[int, Tuple[float, float, float]] = dict()

        """:field
        The name and ID of each arm joint. Key = The [`ArmJoint` enum value](arm_joint.md). Value = The object ID.
        
        ```python
        from magnebot import Magnebot, ArmJoint

        m = Magnebot()
        m.init_scene(scene="2a", layout=1)
        
        # Print the object ID and segmentation color of the left shoulder.
        b_id = m.magnebot_static.arm_joints[ArmJoint.shoulder_left]
        color = m.magnebot_static.joints[b_id].segmentation_color
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
        color = m.magnebot_static.joints[b_id].segmentation_color
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
        color = m.magnebot_static.joints[b_id].segmentation_color
        print(b_id, color)
        ```
        """
        self.magnets: Dict[Arm, int] = dict()

        """:field
        The ID of the root object.
        """
        self.root: int = -1

        for i in range(static_robot.get_num_joints()):
            joint_id = static_robot.get_joint_id(i)
            # Cache the body parts.
            self.joints[joint_id] = JointStatic(sr=static_robot, index=i)
            self.body_parts[joint_id] = static_robot.get_joint_segmentation_color(i)
            # Cache the wheels.
            joint_name = static_robot.get_joint_name(i)
            if "wheel" in joint_name:
                self.wheels[Wheel[joint_name]] = joint_id
            elif "magnet" in joint_name:
                self.magnets[Arm.left if "left" in joint_name else Arm.right] = joint_id
            elif static_robot.get_is_joint_root(i):
                self.root = joint_id
            else:
                self.arm_joints[ArmJoint[joint_name]] = joint_id
        for i in range(static_robot.get_num_non_moving()):
            self.body_parts[static_robot.get_non_moving_id(i)] = static_robot.get_non_moving_segmentation_color(i)
