from typing import Union, Dict, List
import numpy as np
from tdw.tdw_utils import TDWUtils
from tdw.output_data import Transforms
from magnebot.util import get_data
from magnebot.actions.action import Action
from magnebot.actions.turn import Turn
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.collision_detection import CollisionDetection


class TurnTo(Turn):
    """
    Turn to a target position or object.
    """

    def __init__(self, target: Union[int, Dict[str, float], np.array], resp: List[bytes], dynamic: MagnebotDynamic,
                 collision_detection: CollisionDetection, aligned_at: float = 1, previous: Action = None):
        """
        :param target: The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array.
        :param resp: The response from the build.
        :param aligned_at: If the difference between the current angle and the target angle is less than this value, then the action is successful.
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        :param collision_detection: [The collision detection rules.](../collision_detection.md)
        :param previous: The previous action, if any.
        """

        # Set the target position.
        if isinstance(target, int):
            # Get the position of the object.
            transforms = get_data(resp=resp, d_type=Transforms)
            object_position: np.array = np.array([0, 0, 0])
            for i in range(transforms.get_num()):
                if transforms.get_id(i) == target:
                    object_position = np.array(transforms.get_position(i))
                    break
            """:field
            The target position as a numpy array.
            """
            self.target_arr: np.array = object_position
            """:field
            The target position as a dictionary.
            """
            self.target_dict: Dict[str, float] = TDWUtils.array_to_vector3(object_position)
        elif isinstance(target, dict):
            self.target_arr: np.array = TDWUtils.vector3_to_array(target)
            self.target_dict: Dict[str, float] = target
        elif isinstance(target, np.ndarray):
            self.target_arr: np.array = target
            self.target_dict: Dict[str, float] = TDWUtils.array_to_vector3(target)
        else:
            raise Exception(f"Invalid target: {target}")
        super().__init__(aligned_at=aligned_at, dynamic=dynamic, collision_detection=collision_detection,
                         previous=previous)

    def _get_angle(self, dynamic: MagnebotDynamic) -> float:
        return TDWUtils.get_angle_between(v1=dynamic.transform.forward,
                                          v2=self.target_arr - dynamic.transform.position)

    def _get_turn_command(self, static: MagnebotStatic) -> dict:
        return {"$type": "set_magnebot_wheels_during_turn_to",
                "angle": self._angle,
                "origin": self._initial_forward_vector,
                "arrived_at": self._aligned_at,
                "position": self.target_dict,
                "minimum_friction": self._minimum_friction,
                "brake_angle": Turn._BRAKE_ANGLE,
                "id": static.robot_id}
