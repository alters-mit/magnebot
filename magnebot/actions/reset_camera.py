from typing import List
import numpy as np
from magnebot.action_status import ActionStatus
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.actions.camera_action import CameraAction
from magnebot.image_frequency import ImageFrequency


class ResetCamera(CameraAction):
    """
    Reset the Magnebot's camera to its initial rotation.
    """

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        commands.append({"$type": "reset_sensor_container_rotation",
                         "avatar_id": static.avatar_id})
        return commands

    def set_status_after_initialization(self) -> None:
        # This action always succeeds.
        self.status = ActionStatus.success
