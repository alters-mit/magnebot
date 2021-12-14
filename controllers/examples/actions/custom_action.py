from typing import List
from tdw.tdw_utils import TDWUtils
from tdw.controller import Controller
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.image_frequency import ImageFrequency
from magnebot.actions.action import Action
from magnebot.action_status import ActionStatus
from magnebot.magnebot import Magnebot
from magnebot.util import get_default_post_processing_commands

"""
Define two custom actions and a custom Magnebot agent.
"""


class SetScreenSize(Action):
    def __init__(self, width: int, height: int):
        super().__init__()
        self.width: int = width
        self.height: int = height

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        commands.append({"$type": "set_screen_size",
                         "width": self.width,
                         "height": self.height})
        return commands

    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        return []

    def set_status_after_initialization(self) -> None:
        self.status = ActionStatus.success


class ApplyForceToWheels(Action):
    def __init__(self, force: float):
        super().__init__()
        self.force = force

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        if self.force == 0:
            self.status = ActionStatus.failure
            return []
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        if dynamic.immovable:
            commands.append({"$type": "set_immovable",
                             "immovable": False,
                             "id": static.robot_id})
        for wheel in static.wheels:
            commands.append({"$type": "add_torque_to_revolute",
                             "torque": self.force,
                             "joint_id": static.wheels[wheel],
                             "id": static.robot_id})
        return commands

    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        moving = True
        for wheel in static.wheels:
            if not dynamic.joints[static.wheels[wheel]].moving:
                moving = False
                break
        if not moving:
            self.status = ActionStatus.success
        return []

    def get_end_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                         image_frequency: ImageFrequency,) -> List[dict]:
        commands = super().get_end_commands(resp=resp, static=static, dynamic=dynamic, image_frequency=image_frequency)
        commands.append({"$type": "set_immovable",
                         "immovable": True,
                         "id": static.robot_id})
        return commands


class MyMagnebot(Magnebot):
    def apply_force_to_wheels(self, force: float) -> None:
        self.action = ApplyForceToWheels(force=force)

    def set_screen_size(self, width: int, height: int) -> None:
        self.action = SetScreenSize(width=width, height=height)


if __name__ == "__main__":
    c = Controller()
    magnebot = MyMagnebot()
    c.add_ons.append(magnebot)
    commands = [{"$type": "load_scene",
                 "scene_name": "ProcGenScene"},
                TDWUtils.create_empty_room(12, 12)]
    commands.extend(get_default_post_processing_commands())
    c.communicate(commands)
    # Set the screen size.
    magnebot.set_screen_size(width=256, height=256)
    c.communicate([])
    print(magnebot.action.status)
    magnebot.apply_force_to_wheels(force=70)
    while magnebot.action.status == ActionStatus.ongoing:
        c.communicate([])
    c.communicate([])
    print(magnebot.action.status)
    print(magnebot.dynamic.transform.position)
    c.communicate({"$type": "terminate"})
