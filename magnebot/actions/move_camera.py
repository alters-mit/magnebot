from typing import List, Dict, Union
import numpy as np
from tdw.tdw_utils import TDWUtils
from magnebot.action_status import ActionStatus
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.image_frequency import ImageFrequency
from magnebot.actions.camera_action import CameraAction


class MoveCamera(CameraAction):
    """
    Move the Magnebot's camera by an offset position.
    """

    def __init__(self, position: Union[Dict[str, float], np.ndarray]):
        """
        :param position: The positional offset that the camera will move by.
        """

        super().__init__()
        if isinstance(position, dict):
            """:field
            The positional offset that the camera will move by. 
            """
            self.position: Dict[str, float] = {k: v for k, v in position.items()}
        elif isinstance(position, np.ndarray):
            self.position = TDWUtils.array_to_vector3(position)
        else:
            raise Exception(f"Invalid position: {position}")

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        commands.append({"$type": "teleport_avatar_by",
                         "position": self.position,
                         "avatar_id": static.avatar_id})
        return commands

    def set_status_after_initialization(self) -> None:
        self.status = ActionStatus.success
