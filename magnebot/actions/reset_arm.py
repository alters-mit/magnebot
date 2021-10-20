from typing import List
from magnebot.action_status import ActionStatus
from magnebot.actions.arm_motion import ArmMotion
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.image_frequency import ImageFrequency


class ResetArm(ArmMotion):
    """
    Reset an arm to its neutral position.
    """

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        commands.extend(self._get_reset_arm_commands(arm=self._arm, static=static))
        return commands

    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        if not self._joints_are_moving(static=static, dynamic=dynamic):
            self.status = ActionStatus.success
        return []
