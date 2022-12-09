from typing import List
from abc import ABC
from overrides import final
from magnebot.arm import Arm
from magnebot.actions.action import Action
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.image_frequency import ImageFrequency


class ArmMotion(Action, ABC):
    """
    Abstract base class for arm motions.
    """

    def __init__(self, arm: Arm, set_torso_at_end: bool):
        """
        :param arm: [The arm used for this action.](../arm.md)
        :param set_torso_at_end: If True, set the position of the torso when the arms stop moving at the end of the action.
        """

        super().__init__()
        # The arm used for the action.
        self._arm: Arm = arm
        self._set_torso_at_end: bool = set_torso_at_end

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

    def get_end_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                         image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_end_commands(resp=resp, static=static, dynamic=dynamic, image_frequency=image_frequency)
        commands.extend(self._get_stop_arm_commands(arm=self._arm, static=static, dynamic=dynamic,
                                                    set_torso=self._set_torso_at_end))
        return commands

    @final
    def _joints_are_moving(self, static: MagnebotStatic, dynamic: MagnebotDynamic) -> bool:
        """
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)

        :return: True if these joints are still moving.
        """

        for arm_joint in ArmMotion.JOINT_ORDER[self._arm]:
            if dynamic.joints[static.arm_joints[arm_joint]].moving:
                return True
        return False
