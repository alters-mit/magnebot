from typing import Union, Dict, List
import numpy as np
from tdw.tdw_utils import TDWUtils
from tdw.output_data import Transforms
from magnebot.util import get_data
from magnebot.actions.action import Action
from magnebot.actions.turn import Turn
from magnebot.image_frequency import ImageFrequency
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.collision_detection import CollisionDetection


class TurnTo(Turn):
    """
    Turn to a target position or object.
    """

    def __init__(self, target: Union[int, Dict[str, float], np.array], static: MagnebotStatic, dynamic: MagnebotDynamic,
                 image_frequency: ImageFrequency, collision_detection: CollisionDetection, aligned_at: float = 1,
                 previous: Action = None):
        """
        :param target: The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array.
        :param aligned_at: If the difference between the current angle and the target angle is less than this value, then the action is successful.
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        :param image_frequency: [How image data will be captured during the image.](../image_frequency.md)
        :param collision_detection: [The collision detection rules.](../collision_detection.md)
        :param previous: The previous action, if any.
        """

        # This will be handled in get_initialization_commands().
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
        self._angle = self._get_angle()
        print(self._angle)
        return super().get_initialization_commands(resp=resp)

    def _get_angle(self) -> float:
        self._angle = TDWUtils.get_angle_between(v1=self.dynamic.transform.forward,
                                                 v2=self.target_arr - self.dynamic.transform.position)
        # Clamp the angle and set the delta angle and previous delta angle.
        self._clamp_angle()
        self._max_attempts: int = int((np.abs(self._angle) + 1) / 2)
        self._delta_angle: float = self._angle
        self._previous_delta_angle: float = self._angle
        return self._angle

    def _get_turn_command(self) -> dict:
        return {"$type": "set_magnebot_wheels_during_turn_to",
                "angle": self._angle,
                "origin": self._initial_forward_vector,
                "arrived_at": self._aligned_at,
                "position": self.target_dict,
                "minimum_friction": self._minimum_friction,
                "brake_angle": Turn._BRAKE_ANGLE,
                "id": self.static.robot_id}
