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

- `body_parts` [Static body part info](body_part_static.md) for each body part. Key = the body part object ID.

```python
from magnebot import Magnebot

m = Magnebot()
m.init_scene(scene="2a", layout=1)

# Print the object ID and segmentation color of each body part.
for b_id in m.magnebot_static.body_parts:
    print(b_id, m.magnebot_static.body_parts[b_id].segmentation_color)
```

- `arm_joints` The object of each arm joint. Key = The [arm](arm.md). Value = A dictionary of [`ArmJoint` enum values](arm_joint.md) and their object IDs.

```python
from magnebot import Magnebot, Arm, ArmJoint

m = Magnebot()
m.init_scene(scene="2a", layout=1)

# Print the object ID of the left shoulder.
print(m.magnebot_static.arm_joints[Arm.left][ArmJoint.shoulder])
```

- `wheels` The object IDs of each wheel. Key = the name of the wheel as an [`Wheel` enum value](wheel.md).

- `magnets` The object IDs of each magnet. Key = the [`Arm`](arm.md) attached to the magnet.

***

## Functions

#### \_\_init\_\_

**`def __init__(self, static_robot: StaticRobot)`**

| Parameter | Description |
| --- | --- |
| static_robot | Static robot output data. |

