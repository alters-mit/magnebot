from typing import List
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.action_status import ActionStatus
from magnebot.collision_detection import CollisionDetection
from magnebot.actions.wheel_motion import WheelMotion
from magnebot.actions.action import Action
from magnebot.actions.move_by import MoveBy
from magnebot.magnebot import Magnebot
from magnebot.util import get_default_post_processing_commands

"""
Define a custom ApplyForceToWheels and use it in a controller.
"""


class ApplyForceToWheels(WheelMotion):
    def __init__(self, force: float, dynamic: MagnebotDynamic, collision_detection: CollisionDetection, previous: Action = None):
        super().__init__(dynamic=dynamic, collision_detection=collision_detection, previous=previous, set_torso=True)
        self.force: float = force

    def _previous_was_same(self, previous: Action) -> bool:
        if isinstance(previous, MoveBy):
            return (previous.distance > 0 and self.force > 0) or (previous.distance < 0 and self.force < 0)
        elif isinstance(previous, ApplyForceToWheels):
            return (previous.force > 0 and self.force > 0) or (previous.force < 0 and self.force < 0)
        else:
            return False

    def _get_start_wheels_commands(self, static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        commands = []
        for wheel in static.wheels:
            commands.append({"$type": "add_torque_to_revolute",
                             "torque": self.force,
                             "joint_id": static.wheels[wheel],
                             "id": static.robot_id})
        return commands

    def _get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        # The action is success if the wheels aren't turning and there isn't a collision.
        if self._is_valid_ongoing(dynamic=dynamic) and not self._wheels_are_turning(static=static, dynamic=dynamic):
            self.status = ActionStatus.success
        return []


class MyMagnebot(Magnebot):
    def apply_force_to_wheels(self, force: float) -> None:
        self.action = ApplyForceToWheels(force=force,
                                         collision_detection=self.collision_detection,
                                         dynamic=self.dynamic)


if __name__ == "__main__":
    c = Controller()
    magnebot = MyMagnebot()
    c.add_ons.append(magnebot)
    commands = [{"$type": "load_scene",
                 "scene_name": "ProcGenScene"},
                TDWUtils.create_empty_room(12, 12)]
    commands.extend(get_default_post_processing_commands())
    c.communicate(commands)
    magnebot.apply_force_to_wheels(force=70)
    while magnebot.action.status == ActionStatus.ongoing:
        c.communicate([])
    c.communicate([])
    print(magnebot.action.status)
    print(magnebot.dynamic.transform.position)
    c.communicate({"$type": "terminate"})
