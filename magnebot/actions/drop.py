from typing import List
import numpy as np
from tdw.output_data import Transforms
from magnebot.action_status import ActionStatus
from magnebot.util import get_data
from magnebot.arm import Arm
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.image_frequency import ImageFrequency
from magnebot.actions.arm_motion import ArmMotion


class Drop(ArmMotion):
    def __init__(self, target: int, arm: Arm, wait_for_object: bool, static: MagnebotStatic, dynamic: MagnebotDynamic,
                 image_frequency: ImageFrequency):
        super().__init__(static=static, dynamic=dynamic, image_frequency=image_frequency, arm=arm)
        self._target: int = int(target)
        self._wait_for_object: bool = wait_for_object
        self._object_position: np.array = np.array([0, 0, 0])
        # Wait a few frames before checking on the object.
        self._initial_frames: int = 0
        if self._target not in self.dynamic.held[self._arm]:
            self.status = ActionStatus.not_holding

    def get_initialization_commands(self, resp: List[bytes]) -> List[dict]:
        self._object_is_moving(resp=resp)
        commands = super().get_initialization_commands(resp=resp)
        commands.append({"$type": "detach_from_magnet",
                         "arm": self._arm.name,
                         "object_id": self._target,
                         "id": self.static.robot_id})
        return commands

    def set_status_after_initialization(self) -> None:
        # If we don't want to wait for the object to stop moving, the action ends here.
        if not self._wait_for_object:
            self.status = ActionStatus.success

    def get_ongoing_commands(self, resp: List[bytes]) -> List[dict]:
        # Wait a few frames before checking.
        if self._initial_frames < 5:
            self._initial_frames += 1
        # Check if the object is still moving.
        elif not self._object_is_moving(resp=resp):
            self.status = ActionStatus.success
        return []

    def _object_is_moving(self, resp: List[bytes]) -> bool:
        """
        Update the object's position and check if it's still moving.

        :param resp: The response from the build.

        :return: True if the object is moving.
        """

        # Get the initial position of the object.
        transforms = get_data(resp=resp, d_type=Transforms)
        for i in range(transforms.get_num()):
            if transforms.get_id(i) == self._target:
                object_position = np.array(transforms.get_position(i))
                d = np.linalg.norm(self._object_position - object_position)
                self._object_position = np.array([object_position[0] ,object_position[1], object_position[2]])
                # Stop if the object somehow fell below the floor or if the object isn't moving.
                if object_position[1] < -1 or d < 0.01:
                    return False
                break
        return True
