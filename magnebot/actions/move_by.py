from typing import Dict, List
import numpy as np
from tdw.tdw_utils import TDWUtils
from magnebot.actions.action import Action
from magnebot.actions.wheel_motion import WheelMotion
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

        """:field
        The target distance.
        """
        self.distance: float = distance
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
        self._max_attempts: int = int(np.abs(distance) * 5)
        if self._max_attempts < 5:
            self._max_attempts = 5
        self._attempts: int = 0
        self._move_frames: int = 0
        self._initial_distance: float = np.linalg.norm(self._target_position_arr - self._initial_position_arr)
        # We're already here.
        if self._initial_distance < arrived_at:
            self.status = ActionStatus.success

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
            overshot: bool = False
            # Check if any wheels stopped turning.
            wheels_are_turning = True
            for wheel in static.wheels:
                if not dynamic.joints[static.wheels[wheel]].moving:
                    wheels_are_turning = False
                    break
            # We are still moving.
            if self._move_frames < 2000 and wheels_are_turning:
                if self._wheel_motion_complete(static=static, resp=resp):
                    if self.status == ActionStatus.success:
                        return []
                    else:
                        next_attempt = True
                        # When the Magnebot overshoots, "reset" the parameters of the action to aim for a new target.
                        overshot = True
                        self._initial_position_arr = np.array(p1[:])
                        self._initial_position_v3 = TDWUtils.array_to_vector3(self._initial_position_arr)
                        self._target_position_arr = dynamic.transform.position + (dynamic.transform.forward * self.distance)
                        self._target_position_v3 = TDWUtils.array_to_vector3(self._target_position_arr)
                        d = np.linalg.norm(p1 - self._target_position_arr)
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
                    self._spin = (d / WHEEL_CIRCUMFERENCE) * 360 * (1 if self.distance > 0 else -1)
                    # If this isn't an overshoot, multiply the spin by a magic number.
                    if not overshot:
                        self._spin *= 0.5
                    d_total = np.linalg.norm(p1 - self._initial_position_arr)
                    if d_total > self._initial_distance:
                        self._spin *= -1
                    commands.extend(self._get_start_wheels_commands(static=static, dynamic=dynamic))
                    return commands
            else:
                return []

    def _previous_was_same(self, previous: Action) -> bool:
        if isinstance(previous, MoveBy):
            return (previous.distance > 0 and self.distance > 0) or (previous.distance < 0 and self.distance < 0)
        else:
            return False

    def _get_start_wheels_commands(self, static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        commands = []
        for wheel in static.wheels:
            # Get the target from the current joint angles. Add or subtract the speed.
            target = dynamic.joints[static.wheels[wheel]].angles[0] + self._spin
            commands.append({"$type": "set_revolute_target",
                             "target": target,
                             "joint_id": static.wheels[wheel],
                             "id": static.robot_id})
        return commands
