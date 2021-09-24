from typing import List
from magnebot.actions.action import Action
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.image_frequency import ImageFrequency
from magnebot.action_status import ActionStatus


class Stop(Action):
    """
    Stop the Magnebot's wheels at their current positions.
    """

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        return self._get_stop_wheels_commands(static=static, dynamic=dynamic)

    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        return []

    def set_status_after_initialization(self) -> None:
        self.status = ActionStatus.success
