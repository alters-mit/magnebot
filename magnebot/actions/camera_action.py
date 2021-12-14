from typing import List
from abc import ABC
from overrides import final
from magnebot.actions.action import Action
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic


class CameraAction(Action, ABC):
    """
    Abstract class for actions that rotate the camera.
    """

    def __init__(self):
        """
        (no parameters)
        """

        super().__init__()

    @final
    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        return []
