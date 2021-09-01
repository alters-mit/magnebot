from abc import ABC, abstractmethod
from typing import List
from overrides import final
import numpy as np
from tdw.tdw_utils import QuaternionUtils
from magnebot.action_status import ActionStatus
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.image_frequency import ImageFrequency


class Action(ABC):
    """
    An action that the Magnebot can do, expressed as a state machine.

    Actions have three core functions:

    1. `evaluate()` will evaluate the current state of an ongoing action and return an `ActionStatus` and a list of commands.
    2. `end()` will return a list of commands to end the action.
    """

    def __init__(self, static: MagnebotStatic, dynamic: MagnebotDynamic, image_frequency: ImageFrequency):
        """
        :param static: [The static Magnebot data.](magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](magnebot_dynamic.md)
        :param image_frequency: [How image data will be captured during the image.](image_frequency.md)
        """

        """:field
        [The static Magnebot data.](magnebot_static.md)
        """
        self.static: MagnebotStatic = static
        """:field
        [The dynamic Magnebot data.](magnebot_dynamic.md)
        """
        self.dynamic: MagnebotDynamic = dynamic
        """:field
        [How image data will be captured during the image.](image_frequency.md)
        """
        self.image_frequency: ImageFrequency = image_frequency
        self.status: ActionStatus = ActionStatus.ongoing
        self.initialized: bool = False

    def get_initialization_commands(self, resp: List[bytes]) -> List[dict]:
        if self.image_frequency == ImageFrequency.once or self.image_frequency == ImageFrequency.never:
            commands = [{"$type": "enable_image_sensor",
                         "enable": False,
                         "avatar_id": self.static.avatar_id}]
        elif self.image_frequency == ImageFrequency.always:
            commands = [{"$type": "enable_image_sensor",
                         "enable": True,
                         "avatar_id": self.static.avatar_id},
                        {"$type": "send_images",
                         "frequency": "always"},
                        {"$type": "send_camera_matrices",
                         "frequency": "always"}]
        else:
            raise Exception(f"Invalid image capture option: {self.image_frequency}")
        return commands

    def set_status_after_initialization(self) -> None:
        """
        In some cases (such as camera actions) that finish on one frame, we want to set the status after sending initialization commands.
        To do so, override this method.
        """

        pass

    @abstractmethod
    def get_ongoing_commands(self, resp: List[bytes]) -> List[dict]:
        """
        Evaluate an action per-frame to determine whether it's done.

        :param resp: The response from the build.

        :return: Tuple: An `ActionStatus` describing whether the action is ongoing, succeeded, or failed; A list of commands to send to the build if the action is ongoing.
        """

        raise Exception()

    def get_end_commands(self, resp: List[bytes]) -> List[dict]:
        """
        :param resp: The response from the build.

        :return: A list of commands that must be sent to end any action.
        """

        commands: List[dict] = list()
        if self.image_frequency == ImageFrequency.once:
            commands.extend([{"$type": "enable_image_sensor",
                              "enable": True,
                              "avatar_id": self.static.avatar_id},
                             {"$type": "send_images",
                              "frequency": "once"},
                             {"$type": "send_camera_matrices",
                              "frequency": "once"}])
        return commands

    @final
    def _absolute_to_relative(self, position: np.array) -> np.array:
        """
        :param position: The position in absolute world coordinates.

        :return: The converted position relative to the Magnebot's position and rotation.
        """

        return QuaternionUtils.world_to_local_vector(position=position,
                                                     origin=self.dynamic.transform.position,
                                                     rotation=self.dynamic.transform.rotation)
