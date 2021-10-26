from typing import List
import numpy as np
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
                 target_orientation: TargetOrientation, dynamic: MagnebotDynamic, arrived_at: float = 0.125):
        """
        :param target: The target position.
        :param absolute: If True, `target` is in absolute world coordinates. If `False`, `target` is relative to the position and rotation of the Magnebot.
        :param arrived_at: If the magnet is this distance or less from `target`, then the action is successful.
        :param arm: [The arm used for this action.](../arm.md)
        :param orientation_mode: [The orientation mode.](../ik/orientation_mode.md)
        :param target_orientation: [The target orientation.](../ik/target_orientation.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        """

        super().__init__(arm=arm, orientation_mode=orientation_mode, target_orientation=target_orientation,
                         dynamic=dynamic)
        if absolute:
            target = self._absolute_to_relative(position=target, dynamic=dynamic)
        self._target_arr: np.array = target
        self._arrived_at: float = arrived_at

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        self._set_start_arm_articulation_commands(static=static, dynamic=dynamic)
        commands.extend(self._evaluate_arm_articulation(resp=resp, static=static, dynamic=dynamic))
        return commands

    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        return self._evaluate_arm_articulation(resp=resp, static=static, dynamic=dynamic)

    def _get_fail_status(self) -> ActionStatus:
        return ActionStatus.failed_to_reach

    def _is_success(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> bool:
        magnet_position = self._absolute_to_relative(position=dynamic.joints[static.magnets[self._arm]].position,
                                                     dynamic=dynamic)
        return np.linalg.norm(magnet_position - self._target_arr) < self._arrived_at

    def _get_ik_target_position(self) -> np.array:
        return self._target_arr
