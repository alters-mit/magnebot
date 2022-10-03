from typing import List
from magnebot.action_status import ActionStatus
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.actions.camera_action import CameraAction
from magnebot.image_frequency import ImageFrequency
from magnebot.constants import DEFAULT_CAMERA_POSITION_TORSO, DEFAULT_CAMERA_POSITION_COLUMN


class ResetCameraPosition(CameraAction):
    """
    Reset the Magnebot's camera to its initial position.
    """

    def __init__(self, parented_to_torso: bool):
        """
        :param parented_to_torso: If True, the camera is parented to the torso.
        """

        super().__init__()
        self._parented_to_torso: bool = parented_to_torso

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        commands.append({"$type": "teleport_avatar_to",
                         "position": DEFAULT_CAMERA_POSITION_TORSO if self._parented_to_torso else DEFAULT_CAMERA_POSITION_COLUMN,
                         "avatar_id": static.robot_id})
        return commands

    def set_status_after_initialization(self) -> None:
        # This action always succeeds.
        self.status = ActionStatus.success
