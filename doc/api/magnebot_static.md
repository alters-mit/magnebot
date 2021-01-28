# MagnebotStatic

`from magnebot.magnebot_static import MagnebotStatic`

Static data for the Magnebot. See: `Magnebot.magnebot_static`

```python
from magnebot import Magnebot

m = Magnebot()
m.init_scene(scene="2a", layout=1)
print(m.magnebot_static.magnets)
```

***

## Fields

- `joints` [Static joint info](joint_static.md) for each joint, including the column, torso, wheels, and arm joints.
Key = The body part object ID.

```python
from magnebot import Magnebot

m = Magnebot()
m.init_scene(scene="2a", layout=1)

# Print the object ID and segmentation color of each joint.
for b_id in m.magnebot_static.joints:
    print(b_id, m.magnebot_static.joints[b_id].segmentation_color)
```

- `body_parts` A list of the object IDs of every part of the Magnebot. Includes everything in `self.joints` as well as non-moving parts.


```python
from magnebot import Magnebot

m = Magnebot()
m.init_scene(scene="2a", layout=1)

# Print the object ID of each body part.
for b_id in m.magnebot_static.body_parts:
    print(b_id)
```

- `arm_joints` The name and ID of each arm joint. Key = The [`ArmJoint` enum value](arm_joint.md). Value = The object ID.

```python
from magnebot import Magnebot, ArmJoint

m = Magnebot()
m.init_scene(scene="2a", layout=1)

# Print the object ID and segmentation color of the left shoulder.
b_id = m.magnebot_static.arm_joints[ArmJoint.shoulder_left]
color = m.magnebot_static.joints[b_id].segmentation_color
print(b_id, color)
```

- `wheels` The object IDs of each wheel. Key = The [`Wheel` enum value](wheel.md).

```python
from magnebot import Magnebot, Wheel

m = Magnebot()
m.init_scene(scene="2a", layout=1)

# Print the object ID and segmentation color of the left back wheel.
b_id = m.magnebot_static.wheels[Wheel.wheel_left_back]
color = m.magnebot_static.joints[b_id].segmentation_color
print(b_id, color)
```

- `magnets` The object IDs of each magnet. Key = The [enum value of the `Arm`](arm.md) attached to the magnet.

```python
from magnebot import Magnebot, Arm

m = Magnebot()
m.init_scene(scene="2a", layout=1)

# Print the object ID and the segmentation color of the left magnet.
b_id = m.magnebot_static.magnets[Arm.left]
color = m.magnebot_static.joints[b_id].segmentation_color
print(b_id, color)
```

- `root` The ID of the root object.

***

## Functions

#### \_\_init\_\_

**`MagnebotStatic(static_robot)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| static_robot |  StaticRobot |  | Static robot output data. |

