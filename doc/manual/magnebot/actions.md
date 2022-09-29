##### Magnebot

# Actions

An **action** in the [`Magnebot`](../../api/magnebot.md) is a function that causes the Magnebot to *start* to do something. Unlike the `MagnebotController`, `Magnebot` actions won't automatically finish and can be interrupted.

By default, the `Magnebot` action space is: 

- `turn_by(angle)`
- `turn_to(target)`
- `move_by(distance)`
- `move_to(target)`
- `reach_for(target, arm)`
- `grasp(target, arm)`
- `drop(target, arm)`
- `reset_arm(arm)`
- `reset_position()`
- `rotate_camera(roll, pitch, yaw)`
- `reset_camera()`
- `slide_torso(height)`
- `stop()`

*Note:  Most of these actions have additional optional parameters. Read the API document for more information.*

### Evaluating actions

Calling an action function begins an action. After this, the Magnebot will update `self.dynamic` and evaluate the action's [status](../../api/action_status.md) per `c.communicate(commands)` call.

This controller will move a Magnebot forward by 8 meters. The action will end in `ActionStatus.collision` when the Magnebot collides with a wall:

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus

c = Controller()
magnebot = Magnebot()
c.add_ons.append(magnebot)
c.communicate([{"$type": "load_scene",
                "scene_name": "ProcGenScene"},
               TDWUtils.create_empty_room(12, 12)])
magnebot.move_by(distance=8)
while magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])
# End the action.
c.communicate([])
print(magnebot.action.status)
c.communicate({"$type": "terminate"})
```

Output:

```
ActionStatus.collision
```

Unlike the `MagnebotController`, actions can be interrupted when using the `Magnebot` agent. In this example, the Magnebot will stop before colliding with the wall:

```python
import numpy as np
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus

c = Controller()
magnebot = Magnebot()
c.add_ons.append(magnebot)
c.communicate([{"$type": "load_scene",
                "scene_name": "ProcGenScene"},
               TDWUtils.create_empty_room(12, 12)])
initial_position = np.array(magnebot.dynamic.transform.position[:])
magnebot.move_by(distance=8)
while magnebot.action.status == ActionStatus.ongoing:
    distance = np.linalg.norm(initial_position - magnebot.dynamic.transform.position)
    # Stop before the Magnebot collides with a wall.
    if distance > 4.75:
        magnebot.stop()
    c.communicate([])
# End the action.
c.communicate([])
print(magnebot.action.status)
c.communicate({"$type": "terminate"})
```

Output:

```
ActionStatus.success
```

## Images

By default, the Magnebot captures image data *only at the end of an action*. This is for performance reasons; image capture is one of the slowest processes in TDW.

To enable image capture per `c.communicate(commands)` call, set the [`image_frequency`](../../api/image_frequency.md) parameter in the `Magnebot` constructor:

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ImageFrequency

c = Controller()
magnebot = Magnebot(position={"x": 0, "y": 0, "z": -1},
                    rotation={"x": 0, "y": 32, "z": 0},
                    image_frequency=ImageFrequency.always)
c.add_ons.append(magnebot)
c.communicate([{"$type": "load_scene",
                "scene_name": "ProcGenScene"},
               TDWUtils.create_empty_room(12, 12)])
# Advance one more frame after initialization to capture an image.
c.communicate([])
for pass_mask in magnebot.dynamic.images:
    print(pass_mask)
c.communicate({"$type": "terminate"})
```

Output:

```
img
id
depth
```

## Skipped frames

For performance reasons, `MagnebotController` advances 11 physics frames per output frame and renders frames only at the end of every action.

You can implement this behavior for a `Magnebot` agent as well by adding a `StepPhysics` add-on:

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.step_physics import StepPhysics
from magnebot import Magnebot, ImageFrequency

c = Controller()
magnebot = Magnebot(position={"x": 0, "y": 0, "z": -1},
                    rotation={"x": 0, "y": 32, "z": 0},
                    image_frequency=ImageFrequency.always)
step_physics = StepPhysics(num_frames=10)
c.add_ons.extend([magnebot, step_physics])
c.communicate([{"$type": "load_scene",
                "scene_name": "ProcGenScene"},
               TDWUtils.create_empty_room(12, 12)])
```

The `Magnebot` won't update its status, evaluate its action, capture images, etc. until all skipped frames have elapsed. It *will* detect collisions.

***

**Next: [Moving, turning, and collision detection](movement.md)**

[Return to the README](../../../README.md)

***

Examples controllers:

- [stop.py](https://github.com/alters-mit/magnebot/blob/main/controllers/examples/magnebot/stop.py) Move forward by 8 meters. Stop before colliding with a wall.
