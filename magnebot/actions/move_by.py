from typing import Dict, List
import numpy as np
from tdw.tdw_utils import TDWUtils
from tdw.output_data import OutputData, MagnebotWheels
from magnebot.actions.action import Action
from magnebot.actions.wheel_motion import WheelMotion
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.collision_detection import CollisionDetection
from magnebot.constants import DEFAULT_WHEEL_FRICTION, WHEEL_CIRCUMFERENCE
from magnebot.action_status import ActionStatus


class MoveBy(WheelMotion):
    # The distance at which to start braking while moving.
    _BRAKE_DISTANCE: float = 0.1

    def __init__(self, distance: float, static: MagnebotStatic, dynamic: MagnebotDynamic,
                 collision_detection: CollisionDetection, arrived_at: float = 0.1, previous: Action = None):
        self._distance: float = distance
        self._arrived_at: float = arrived_at
        super().__init__(static=static, dynamic=dynamic, collision_detection=collision_detection, previous=previous)
        # Get the initial state.
        self._initial_position_arr: np.array = np.array(self.dynamic.transform.position[:])
        self._initial_position_v3: Dict[str, float] = TDWUtils.array_to_vector3(self._initial_position_arr)
        self._target_position_arr: np.array = self.dynamic.transform.position + (self.dynamic.transform.forward * distance)
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

    def get_initialization_commands(self, resp: List[bytes]) -> List[dict]:
        # Start spinning the wheels.
        commands = super().get_initialization_commands(resp=resp)
        commands.extend(self._get_wheel_commands())
        return commands

    def get_ongoing_commands(self, resp: List[bytes]) -> List[dict]:
        p1 = self.dynamic.transform.position
        d = np.linalg.norm(self._target_position_arr - p1)
        if d < self._arrived_at:
            self.status = ActionStatus.success
        elif self._is_valid_ongoing():
            if self._move_frames < 2000:
                for i in range(len(resp) - 1):
                    if OutputData.get_data_type_id(resp[i]) == "mwhe":
                        mwhe = MagnebotWheels(resp[i])
                        if mwhe.get_success():
                            self.status = ActionStatus.success
                        else:
                            self.status = ActionStatus.failed_to_move
                if self.status == ActionStatus.ongoing:
                    if self._arrived_at < 0.2:
                        return[{"$type": "set_magnebot_wheels_during_move",
                                "position": self._target_position_v3,
                                "origin": self._initial_position_v3,
                                "arrived_at": self._arrived_at,
                                "brake_distance": MoveBy._BRAKE_DISTANCE,
                                "minimum_friction": self._minimum_friction}]
                    else:
                        self._move_frames += 1
                        return []
            # Make another attempt.
            else:
                self._move_frames = 0
                self._attempts += 1
                # We made too many attempts.
                if self._attempts >= self._max_attempts:
                    self.status = ActionStatus.failed_to_move
                # Start spinning the wheels again.
                else:
                    self._spin = (d / WHEEL_CIRCUMFERENCE) * 360 * 0.5 * (1 if self._distance > 0 else -1)
                    d_total = np.linalg.norm(p1 - self._initial_position_arr)
                    if d_total > self._initial_distance:
                        self._spin *= -1
                    return self._get_wheel_commands()

    def _previous_was_same(self, previous: Action) -> bool:
        if isinstance(previous, MoveBy):
            return (previous._distance > 0 and self._distance > 0) or (previous._distance < 0 and self._distance < 0)
        else:
            return False

    def _get_wheel_commands(self) -> List[dict]:
        commands = []
        for wheel in self.static.wheels:
            # Get the target from the current joint angles. Add or subtract the speed.
            target = self.dynamic.joints[self.static.wheels[wheel]].angles[0] + self._spin
            commands.append({"$type": "set_revolute_target",
                             "target": target,
                             "joint_id": self.static.wheels[wheel],
                             "id": self.static.robot_id})
        return commands
