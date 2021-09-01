from typing import Union, Dict, List
import numpy as np
from tdw.tdw_utils import TDWUtils
from tdw.output_data import Transforms
from magnebot.util import get_data
from magnebot.actions.action import Action
from magnebot.actions.turn import Turn
from magnebot.actions.image_frequency import ImageFrequency
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.collision_detection import CollisionDetection


class TurnTo(Turn):
    def __init__(self, target: Union[int, Dict[str, float], np.array], static: MagnebotStatic, dynamic: MagnebotDynamic,
                 image_frequency: ImageFrequency, collision_detection: CollisionDetection, aligned_at: float = 1,
                 previous: Action = None):
        self.__target: Union[int, Dict[str, float]] = target
        """:field
        The target position as a numpy array.
        """
        self.target_arr: np.array = np.array([0, 0, 0])
        """:field
        The target position as a dictionary.
        """
        self.target_dict: Dict[str, float] = {"x": 0, "y": 0, "z": 0}
        super().__init__(aligned_at=aligned_at, static=static, dynamic=dynamic, collision_detection=collision_detection,
                         previous=previous, image_frequency=image_frequency)

    def get_initialization_commands(self, resp: List[bytes]) -> List[dict]:
        # Set the target position.
        if isinstance(self.__target, int):
            # Get the position of the object.
            transforms = get_data(resp=resp, d_type=Transforms)
            object_position: np.array = np.array([0, 0, 0])
            for i in range(transforms.get_num()):
                if transforms.get_id(i) == self.__target:
                    object_position = np.array(transforms.get_position(i))
                    break

            self.target_arr: np.array = object_position
            self.target_dict: Dict[str, float] = TDWUtils.array_to_vector3(object_position)
        elif isinstance(self.__target, dict):
            self.target_arr: np.array = TDWUtils.vector3_to_array(self.__target)
            self.target_dict: Dict[str, float] = self.__target
        elif isinstance(self.__target, np.ndarray):
            self.target_arr: np.array = self.__target
            self.target_dict: Dict[str, float] = TDWUtils.array_to_vector3(self.__target)
        else:
            raise Exception(f"Invalid target: {self.__target}")
        return super().get_initialization_commands(resp=resp)

    def _get_angle(self) -> float:
        return TDWUtils.get_angle_between(v1=self.dynamic.transform.forward,
                                          v2=self.target_arr - self.dynamic.transform.position)

    def _get_turn_command(self) -> dict:
        return {"$type": "set_magnebot_wheels_during_turn_to",
                "angle": self._angle,
                "origin": self._initial_forward_vector,
                "arrived_at": self._aligned_at,
                "position": self.target_dict,
                "minimum_friction": self._minimum_friction,
                "brake_angle": Turn._BRAKE_ANGLE}
