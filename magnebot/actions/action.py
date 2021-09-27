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

    def __init__(self):
        """
        (no parameters)
        """

        """:field
        [The current status of the action.](../action_status.md) By default, this is `ongoing` (the action isn't done).
        """
        self.status: ActionStatus = ActionStatus.ongoing
        """:field
        If True, the action has initialized. If False, the action will try to send `get_initialization_commands(resp)` on this frame.
        """
        self.initialized: bool = False
        """:field
        If True, this action is done and won't send any more commands.
        """
        self.done: bool = False

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        """
        :param resp: The response from the build.
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        :param image_frequency: [How image data will be captured during the image.](../image_frequency.md)

        :return: A list of commands to initialize this action.
        """

        # If we only want images at the start of the action or never, disable the camera now.
        if image_frequency == ImageFrequency.once or image_frequency == ImageFrequency.never:
            commands = [{"$type": "enable_image_sensor",
                         "enable": False,
                         "avatar_id": static.avatar_id}]
        # If we want images per frame, enable image capture now.
        elif image_frequency == ImageFrequency.always:
            commands = [{"$type": "enable_image_sensor",
                         "enable": True,
                         "avatar_id": static.avatar_id},
                        {"$type": "send_images",
                         "frequency": "always"},
                        {"$type": "send_camera_matrices",
                         "frequency": "always"}]
        else:
            raise Exception(f"Invalid image capture option: {image_frequency}")
        return commands

    def set_status_after_initialization(self) -> None:
        """
        In some cases (such as camera actions) that finish on one frame, we want to set the status after sending initialization commands.
        To do so, override this method.
        """

        pass

    @abstractmethod
    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        """
        Evaluate an action per-frame to determine whether it's done.

        :param resp: The response from the build.
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)

        :return: Tuple: A list of commands to send to the build to continue the action.
        """

        raise Exception()

    def get_end_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                         image_frequency: ImageFrequency,) -> List[dict]:
        """
        :param resp: The response from the build.
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        :param image_frequency: [How image data will be captured during the image.](../image_frequency.md)

        :return: A list of commands that must be sent to end any action.
        """

        commands: List[dict] = list()
        # Enable image capture on this frame only.
        if image_frequency == ImageFrequency.once:
            commands.extend([{"$type": "enable_image_sensor",
                              "enable": True,
                              "avatar_id": static.avatar_id},
                             {"$type": "send_images",
                              "frequency": "once"},
                             {"$type": "send_camera_matrices",
                              "frequency": "once"}])
        return commands

    @final
    def _absolute_to_relative(self, position: np.array, dynamic: MagnebotDynamic) -> np.array:
        """
        :param position: The position in absolute world coordinates.
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)

        :return: The converted position relative to the Magnebot's position and rotation.
        """

        return QuaternionUtils.world_to_local_vector(position=position,
                                                     origin=dynamic.transform.position,
                                                     rotation=dynamic.transform.rotation)

    @final
    def _is_tipping(self, dynamic: MagnebotDynamic) -> Tuple[bool, bool]:
        """
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)

        :return: Tuple: True if the Magnebot has tipped over; True if the Magnebot is tipping.
        """

        bottom_top_distance = np.linalg.norm(np.array([dynamic.transform.position[0],
                                                       dynamic.transform.position[2]]) -
                                             np.array([dynamic.top[0], dynamic.top[2]]))
        return bottom_top_distance > 1.7, bottom_top_distance > 0.4

    @final
    def _get_stop_wheels_commands(self, static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        """
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)

        :return: A list of commands to make the wheels stop spinning.
        """

        commands = []
        for wheel in static.wheels:
            # Set the target of each wheel to its current position.
            commands.append({"$type": "set_revolute_target",
                             "id": static.robot_id,
                             "target": float(dynamic.joints[static.wheels[wheel]].angles[0]),
                             "joint_id": static.wheels[wheel]})
        return commands

