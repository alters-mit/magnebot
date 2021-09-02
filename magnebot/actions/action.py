from abc import ABC, abstractmethod
from typing import List, Tuple
from overrides import final
import numpy as np
from tdw.tdw_utils import QuaternionUtils
from magnebot.action_status import ActionStatus
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.image_frequency import ImageFrequency
from magnebot.constants import TORSO_MAX_Y, TORSO_MIN_Y


class Action(ABC):
    """
    An action that the Magnebot can do. An action is initialized, has an ongoing state, and an end state.
    An action also has a status indicating whether it's ongoing, succeeded, or failed; and if it failed, why.
    """

    def __init__(self, static: MagnebotStatic, dynamic: MagnebotDynamic, image_frequency: ImageFrequency):
        """
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        :param image_frequency: [How image data will be captured during the image.](../image_frequency.md)
        """

        """:field
        [The static Magnebot data.](../magnebot_static.md)
        """
        self.static: MagnebotStatic = static
        """:field
        [The dynamic Magnebot data.](../magnebot_dynamic.md)
        """
        self.dynamic: MagnebotDynamic = dynamic
        """:field
        [How image data will be captured during the image.](../image_frequency.md)
        """
        self.image_frequency: ImageFrequency = image_frequency
        """:field
        [The current status of the action.](../action_status.md) By default, this is `ongoing` (the action isn't done).
        """
        self.status: ActionStatus = ActionStatus.ongoing
        """:field
        If True, the action has initialized. If False, the action will try to send `get_initialization_commands(resp)` on this frame.
        """
        self.initialized: bool = False

    def get_initialization_commands(self, resp: List[bytes]) -> List[dict]:
        """
        :param resp: The response from the build.

        :return: A list of commands to initialize this action.
        """

        # If we only want images at the start of the action or never, disable the camera now.
        if self.image_frequency == ImageFrequency.once or self.image_frequency == ImageFrequency.never:
            commands = [{"$type": "enable_image_sensor",
                         "enable": False,
                         "avatar_id": self.static.avatar_id}]
        # If we want images per frame, enable image capture now.
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
        # Enable image capture on this frame only.
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

    @final
    def _is_tipping(self) -> Tuple[bool, bool]:
        """
        :return: Tuple: True if the Magnebot has tipped over; True if the Magnebot is tipping.
        """

        bottom_top_distance = np.linalg.norm(np.array([self.dynamic.transform.position[0],
                                                       self.dynamic.transform.position[2]]) -
                                             np.array([self.dynamic.top[0], self.dynamic.top[2]]))
        return bottom_top_distance > 1.7, bottom_top_distance > 0.4

    @staticmethod
    def _y_position_to_torso_position(y_position: float) -> float:
        """
        :param y_position: A y positional value in meters.

        :return: A corresponding joint position value for the torso prismatic joint.
        """

        # Convert the torso value to a percentage and then to a joint position.
        p = (y_position * (TORSO_MAX_Y - TORSO_MIN_Y)) + TORSO_MIN_Y
        return float(p * 1.5)
