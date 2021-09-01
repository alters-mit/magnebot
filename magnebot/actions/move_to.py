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
    def __init__(self, target: Union[int, Dict[str, float], np.array], static: MagnebotStatic, dynamic: MagnebotDynamic,
                 image_frequency: ImageFrequency, collision_detection: CollisionDetection, arrived_at: float = 0.1,
                 aligned_at: float = 1, previous: Action = None):
        super().__init__(static=static, dynamic=dynamic, image_frequency=image_frequency)
        self._turn_to: TurnTo = TurnTo(target=target, static=static, dynamic=dynamic, image_frequency=image_frequency,
                                       collision_detection=collision_detection, aligned_at=aligned_at,
                                       previous=previous)
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
