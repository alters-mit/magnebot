# MagnebotStatic

`from magnebot.magnebot_static import MagnebotStatic`

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

***

## Fields

- `robot_id` The ID of the robot.

- `joints` A dictionary of [Static robot joint data](joint_static.md) for each joint. Key = The ID of the joint.

- `joint_ids_by_name` A dictionary of joint names. Key = The name of the joint. Value = The joint ID.

- `non_moving` A dictionary of [Static data for non-moving parts](non_moving.md) for each non-moving part. Key = The ID of the part.

- `body_parts` A list of joint IDs and non-moving body part IDs.

- `immovable` If True, the robot is immovable.

- `arm_joints` The name and ID of each arm joint. Key = The [`ArmJoint` enum value](arm_joint.md). Value = The object ID.

- `wheels` The object IDs of each wheel. Key = The [`Wheel` enum value](wheel.md).

- `magnets` The object IDs of each magnet. Key = The [enum value of the `Arm`](arm.md) attached to the magnet.

- `avatar_id` The ID of the Magnebot's avatar (camera). This is used internally for API calls.

***

## Functions

#### \_\_init\_\_

**`MagnebotStatic()`**

The name and ID of each arm joint. Key = The [`ArmJoint` enum value](arm_joint.md). Value = The object ID.

