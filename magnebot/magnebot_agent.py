from typing import List, Optional, Dict, Union
from copy import deepcopy
import numpy as np
from tdw.add_ons.robot_base import RobotBase
from tdw.output_data import Version
from tdw.release.pypi import PyPi
from magnebot.util import get_data, check_version
from magnebot.arm import Arm
from magnebot.ik.orientation_mode import OrientationMode
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.arm_joint import ArmJoint
from magnebot.actions.action import Action
from magnebot.action_status import ActionStatus
from magnebot.image_frequency import ImageFrequency
from magnebot.collision_detection import CollisionDetection
from magnebot.actions.turn_by import TurnBy
from magnebot.actions.turn_to import TurnTo
from magnebot.actions.move_by import MoveBy
from magnebot.actions.move_to import MoveTo
from magnebot.actions.reach_for import ReachFor
from magnebot.actions.grasp import Grasp
from magnebot.actions.drop import Drop
from magnebot.actions.reset_arm import ResetArm
from magnebot.actions.rotate_camera import RotateCamera
from magnebot.actions.reset_camera import ResetCamera
from magnebot.actions.wait import Wait
from magnebot.constants import TDW_VERSION


class MagnebotAgent(RobotBase):
    # If True, we've already checked the version.
    _CHECKED_VERSION: bool = False

    def __init__(self, robot_id: int = 0, position: Dict[str, float] = None, rotation: Dict[str, float] = None,
                 image_frequency: ImageFrequency = ImageFrequency.once, check_pypi_version: bool = True):
        """
        :param robot_id: The ID of the robot.
        :param position: The position of the robot. If None, defaults to `{"x": 0, "y": 0, "z": 0}`.
        :param rotation: The rotation of the robot in Euler angles (degrees). If None, defaults to `{"x": 0, "y": 0, "z": 0}`.
        :param image_frequency: [The frequency of image capture.](image_Frequency.md)
        :param check_pypi_version: If True, check whether an update to the Magnebot API is available.
        """

        super().__init__(robot_id=robot_id, position=position, rotation=rotation)
        """:field
        [Cached static data for the Magnebot.](magnebot_static.md)
        """
        self.static: Optional[MagnebotStatic] = None
        """:field
        [Per-frame dynamic data for the Magnebot (including images).](magnebot_dynamic.md)
        """
        self.dynamic: Optional[MagnebotDynamic] = None
        """:field
        The Magnebot's current [action](actions/action.md). Can be None (no ongoing action).
        """
        self.action: Optional[Action] = None
        """:field
        This sets [how often images are captured](image_frequency.md).
        """
        self.image_frequency: ImageFrequency = image_frequency
        """:field
        [The collision detection rules.](collision_detection.md) This determines whether the Magnebot will immediately stop moving or turning when it collides with something.
        """
        self.collision_detection: CollisionDetection = CollisionDetection()
        """:field
        The current (roll, pitch, yaw) angles of the Magnebot's camera in degrees as a numpy array. This is handled outside of `self.state` because it isn't calculated using output data from the build. See: `Magnebot.CAMERA_RPY_CONSTRAINTS` and `self.rotate_camera()`
        """
        self.camera_rpy: np.array = np.array([0, 0, 0])
        self._previous_action: Optional[Action] = None
        if check_pypi_version:
            check_version()

    def get_initialization_commands(self) -> List[dict]:
        """
        This function gets called exactly once per add-on. To re-initialize, set `self.initialized = False`.

        :return: A list of commands that will initialize this add-on.
        """

        MagnebotDynamic.FRAME_COUNT = 0
        self.action = None
        self._previous_action = None
        self.camera_rpy: np.array = np.array([0, 0, 0])
        commands = super().get_initialization_commands()
        commands.extend([{"$type": "send_magnebots",
                         "frequency": "always"},
                         {"$type": "send_transforms",
                          "frequency": "always"},
                         {"$type": "send_collisions",
                          "enter": True,
                          "stay": False,
                          "exit": True,
                          "collision_types": ["obj", "env"]}])
        if not MagnebotAgent._CHECKED_VERSION:
            commands.append({"$type": "send_version"})
        return commands

    def on_send(self, resp: List[bytes]) -> None:
        """
        This is called after commands are sent to the build and a response is received.

        Use this function to send commands to the build on the next frame, given the `resp` response.
        Any commands in the `self.commands` list will be sent on the next frame.

        :param resp: The response from the build.
        """

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

    def turn_by(self, angle: float, aligned_at: float = 1) -> None:
        """
        Turn the Magnebot by an angle.

        While turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

        :param angle: The target angle in degrees. Positive value = clockwise turn.
        :param aligned_at: If the difference between the current angle and the target angle is less than this value, then the action is successful.
        """

        self.action = TurnBy(angle=angle, aligned_at=aligned_at, collision_detection=self.collision_detection,
                             previous=self._previous_action, static=self.static, dynamic=self.dynamic,
                             image_frequency=self.image_frequency)

    def turn_to(self, target: Union[int, Dict[str, float], np.ndarray], aligned_at: float = 1) -> None:
        """
        Turn the Magnebot to face a target object or position.

        While turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

        :param target: The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array.
        :param aligned_at: If the difference between the current angle and the target angle is less than this value, then the action is successful.
        """

        self.action = TurnTo(target=target, aligned_at=aligned_at, collision_detection=self.collision_detection,
                             previous=self._previous_action, static=self.static, dynamic=self.dynamic,
                             image_frequency=self.image_frequency)

    def move_by(self, distance: float, arrived_at: float = 0.1) -> None:
        """
        Move the Magnebot forward or backward by a given distance.

        :param distance: The target distance. If less than zero, the Magnebot will move backwards.
        :param arrived_at: If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful.
        """

        self.action = MoveBy(distance=distance, arrived_at=arrived_at, collision_detection=self.collision_detection,
                             previous=self._previous_action, static=self.static, dynamic=self.dynamic,
                             image_frequency=self.image_frequency)

    def move_to(self, target: Union[int, Dict[str, float], np.ndarray], arrived_at: float = 0.1, aligned_at: float = 1) -> None:
        """
        Move to a target object or position. This combines turn_to() followed by move_by().

        :param target: The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array.
        :param arrived_at: If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful.
        :param aligned_at: If the difference between the current angle and the target angle is less than this value, then the action is successful.
        """

        self.action = MoveTo(target=target, static=self.static, dynamic=self.dynamic,
                             image_frequency=self.image_frequency, collision_detection=self.collision_detection,
                             arrived_at=arrived_at, aligned_at=aligned_at, previous=self._previous_action)

    def reach_for(self, target: Dict[str, float], arm: Arm, absolute: bool = True,
                  orientation_mode: OrientationMode = OrientationMode.auto,
                  target_orientation: TargetOrientation = TargetOrientation.auto, arrived_at: float = 0.125) -> None:
        """
        Reach for a target position. The action ends when the magnet is at or near the target position, or if it fails to reach the target.
        The Magnebot may try to reach for the target multiple times, trying different IK orientations each time, or no times, if it knows the action will fail.

        :param target: The target position.
        :param arm: The arm that will reach for the target.
        :param absolute: If True, `target` is in absolute world coordinates. If `False`, `target` is relative to the position and rotation of the Magnebot.
        :param arrived_at: If the magnet is this distance or less from `target`, then the action is successful.
        :param orientation_mode: [The orientation mode.](../arm_articulation.md)
        :param target_orientation: [The target orientation.](../arm_articulation.md)
        """

        self.action = ReachFor(target=target, arm=arm, absolute=absolute, orientation_mode=orientation_mode,
                               target_orientation=target_orientation, arrived_at=arrived_at, static=self.static,
                               dynamic=self.dynamic, image_frequency=self.image_frequency)

    def grasp(self, target: int, arm: Arm, orientation_mode: OrientationMode = OrientationMode.auto,
              target_orientation: TargetOrientation = TargetOrientation.auto) -> None:
        """
        Try to grasp a target object.
        The action ends when either the Magnebot grasps the object, can't grasp it, or fails arm articulation.

        :param target: The ID of the target object.
        :param arm: [The arm used for this action.](../arm.md)
        :param orientation_mode: [The orientation mode.](../arm_articulation.md)
        :param target_orientation: [The target orientation.](../arm_articulation.md)
        """

        self.action = Grasp(target=target, arm=arm, orientation_mode=orientation_mode,
                            target_orientation=target_orientation, static=self.static, dynamic=self.dynamic,
                            image_frequency=self.image_frequency)

    def drop(self, target: int, arm: Arm, wait_for_object: bool) -> None:
        """
        Drop an object held by a magnet.

        :param target: The ID of the object currently held by the magnet.
        :param arm: The arm of the magnet holding the object.
        :param wait_for_object: If True, the action will continue until the object has finished falling. If False, the action advances the simulation by exactly 1 frame.
        """

        self.action = Drop(arm=arm, target=target, wait_for_object=wait_for_object,
                           static=self.static, dynamic=self.dynamic, image_frequency=self.image_frequency)

    def reset_arm(self, arm: Arm) -> None:
        """
        Reset an arm to its neutral position.

        :param arm: The arm to reset.
        """

        self.action = ResetArm(arm=arm, static=self.static, dynamic=self.dynamic, image_frequency=self.image_frequency)

    def rotate_camera(self, roll: float, pitch: float, yaw: float) -> None:
        """
        Rotate the Magnebot's camera by the (roll, pitch, yaw) axes.

        Each axis of rotation is constrained by the following limits:

        | Axis | Minimum | Maximum |
        | --- | --- | --- |
        | roll | -55 | 55 |
        | pitch | -70 | 70 |
        | yaw | -85 | 85 |

        :param roll: The roll angle in degrees.
        :param pitch: The pitch angle in degrees.
        :param yaw: The yaw angle in degrees.
        """

        self.action = RotateCamera(roll=roll, pitch=pitch, yaw=yaw, camera_rpy=self.camera_rpy, static=self.static,
                                   dynamic=self.dynamic, image_frequency=self.image_frequency)

    def reset_camera(self) -> None:
        """
        Reset the rotation of the Magnebot's camera to its default angles.
        """

        self.action = ResetCamera(camera_rpy=self.camera_rpy, static=self.static, dynamic=self.dynamic,
                                  image_frequency=self.image_frequency)

    def _cache_static_data(self, resp: List[bytes]) -> None:
        if not MagnebotAgent._CHECKED_VERSION:
            MagnebotAgent._CHECKED_VERSION = True
            version_data = get_data(resp=resp, d_type=Version)
            build_version = version_data.get_tdw_version()
            PyPi.required_tdw_version_is_installed(required_version=TDW_VERSION, build_version=build_version,
                                                   comparison=">=")
        self.static = MagnebotStatic(robot_id=self.robot_id, resp=resp)
        # Wait for the joints to finish moving.
        self.action = Wait(static=self.static,
                           dynamic=MagnebotDynamic(robot_id=self.robot_id,
                                                   resp=resp,
                                                   body_parts=self.static.body_parts,
                                                   frame_count=0),
                           image_frequency=self.image_frequency)
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
                               "avatar_id": self.static.avatar_id,
                               "id": self.static.robot_id},
                              {"$type": "set_anti_aliasing",
                               "mode": "subpixel",
                               "avatar_id": self.static.avatar_id},
                              {"$type": "enable_image_sensor",
                               "enable": False,
                               "avatar_id": self.static.avatar_id}])

    def _set_dynamic_data(self, resp: List[bytes]) -> None:
        if self.dynamic is None:
            frame_count = 0
        else:
            self.dynamic: MagnebotDynamic
            frame_count = self.dynamic.frame_count
        dynamic = MagnebotDynamic(resp=resp, robot_id=self.robot_id, body_parts=self.static.body_parts,
                                  previous=self.dynamic, frame_count=frame_count)
        self.dynamic = self._set_joints_moving(dynamic)
        if self.action is not None:
            self.action.dynamic = dynamic

    def _get_add_robot_command(self) -> dict:
        return {"$type": "add_magnebot",
                "position": self.initial_position,
                "rotation": self.initial_rotation,
                "id": self.robot_id}
