from typing import List
from magnebot.action_status import ActionStatus
from magnebot.actions.action import Action


class Wait(Action):
    """
    Make the Magnebot's base immovable and wait for its arms to stop moving. The Magnebot has this action when it is first initialized.
    """

    def get_initialization_commands(self, resp: List[bytes]) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp)
        # Make the Magnebot immovable.
        if not self.dynamic.immovable:
            commands.append({"$type": "set_immovable",
                             "immovable": True,
                             "id": self.static.robot_id})
        return commands

    def get_ongoing_commands(self, resp: List[bytes]) -> List[dict]:
        for joint_id in self.dynamic.joints:
            if self.dynamic.joints[joint_id].moving:
                return []
        self.status = ActionStatus.success
        return []
