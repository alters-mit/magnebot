##### Magnebot

# Camera rotation

Camera actions require only one `communicate()` call to complete.

 `rotate_camera(roll, pitch, yaw)` will rotate the camera by (roll, pitch, yaw) in degrees. The Magnebot's camera rotation is clamped to a certain range.

To reset the camera's rotation, call `reset_camera()`.

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
# Use default orientation parameters (auto, auto).
magnebot.rotate_camera(roll=0, pitch=45, yaw=0)
c.communicate([])
assert magnebot.action.status == ActionStatus.success, magnebot.action.status
# Clamped pitch.
magnebot.rotate_camera(pitch=90)
c.communicate([])
assert magnebot.action.status == ActionStatus.clamped_camera_rotation, magnebot.action.status
# Reset the camera.
magnebot.reset_camera()
c.communicate([])
c.communicate({"$type": "terminate"})
```

***

**Next: [Third-person cameras](third_person_camera.md)**

[Return to the README](../../../README.md)

