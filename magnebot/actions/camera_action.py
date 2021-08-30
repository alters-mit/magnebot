from typing import List
from abc import ABC
from overrides import final
from magnebot.actions.action import Action


class CameraAction(Action, ABC):
    """
    Abstract class for actions that rotate the camera.
    """

    """:class_var
    The camera roll, pitch, yaw constraints in degrees.
    """
    CAMERA_RPY_CONSTRAINTS: List[float] = [55, 70, 85]

    @final
    def get_ongoing_commands(self, resp: List[bytes]) -> List[dict]:
        return []
