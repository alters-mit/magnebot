from typing import List, Dict
from csv import DictReader
from abc import ABC, abstractmethod
from overrides import final
import numpy as np
from tdw.tdw_utils import TDWUtils
from tdw.quaternion_utils import QuaternionUtils
from magnebot.turn_constants import TurnConstants
from magnebot.action_status import ActionStatus
from magnebot.actions.action import Action
from magnebot.actions.wheel_motion import WheelMotion
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.collision_detection import CollisionDetection
from magnebot.paths import TURN_CONSTANTS_PATH
from magnebot.constants import DEFAULT_WHEEL_FRICTION, WHEEL_CIRCUMFERENCE, BRAKE_FRICTION, MAGNEBOT_CIRCUMFERENCE


class Turn(WheelMotion, ABC):
    """
    Abstract base class for a turn action.
    """

    # The angle at which to start braking at while turning.
    _BRAKE_ANGLE: float = 0.5
    # Turn constants by angle.
    _TURN_CONSTANTS: Dict[int, TurnConstants] = dict()
    with TURN_CONSTANTS_PATH.open(encoding='utf-8-sig') as f:
        r = DictReader(f)
        for row in r:
            _TURN_CONSTANTS[int(row["angle"])] = TurnConstants(angle=int(row["angle"]),
                                                               magic_number=float(row["magic_number"]),
                                                               outer_track=float(row["outer_track"]),
                                                               front=float(row["front"]))

    def __init__(self, dynamic: MagnebotDynamic, collision_detection: CollisionDetection, aligned_at: float = 1,
                 previous: Action = None):
        """
        :param aligned_at: If the difference between the current angle and the target angle is less than this value, then the action is successful.
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        :param collision_detection: [The collision detection rules.](../collision_detection.md)
        :param previous: The previous action, if any.
        """

        self._angle = self._get_angle(dynamic=dynamic)
        super().__init__(dynamic=dynamic, collision_detection=collision_detection, previous=previous)
        self._clamp_angle()
        self._aligned_at: float = aligned_at
        self._max_attempts: int = int((np.abs(self._angle) + 1) / 2)
        self._attempts: int = 0
        self._turn_frames: int = 0
        # The current angle to turn by.
        self._delta_angle: float = self._angle
        # The previous angle to turn by.
        self._previous_delta_angle: float = self._angle
        # The initial forward directional vector of the Magnebot.
        self._initial_forward_vector: np.array = TDWUtils.array_to_vector3(dynamic.transform.forward)
        self._initial_rotation = dynamic.transform.rotation
        # The minimum friction for the wheels.
        self._minimum_friction: float = DEFAULT_WHEEL_FRICTION
        if self._max_attempts == 0:
            self.status = ActionStatus.success

    @final
    def _get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        # Get the change in angle from the initial rotation.
        theta = QuaternionUtils.get_y_angle(self._initial_rotation,
                                            dynamic.transform.rotation)
        if np.abs(self._angle - theta) < self._aligned_at:
            self.status = ActionStatus.success
            return []
        elif not self._is_valid_ongoing(dynamic=dynamic):
            return []
        else:
            next_attempt: bool = False
            if self._turn_frames < 2000 and self._wheels_are_turning(static=static, dynamic=dynamic):
                if self._wheel_motion_complete(static=static, resp=resp):
                    if self.status == ActionStatus.success:
                        return []
                    else:
                        next_attempt = True
            else:
                next_attempt = True
            # Check the position of the Magnebot between frames and adjust the wheels accordingly.
            if not next_attempt:
                self._turn_frames += 1
                if self._aligned_at <= 1:
                    return [self._get_turn_command(static=static)]
                else:
                    return []
        if next_attempt:
            if self._attempts == 0:
                return self._get_start_wheels_commands(static=static, dynamic=dynamic)
            # Course-correct the angle.
            self._delta_angle = self._angle - theta
            # Handle cases where we flip over the axis.
            if np.abs(self._previous_delta_angle) < np.abs(self._delta_angle):
                self._delta_angle *= -1
            self._previous_delta_angle = self._delta_angle
            # Set a new turn.
            return self._get_start_wheels_commands(static=static, dynamic=dynamic)
        else:
            return []

    @final
    def _previous_was_same(self, previous: Action) -> bool:
        if isinstance(previous, Turn):
            return (previous._angle > 0 and self._angle > 0) or (previous._angle < 0 and self._angle < 0)
        else:
            return False

    def _clamp_angle(self) -> None:
        """
        Clamp the target angle to be within 180 degrees.
        """

        if np.abs(self._angle) > 180:
            if self._angle > 0:
                self._angle -= 360
            else:
                self._angle += 360

    @final
    def _get_start_wheels_commands(self, static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        """
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)

        :return: A list of commands to start spinning the wheels.
        """

        if self._attempts >= self._max_attempts:
            self.status = ActionStatus.failed_to_turn
            return []

        commands = []
        if self._delta_angle < 9.25:
            commands.extend(self._set_brake_wheel_drives(static=static))
            self._minimum_friction = BRAKE_FRICTION
        pass
        # Get the nearest turn constants.
        da = int(np.abs(self._delta_angle))
        if da >= 179:
            turn_constants = Turn._TURN_CONSTANTS[179]
        else:
            turn_constants = Turn._TURN_CONSTANTS[120]
            for turn_constants_angle in Turn._TURN_CONSTANTS:
                if da <= turn_constants_angle:
                    turn_constants = Turn._TURN_CONSTANTS[turn_constants_angle]
                    break
        # Calculate the delta angler of the wheels, given the target angle of the Magnebot.
        # Source: https://answers.unity.com/questions/1120115/tank-wheels-and-treads.html
        # The distance that the Magnebot needs to travel, defined as a fraction of its circumference.
        d = (self._delta_angle / 360.0) * MAGNEBOT_CIRCUMFERENCE
        spin = (d / WHEEL_CIRCUMFERENCE) * 360 * turn_constants.magic_number
        # Set the direction of the wheels for the turn and send commands.
        commands = []
        if spin > 0:
            inner_track = "right"
        else:
            inner_track = "left"
        for wheel in static.wheels:
            if inner_track in wheel.name:
                wheel_spin = spin
            else:
                wheel_spin = spin * turn_constants.outer_track
            if "front" in wheel.name:
                wheel_spin *= turn_constants.front
            # Spin one side of the wheels forward and the other backward to effect a turn.
            if "left" in wheel.name:
                target = dynamic.joints[static.wheels[wheel]].angles[0] + wheel_spin
            else:
                target = dynamic.joints[static.wheels[wheel]].angles[0] - wheel_spin

            commands.append({"$type": "set_revolute_target",
                             "target": target,
                             "joint_id": static.wheels[wheel],
                             "id": static.robot_id})
        self._attempts += 1
        self._turn_frames = 0
        return commands

    @abstractmethod
    def _get_angle(self, dynamic: MagnebotDynamic) -> float:
        """
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)

        :return: The angle to turn by.
        """

        raise Exception()

    @abstractmethod
    def _get_turn_command(self, static: MagnebotStatic) -> dict:
        """
        :param static: [The static Magnebot data.](../magnebot_static.md)

        :return: The "during turn" command.
        """

        raise Exception()
