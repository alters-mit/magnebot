from typing import List
from magnebot.action_status import ActionStatus
from magnebot.actions.action import Action
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.image_frequency import ImageFrequency


class Wait(Action):
    """
    Make the Magnebot's base immovable and wait for its arms to stop moving. The Magnebot has this action when it is first initialized.
    """

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        # Make the Magnebot immovable.
        if not dynamic.immovable:
            commands.append({"$type": "set_immovable",
                             "immovable": True,
                             "id": static.robot_id})
        return commands

    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        for joint_id in dynamic.joints:
            if dynamic.joints[joint_id].moving:
                return []
        self.status = ActionStatus.success
        return []
