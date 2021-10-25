from typing import List
from magnebot.actions.action import Action
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.arm import Arm
from magnebot.image_frequency import ImageFrequency
from magnebot.action_status import ActionStatus


class Stop(Action):
    """
    Stop the Magnebot's wheels and joints at their current positions.
    """

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        commands.extend(self._get_stop_wheels_commands(static=static, dynamic=dynamic))
        for arm in [Arm.left, Arm.right]:
            commands.extend(self._get_stop_arm_commands(arm=arm, static=static, dynamic=dynamic))
        # Make the Magnebot immovable.
        if not dynamic.immovable:
            commands.append({"$type": "set_immovable",
                             "immovable": True,
                             "id": static.robot_id})
        return commands

    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        return []

    def set_status_after_initialization(self) -> None:
        self.status = ActionStatus.success
