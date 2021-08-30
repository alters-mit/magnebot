from typing import List
import numpy as np
from magnebot.action_status import ActionStatus
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.actions.camera_action import CameraAction
from magnebot.actions.image_frequency import ImageFrequency


class ResetCamera(CameraAction):
    """
    Reset the Magnebot's camera to its initial rotation.
    """

    def __init__(self, camera_rpy: np.array,  static: MagnebotStatic, dynamic: MagnebotDynamic,
                 image_frequency: ImageFrequency):
        """
        :param camera_rpy: The current camera angles.
        :param static: [The static Magnebot data.](magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](magnebot_dynamic.md)
        :param image_frequency: [How image data will be captured during the image.](image_frequency.md)
        """

        super().__init__(static=static, dynamic=dynamic, image_frequency=image_frequency)
        # Reset the camera rotation.
        for i in range(len(camera_rpy)):
            camera_rpy[i] = 0

    def get_initialization_commands(self, resp: List[bytes]) -> List[dict]:
        return [{"$type": "reset_sensor_container_rotation",
                 "avatar_id": self.static.avatar_id}]

    def set_status_after_initialization(self) -> None:
        # This action always succeeds/
        self.status = ActionStatus.success
