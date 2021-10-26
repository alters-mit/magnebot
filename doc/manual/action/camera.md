##### Action

# Camera actions

Camera actions are relatively easy to define because they only require one frame to complete.

All camera actions should be subclasses of the abstract class [`CameraAction`](../../api/actions/camera_action.md). This class overrides `get_ongoing_commands` to return `[]` (because this function isn't used at all). In the default API, [`RotateCamera`](../../api/actions/rotate_camera.md) and [`ResetCamera`](../../api/actions/reset_camera.md) are subclasses of `CameraAction`.

Because camera actions require only one frame, you'll want to override `get_initialization_commands` to send the commands and `set_status_after_initialization` to immediately set [`self.status`](../../api/action_status.md) to something other than `ActionStatus.ongoing`, thereby ending the action.

This is an example subclass of `CameraAction` that sets the camera rotation to a target quaternion:

```python
from typing import List, Dict
from magnebot.action_status import ActionStatus
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.image_frequency import ImageFrequency
from magnebot.actions.camera_action import CameraAction

class SetCameraQuaternion(CameraAction):
    def __init__(self, quaternion: Dict[str, float]):
        super().__init__()
        self.quaternion: Dict[str, float] = quaternion

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        commands.append({"$type": "rotate_sensor_container_to",
                         "rotation": self.quaternion, 
                         "avatar_id": static.avatar_id})
        return commands

    def set_status_after_initialization(self) -> None:
        self.status = ActionStatus.success
```

***

[Return to the README](../../../README.md)

