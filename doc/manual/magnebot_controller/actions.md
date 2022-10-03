##### MagnebotController

# Actions

An **action** in the [`MagnebotController`](../../api/magnebot_controller.md) is a function that causes the Magnebot to do something. All actions advance the simulation by at least one frame. All actions involving motion such as movement or arm articulation advance the simulation by multiple frames.

The `MagnebotController` action space is:

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
- `reset_camera_rotation()`
- `move_camera(position)`
- `reset_camera_position()`
- `slide_torso(height)`

*Note:  Most of these actions have additional optional parameters. Read the API document for more information.*

This controller will create a scene, add a Magnebot, and move the Magnebot forward by 2 meters:

```python
from magnebot import MagnebotController

c = MagnebotController()
c.init_scene()
c.move_by(2)
c.end()
```

## Dynamic output data

When an action ends, it updates `c.magnebot.dynamic`, including image data.

Every action also returns an [`ActionStatus`](../../api/action_status.md), an enum value that describes whether the action succeeded or failed and, if the action failed, why.

In this example, the action succeeds because the Magnebot moves forward by 2 meters:

```python
from magnebot import MagnebotController

c = MagnebotController()
c.init_scene()
status = c.move_by(2)
print(status)  # ActionStatus.success
c.end()
```

In this example, the action fails because the Magnebot collides with a wall and therefore can't move forward by 8 meters:

```python
from magnebot import MagnebotController

c = MagnebotController()
c.init_scene()
status = c.move_by(8)
print(status)  # ActionStatus.collision
c.end()
```

## Skipped frames

For performance reasons, `MagnebotController` advances 11 physics frames per output frame and renders frames only at the end of every action.

You can control the number of skipped physics frames by setting the `skip_frames` parameter in the constructor. If `skip_frames=0` the simulation will advance 1 physics frame per output frame. As a result, the simulation will be much slower.

***

**Next: [Moving, turning, and collision detection](movement.md)**

[Return to the README](../../../README.md)

