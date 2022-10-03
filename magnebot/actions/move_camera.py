from typing import List, Dict, Union
import numpy as np
from tdw.tdw_utils import TDWUtils
from magnebot.action_status import ActionStatus
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.image_frequency import ImageFrequency
from magnebot.camera_coordinate_space import CameraCoordinateSpace
from magnebot.actions.camera_action import CameraAction


class MoveCamera(CameraAction):
    """
    Move the Magnebot's camera.
    """

    def __init__(self, position: Union[Dict[str, float], np.ndarray], coordinate_space: CameraCoordinateSpace):
        """
        :param position: The position of the camera.
        :param coordinate_space: The [`CameraCoordinateSpace`](../camera_coordinate_space.md), which is used to define what `position` means.
        """

        super().__init__()
        if isinstance(position, dict):
            self._position: Dict[str, float] = {k: v for k, v in position.items()}
        elif isinstance(position, np.ndarray):
            self._position = TDWUtils.array_to_vector3(position)
        else:
            raise Exception(f"Invalid position: {position}")
        self._coordinate_space: CameraCoordinateSpace = coordinate_space

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        # Teleport to a new absolute position.
        if self._coordinate_space == CameraCoordinateSpace.absolute:
            commands.append({"$type": "teleport_avatar_to",
                             "position": self._position,
                             "avatar_id": static.avatar_id})
        # Teleport by an offset.
        elif self._coordinate_space == CameraCoordinateSpace.relative_to_camera:
            commands.append({"$type": "teleport_avatar_by",
                             "position": self._position,
                             "avatar_id": static.avatar_id})
        # Teleport to a position relative to the Magnebot.
        elif self._coordinate_space == CameraCoordinateSpace.relative_to_magnebot:
            commands.append({"$type": "teleport_avatar_to",
                             "position": TDWUtils.array_to_vector3(TDWUtils.vector3_to_array(self._position) - dynamic.transform.position),
                             "avatar_id": static.avatar_id})
        return commands

    def set_status_after_initialization(self) -> None:
        self.status = ActionStatus.success
