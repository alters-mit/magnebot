from typing import List, Dict
import numpy as np
from tdw.tdw_utils import TDWUtils
from magnebot.arm import Arm
from magnebot.ik.orientation_mode import OrientationMode
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.action_status import ActionStatus
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.image_frequency import ImageFrequency
from magnebot.actions.ik_motion import IKMotion


class ReachFor(IKMotion):
    """
    Reach for a target position. The action ends when the magnet is at or near the target position, or if it fails to reach the target.
    The Magnebot may try to reach for the target multiple times, trying different IK orientations each time, or no times, if it knows the action will fail.
    """

    def __init__(self, target: np.array, absolute: bool, arm: Arm, orientation_mode: OrientationMode,
                 target_orientation: TargetOrientation, static: MagnebotStatic, dynamic: MagnebotDynamic,
                 image_frequency: ImageFrequency, arrived_at: float = 0.125):
        """
        :param target: The target position.
        :param absolute: If True, `target` is in absolute world coordinates. If `False`, `target` is relative to the position and rotation of the Magnebot.
        :param arrived_at: If the magnet is this distance or less from `target`, then the action is successful.
        :param arm: [The arm used for this action.](../arm.md)
        :param orientation_mode: [The orientation mode.](../../arm_articulation.md)
        :param target_orientation: [The target orientation.](../../arm_articulation.md)
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        :param image_frequency: [How image data will be captured during the image.](../image_frequency.md)
        """

        super().__init__(arm=arm, orientation_mode=orientation_mode, target_orientation=target_orientation,
                         static=static, dynamic=dynamic, image_frequency=image_frequency)
        if absolute:
            target = self._absolute_to_relative(position=target)
        self._target_arr: np.array = target
        self._arrived_at: float = arrived_at

    def get_initialization_commands(self, resp: List[bytes]) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp)
        self._set_start_arm_articulation_commands()
        commands.extend(self._evaluate_arm_articulation(resp=resp))
        return commands

    def get_ongoing_commands(self, resp: List[bytes]) -> List[dict]:
        return self._evaluate_arm_articulation(resp=resp)

    def _get_fail_status(self) -> ActionStatus:
        return ActionStatus.failed_to_reach

    def _is_success(self, resp: List[bytes]) -> bool:
        magnet_position = self._absolute_to_relative(position=self.dynamic.joints[self.static.magnets[self._arm]].position)
        return np.linalg.norm(magnet_position - self._target_arr) < self._arrived_at

    def _get_ik_target_position(self) -> np.array:
        return self._target_arr
