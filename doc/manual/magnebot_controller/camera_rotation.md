##### MagnebotController

# Camera rotation

Camera actions require only one `communicate()` call to complete.

 `rotate_camera(roll, pitch, yaw)` will rotate the camera by (roll, pitch, yaw) in degrees. The Magnebot's camera rotation is clamped to a certain range.

To reset the camera's rotation, call `reset_camera()`.

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
c.reset_camera()
c.end()
```

***

**Next: [Third-person cameras](third_person_camera.md)**

[Return to the README](../../../README.md)

