from typing import List
import numpy as np
from magnebot.actions.action import Action
from magnebot.arm_joint import ArmJoint
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.image_frequency import ImageFrequency
from magnebot.action_status import ActionStatus
from magnebot.constants import TORSO_MIN_Y, TORSO_MAX_Y


class SlideTorso(Action):
    """
    Slide the Magnebot's torso up or down.
    """

    def __init__(self, height: float):
        """
        :param height: The height of the torso. Must be between `magnebot.constants.TORSO_MIN_Y` and `magnebot.constants.TORSO_MAX_Y`.
        """

        super().__init__()
        """:field
        The torso position value.
        """
        self.position: float = self._y_position_to_torso_position(max(min(height, TORSO_MAX_Y), TORSO_MIN_Y))

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        # Make the Magnebot immovable.
        if not dynamic.immovable:
            commands.append({"$type": "set_immovable",
                             "immovable": True,
                             "id": static.robot_id})
        # Start moving the torso.
        commands.append({"$type": "set_prismatic_target",
                         "joint_id": static.arm_joints[ArmJoint.torso],
                         "id": static.robot_id,
                         "target": self.position})
        return commands

    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        # Wait until the torso stops moving.
        if not dynamic.joints[static.arm_joints[ArmJoint.torso]].moving:
            self.status = ActionStatus.success
        return []

    def get_end_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                         image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_end_commands(resp=resp, static=static, dynamic=dynamic, image_frequency=image_frequency)
        # Stop moving the torso.
        joint_id = static.arm_joints[ArmJoint.torso]
        commands.append({"$type": "set_prismatic_target",
                         "joint_id": joint_id,
                         "target": float(np.radians(dynamic.joints[joint_id].angles)),
                         "id": static.robot_id})
        return commands
