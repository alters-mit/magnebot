from typing import List, Dict, Union
import numpy as np
from tdw.tdw_utils import TDWUtils
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.image_frequency import ImageFrequency
from magnebot.actions.camera_action import CameraAction
from magnebot.action_status import ActionStatus


class LookAt(CameraAction):
    """
    Rotate the Magnebot's camera to look at a target object or position.

    This action is not compatible with [`RotateCamera`](rotate_camera.md) because it will ignore (roll, pitch, yaw) constraints; if you use this action, `RotateCamera` won't work as intended until you use [`ResetCamera`](reset_camera.md).
    """

    def __init__(self, target: Union[int, Dict[str, float], np.ndarray]):
        """
        :param target: The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array.
        """

        super().__init__()
        """:field
        The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array.
        """
        self.target: Union[int, Dict[str, float], np.ndarray] = target

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        # Look at the object.
        if isinstance(self.target, int):
            commands.append({"$type": "look_at",
                             "object_id": int(self.target),
                             "use_centroid": True,
                             "avatar_id": static.avatar_id})
        # Look at the position.
        elif isinstance(self.target, dict):
            commands.append({"$type": "look_at_position",
                             "position": {k: float(v) for k, v in self.target.items()},
                             "avatar_id": static.avatar_id})
        # Convert the position to a dictionary and look at it.
        elif isinstance(self.target, np.ndarray):
            commands.append({"$type": "look_at_position",
                             "position": TDWUtils.array_to_vector3(self.target),
                             "avatar_id": static.avatar_id})
        return commands

    def set_status_after_initialization(self) -> None:
        self.status = ActionStatus.success
