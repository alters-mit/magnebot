from typing import Dict, List
import numpy as np
from tdw.tdw_utils import TDWUtils
from magnebot.actions.action import Action
from magnebot.actions.wheel_motion import WheelMotion
from magnebot.image_frequency import ImageFrequency
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.collision_detection import CollisionDetection
from magnebot.constants import DEFAULT_WHEEL_FRICTION, WHEEL_CIRCUMFERENCE, BRAKE_FRICTION
from magnebot.action_status import ActionStatus


class MoveBy(WheelMotion):
    """
    Move the Magnebot forward or backward by a given distance.
    """

    # The distance at which to start braking while moving.
    _BRAKE_DISTANCE: float = 0.1

    def __init__(self, distance: float, dynamic: MagnebotDynamic, collision_detection: CollisionDetection,
                 arrived_at: float = 0.1, previous: Action = None):
        """
        :param distance: The target distance.
        :param arrived_at: If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful.
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        :param collision_detection: [The collision detection rules.](../collision_detection.md)
        :param previous: The previous action, if any.
        """

        self._distance: float = distance
        self._arrived_at: float = arrived_at
        super().__init__(dynamic=dynamic, collision_detection=collision_detection, previous=previous)
        # Get the initial state.
        self._initial_position_arr: np.array = np.array(dynamic.transform.position[:])
        self._initial_position_v3: Dict[str, float] = TDWUtils.array_to_vector3(self._initial_position_arr)
        self._target_position_arr: np.array = dynamic.transform.position + (dynamic.transform.forward * distance)
        self._target_position_v3: Dict[str, float] = TDWUtils.array_to_vector3(self._target_position_arr)
        self._minimum_friction: float = DEFAULT_WHEEL_FRICTION
        # Get the angle that we expect the wheels should turn to in order to move the Magnebot.
        self._spin: float = (distance / WHEEL_CIRCUMFERENCE) * 360
        self._max_attempts: int = int(np.abs(distance) * 3)
        self._attempts: int = 0
        self._move_frames: int = 0
        self._initial_distance: float = np.linalg.norm(self._target_position_arr - self._initial_position_arr)
        # We're already here.
        if self._initial_distance < arrived_at:
            self.status = ActionStatus.success

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        # Start spinning the wheels.
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        commands.extend(self._get_wheel_commands(static=static, dynamic=dynamic))
        return commands

    def _get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        p1 = dynamic.transform.position
        d = np.linalg.norm(p1 - self._target_position_arr)
        # We've arrived at the target.
        if d < self._arrived_at:
            self.status = ActionStatus.success
            return []
        elif not self._is_valid_ongoing(dynamic=dynamic):
            return []
        else:
            next_attempt: bool = False
            # We are still moving.
            if self._move_frames < 2000 and self._wheels_are_turning(static=static, dynamic=dynamic):
                if self._wheel_motion_complete(resp=resp):
                    if self.status == ActionStatus.success:
                        return []
                    else:
                        next_attempt = True
                # Check the position of the Magnebot between frames and adjust the wheels accordingly.
                if not next_attempt:
                    self._move_frames += 1
                    if self._arrived_at < 0.2:
                        return [{"$type": "set_magnebot_wheels_during_move",
                                 "position": self._target_position_v3,
                                 "origin": self._initial_position_v3,
                                 "arrived_at": self._arrived_at,
                                 "brake_distance": MoveBy._BRAKE_DISTANCE,
                                 "minimum_friction": self._minimum_friction,
                                 "id": static.robot_id}]
            else:
                next_attempt = True
            # Try another attempt.
            if next_attempt:
                self._move_frames = 0
                self._attempts += 1
                # We made too many attempts.
                if self._attempts >= self._max_attempts:
                    self.status = ActionStatus.failed_to_move
                    return []
                # Start spinning the wheels again.
                else:
                    commands = []
                    # Start to brake.
                    if d < 0.5:
                        commands.extend(self._set_brake_wheel_drives(static=static))
                        self._minimum_friction = BRAKE_FRICTION
                    self._spin = (d / WHEEL_CIRCUMFERENCE) * 360 * 0.5 * (1 if self._distance > 0 else -1)
                    d_total = np.linalg.norm(p1 - self._initial_position_arr)
                    if d_total > self._initial_distance:
                        self._spin *= -1
                    commands.extend(self._get_wheel_commands(static=static, dynamic=dynamic))
                    return commands
            else:
                return []

    def _previous_was_same(self, previous: Action) -> bool:
        if isinstance(previous, MoveBy):
            return (previous._distance > 0 and self._distance > 0) or (previous._distance < 0 and self._distance < 0)
        else:
            return False

    def _get_wheel_commands(self, static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        """
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)

        :return: A list of commands to start spinning the wheels.
        """

        commands = []
        for wheel in static.wheels:
            # Get the target from the current joint angles. Add or subtract the speed.
            target = dynamic.joints[static.wheels[wheel]].angles[0] + self._spin
            commands.append({"$type": "set_revolute_target",
                             "target": target,
                             "joint_id": static.wheels[wheel],
                             "id": static.robot_id})
        return commands
