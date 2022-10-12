from typing import List
from magnebot.action_status import ActionStatus
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.actions.camera_action import CameraAction
from magnebot.image_frequency import ImageFrequency
from magnebot.constants import DEFAULT_CAMERA_POSITION_TORSO, DEFAULT_CAMERA_POSITION_COLUMN


class ResetCamera(CameraAction):
    """
    Reset the rotation of the Magnebot's camera to its default angles and/or its default position relative to its parent (by default, its parent is the torso).
    """

    def __init__(self, position: bool, rotation: bool, parented_to_torso: bool):
        """
        :param position: If True, reset the camera's position.
        :param rotation: If True, reset the camera' rotation.
        :param parented_to_torso: If True, the camera is parented to the torso.
        """

        super().__init__()
        self._position: bool = position
        self._rotation: bool = rotation
        self._parented_to_torso: bool = parented_to_torso

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        if self._position:
            commands.append({"$type": "teleport_avatar_to",
                             "position": DEFAULT_CAMERA_POSITION_TORSO if self._parented_to_torso else DEFAULT_CAMERA_POSITION_COLUMN,
                             "avatar_id": static.robot_id})
        if self._rotation:
            commands.append({"$type": "reset_sensor_container_rotation",
                             "avatar_id": static.avatar_id})
        return commands

    def set_status_after_initialization(self) -> None:
        # This action always succeeds.
        self.status = ActionStatus.success
