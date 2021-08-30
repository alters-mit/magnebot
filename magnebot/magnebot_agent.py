from typing import List, Optional, Dict
from copy import deepcopy
import numpy as np
from tdw.add_ons.robot_base import RobotBase
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.arm_joint import ArmJoint
from magnebot.actions.action import Action
from magnebot.action_status import ActionStatus


class MagnebotAgent(RobotBase):
    def __init__(self, robot_id: int = 0, position: Dict[str, float] = None, rotation: Dict[str, float] = None):
        """
        :param robot_id: The ID of the robot.
        :param position: The position of the robot. If None, defaults to `{"x": 0, "y": 0, "z": 0}`.
        :param rotation: The rotation of the robot in Euler angles (degrees). If None, defaults to `{"x": 0, "y": 0, "z": 0}`.
        """

        super().__init__(robot_id=robot_id, position=position, rotation=rotation)
        self.action: Optional[Action] = None
        self._previous_action: Optional[Action] = None
        """:field
        The current (roll, pitch, yaw) angles of the Magnebot's camera in degrees as a numpy array. This is handled outside of `self.state` because it isn't calculated using output data from the build. See: `Magnebot.CAMERA_RPY_CONSTRAINTS` and `self.rotate_camera()`
        """
        self.camera_rpy: np.array = np.array([0, 0, 0])

    def get_initialization_commands(self) -> List[dict]:
        MagnebotDynamic.FRAME_COUNT = 0
        self.action = None
        self._previous_action = None
        self.camera_rpy: np.array = np.array([0, 0, 0])
        commands = super().get_initialization_commands()
        commands.append({"$type": "send_magnebot",
                         "frequency": "always"})
        return commands

    def on_send(self, resp: List[bytes]) -> None:
        super().on_send(resp=resp)
        if self.action is None:
            return
        else:
            if not self.action.initialized:
                # Some actions can fail immediately.
                if self.action.status == ActionStatus.ongoing:
                    self.action.initialized = True
                    initialization_commands = self.action.get_initialization_commands(resp=resp)
                    # This is an ongoing action.
                    if self.action.status == ActionStatus.ongoing:
                        self.commands.extend(initialization_commands)
                        # Set the status after initialization.
                        # This is required from one-frame actions such as RotateCamera.
                        self.action.set_status_after_initialization()
            else:
                action_commands = self.action.get_ongoing_commands(resp=resp)
                # This is an ongoing action. Append ongoing commands.
                if self.action.status == ActionStatus.ongoing:
                    self.commands.extend(action_commands)
                # This action is done. Append end commands.
                else:
                    self.commands.extend(self.action.get_end_commands(resp=resp))
            # This action ended. Remember it as the previous action.
            if self.action.status != ActionStatus.ongoing:
                # Remember the previous action.
                self._previous_action = deepcopy(self.action)

    def _cache_static_data(self, resp: List[bytes]) -> None:
        self.static = MagnebotStatic(robot_id=self.robot_id, resp=resp)
        # Add an avatar and set up its camera.
        self.commands.extend([{"$type": "create_avatar",
                               "type": "A_Img_Caps_Kinematic",
                               "id": self.static.avatar_id},
                              {"$type": "set_pass_masks",
                               "pass_masks": ["_img", "_id", "_depth"],
                               "avatar_id": self.static.avatar_id},
                              {"$type": "parent_avatar_to_robot",
                               "position": {"x": 0, "y": 0.053, "z": 0.1838},
                               "body_part_id": self.static.arm_joints[ArmJoint.torso],
                               "avatar_id": self.static.avatar_id},
                              {"$type": "enable_image_sensor",
                               "enable": False,
                               "avatar_id": self.static.avatar_id}])

    def _set_dynamic_data(self, resp: List[bytes]) -> None:
        dynamic = MagnebotDynamic(resp=resp, robot_id=self.robot_id, body_parts=self.static.body_parts,
                                  previous=self.dynamic)
        self.dynamic = self._set_joints_moving(dynamic)

    def _get_add_robot_command(self) -> dict:
        return {"$type": "add_magnebot",
                "position": self.initial_position,
                "rotation": self.initial_rotation,
                "id": self.robot_id}
