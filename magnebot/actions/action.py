from abc import ABC, abstractmethod
from typing import List
from overrides import final
import numpy as np
from tdw.tdw_utils import QuaternionUtils
from magnebot.action_status import ActionStatus
from magnebot.arm import Arm
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic


class Action(ABC):
    """
    An action that the Magnebot can do, expressed as a state machine.

    Actions have three core functions:

    1. `evaluate()` will evaluate the current state of an ongoing action and return an `ActionStatus` and a list of commands.
    2. `end()` will return a list of commands to end the action.
    """

    def __init__(self, static: MagnebotStatic, dynamic: MagnebotDynamic, images: str = "once"):
        """
        :param static: [The static Magnebot data.](magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](magnebot_dynamic.md)
        :param images: How image data will be captured during the image. Options: "once" (at the end of the action), "always" (per frame), "never" (no image capture).
        """

        """:field
        [The static Magnebot data.](magnebot_static.md)
        """
        self.static: MagnebotStatic = static
        """:field
        [The dynamic Magnebot data.](magnebot_dynamic.md)
        """
        self.dynamic: MagnebotDynamic = dynamic
        # How image data will be captured during the image. Options: "once" (at the end of the action), "always" (per frame), "never" (no image capture).
        self._images: str = images
        self.status: ActionStatus = ActionStatus.ongoing
        self.initialized: bool = False

    def get_initialization_commands(self, resp: List[bytes]) -> List[dict]:
        if self._images == "once" or self._images == "never":
            commands = [{"$type": "enable_image_sensor",
                         "enable": False,
                         "avatar_id": self.static.avatar_id}]
        elif self._images == "always":
            commands = [{"$type": "enable_image_sensor",
                         "enable": True,
                         "avatar_id": self.static.avatar_id},
                        {"$type": "send_images",
                         "frequency": "always"},
                        {"$type": "send_camera_matrices",
                         "frequency": "always"}]
        else:
            raise Exception(f"Invalid image capture option: {self._images}")
        return commands

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
        if self._images == "once":
            commands.extend([{"$type": "enable_image_sensor",
                              "enable": True,
                              "avatar_id": self.static.avatar_id},
                             {"$type": "send_images",
                              "frequency": "once"},
                             {"$type": "send_camera_matrices",
                              "frequency": "once"}])
        return commands

    @final
    def _is_grasping(self, target: int, arm: Arm) -> bool:
        """
        :param target: The object ID.
        :param arm: The arm.

        :return: True if the arm is holding the object in this scene state.
        """

        return target in self.dynamic.held[arm]

    @final
    def _absolute_to_relative(self, position: np.array) -> np.array:
        """
        :param position: The position in absolute world coordinates.

        :return: The converted position relative to the Magnebot's position and rotation.
        """

        return QuaternionUtils.world_to_local_vector(position=position,
                                                     origin=self.dynamic.transform.position,
                                                     rotation=self.dynamic.transform.rotation)
