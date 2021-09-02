from typing import Dict, List, Union, Optional
import numpy as np
from magnebot.actions.action import Action
from magnebot.actions.turn_to import TurnTo
from magnebot.actions.move_by import MoveBy
from magnebot.image_frequency import ImageFrequency
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.collision_detection import CollisionDetection
from magnebot.action_status import ActionStatus


class MoveTo(Action):
    """
    Turn the Magnebot to a target position or object and then move to it.

    This action has two "sub-actions": A [`TurnBy`](turn_by.md) and a [`MoveBy`](move_by.md).
    """

    def __init__(self, target: Union[int, Dict[str, float], np.array], static: MagnebotStatic, dynamic: MagnebotDynamic,
                 image_frequency: ImageFrequency, collision_detection: CollisionDetection, arrived_at: float = 0.1,
                 aligned_at: float = 1, previous: Action = None):
        """
        :param target: The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array.
        :param arrived_at: If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful.
        :param aligned_at: If the difference between the current angle and the target angle is less than this value, then the action is successful.
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        :param image_frequency: [How image data will be captured during the image.](../image_frequency.md)
        :param collision_detection: [The collision detection rules.](../collision_detection.md)
        :param previous: The previous action, if any.
        """

        super().__init__(static=static, dynamic=dynamic, image_frequency=image_frequency)
        self._turn_to: TurnTo = TurnTo(target=target, static=static, dynamic=dynamic, image_frequency=image_frequency,
                                       collision_detection=collision_detection, aligned_at=aligned_at,
                                       previous=previous)
        # Cache these in order to initialize the MoveBy action later.
        self.__collision_detection: CollisionDetection = collision_detection
        self.__image_frequency: ImageFrequency = image_frequency
        self.__arrived_at: float = arrived_at
        self._move_by: Optional[MoveBy] = None

    def get_initialization_commands(self, resp: List[bytes]) -> List[dict]:
        return self._turn_to.get_initialization_commands(resp=resp)

    def get_ongoing_commands(self, resp: List[bytes]) -> List[dict]:
        commands = []
        # We haven't started moving yet (we are turning).
        if self._move_by is None:
            # The turn immediately failed.
            if self._turn_to.status != ActionStatus.ongoing and self._turn_to.status != ActionStatus.success:
                self.status = self._turn_to.status
                return self._turn_to.get_end_commands(resp=resp)
            commands.extend(self._turn_to.get_ongoing_commands(resp=resp))
            # Continue turning.
            if self._turn_to.status == ActionStatus.ongoing:
                return commands
            # Stop turning.
            self.status = self._turn_to.status
            # The turn failed.
            if self._turn_to.status != ActionStatus.success:
                return self._turn_to.get_end_commands(resp=resp)
            # The turn succeeded. Start the move action.
            distance = np.linalg.norm(self._turn_to.target_arr - self.dynamic.transform.position)
            self._move_by = MoveBy(distance=distance, arrived_at=self.__arrived_at, static=self.static,
                                   dynamic=self.dynamic, collision_detection=self.__collision_detection,
                                   previous=self._turn_to, image_frequency=self.__image_frequency)
            self._move_by.initialized = True
            # Initialize the move_by action.
            commands.extend(self._move_by.get_initialization_commands(resp=resp))
            # The move immediately ended.
            if self._move_by.status != ActionStatus.ongoing:
                self.status = self._move_by.status
                return []
        # Continue moving.
        else:
            commands.extend(self._move_by.get_ongoing_commands(resp=resp))
            # The move ended.
            if self._move_by.status != ActionStatus.ongoing:
                self.status = self._move_by.status
                return self._move_by.get_end_commands(resp=resp)
            else:
                return commands