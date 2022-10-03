##### MagnebotController

# Camera actions

Camera actions require only one `communicate()` call to complete.

## Rotation

`rotate_camera(roll, pitch, yaw)` will rotate the camera by (roll, pitch, yaw) in degrees. The Magnebot's camera rotation is clamped to a certain range.

To reset the camera's rotation, call `reset_camera_rotation()`.

```python
from magnebot import MagnebotController, ActionStatus
from magnebot.actions.rotate_camera import RotateCamera

print(RotateCamera.CAMERA_RPY_CONSTRAINTS)
c = MagnebotController()
c.init_scene()
# Rotate the camera.
status = c.rotate_camera(roll=0, pitch=45, yaw=0)
assert status == ActionStatus.success, status
# Clamped pitch.
status = c.rotate_camera(pitch=90)
assert status == ActionStatus.clamped_camera_rotation, status
# Reset the camera.
c.reset_camera_rotation()
c.end()
```

## Movement

`move_camera(position)` will move the camera to/by a position; by default, it will move the camera by a positional offset:

```python
from magnebot import MagnebotController

c = MagnebotController()
c.init_scene()
c.move_camera({"x": 0, "y": 0.6, "z": 0})
c.communicate({"$type": "terminate"})
```

You can move set the coordinate space of camera movement by setting the `coordinate_space` parameter, which accepts a [`CameraCoordinateSpace` enum value](../../api/camera_coordinate_space.md):

```python
from magnebot import MagnebotController
from magnebot.camera_coordinate_space import CameraCoordinateSpace

c = MagnebotController()
c.init_scene()
c.move_camera({"x": 0, "y": 0.6, "z": 0}, coordinate_space=CameraCoordinateSpace.absolute)
c.communicate({"$type": "terminate"})
```

You can reset the camera to its default position with by calling `reset_camera_position()`:

```python
from magnebot import MagnebotController

c = MagnebotController()
c.init_scene()
c.move_camera({"x": 0, "y": 0.6, "z": 0})
c.reset_camera_position()
c.communicate({"$type": "terminate"})
```

***

**Next: [Third-person cameras](third_person_camera.md)**

[Return to the README](../../../README.md)
