from typing import List, Optional, Dict, Union
from copy import deepcopy
import numpy as np
from tdw.add_ons.robot_base import RobotBase
from tdw.output_data import Version
from tdw.tdw_utils import TDWUtils
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
from magnebot.actions.reset_position import ResetPosition
from magnebot.actions.rotate_camera import RotateCamera
from magnebot.actions.look_at import LookAt
from magnebot.actions.move_camera import MoveCamera
from magnebot.actions.reset_camera import ResetCamera
from magnebot.actions.slide_torso import SlideTorso
from magnebot.actions.stop import Stop
from magnebot.actions.wait import Wait
from magnebot.constants import TDW_VERSION, DEFAULT_CAMERA_POSITION_TORSO, DEFAULT_CAMERA_POSITION_COLUMN
from magnebot.wheel import Wheel


class Magnebot(RobotBase):
    """
    The Magnebot agent is a high-level robotics-like API for [TDW](https://github.com/threedworld-mit/tdw) This high-level API supports:

    - Creating a complex interior environment
    - Directional movement
    - Turning
    - Arm articulation via inverse kinematics (IK)
    - Grasping and dropping objects
    - Image rendering
    - Scene state metadata

    The Magnebot has various [actions](actions/action.md). Each action has a start and end, and has a [status](action_status.md) that indicates if it is ongoing, if it succeeded, or if it failed (and if so, why).

    ***

    ## Basic usage

    You can add a Magnebot to a regular TDW controller:

    ```python
    from tdw.controller import Controller
    from tdw.tdw_utils import TDWUtils
    from magnebot import Magnebot
    from magnebot.action_status import ActionStatus

    m = Magnebot(robot_id=0, position={"x": 0.5, "y": 0, "z": -1})
    c = Controller()
    c.add_ons.append(m)
    c.communicate(TDWUtils.create_empty_room(12, 12))
    m.move_by(1)
    while m.action.status == ActionStatus.ongoing:
        c.communicate([])
    c.communicate({"$type": "terminate"})
    ```

    It is possible to create a multi-agent Magnebot simulation simply by adding more Magnebot agents:

    ```python
    from tdw.controller import Controller
    from tdw.tdw_utils import TDWUtils
    from magnebot import Magnebot
    from magnebot.action_status import ActionStatus

    m0 = Magnebot(robot_id=0, position={"x": 0.5, "y": 0, "z": -1})
    m1 = Magnebot(robot_id=1, position={"x": -0.5, "y": 0, "z": 1})
    c = Controller()
    c.add_ons.extend([m0, m1])
    c.communicate(TDWUtils.create_empty_room(12, 12))
    m0.move_by(1)
    m1.move_by(-2)
    while m0.action.status == ActionStatus.ongoing:
        c.communicate([])
    c.communicate({"$type": "terminate"})
    ```

    For a simplified single-agent API, see [`MagnebotController`](magnebot_controller.md):

    ```python
    from magnebot import MagnebotController

    m = MagnebotController()
    m.init_scene()
    m.move_by(2)
    m.end()
    ```

    ***

    ## Skipped frames

    The `Magnebot` and `MagnebotController` were originally the same code--the controller was a hard-coded single-agent simulation.

    The Magnebot has been designed so that a certain number of physics frames will be skipped per frame that actually returns data back to the controller. The `MagnebotController` does this automatically but you can easily add this to your simulation with a [`StepPhysics`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/add_ons/step_physics.md) object:

    ```python
    from tdw.controller import Controller
    from tdw.tdw_utils import TDWUtils
    from tdw.add_ons.step_physics import StepPhysics
    from magnebot.magnebot import Magnebot

    m = Magnebot()
    s = StepPhysics(10)
    c = Controller()
    c.add_ons.extend([m, s])
    c.communicate(TDWUtils.create_empty_room(12, 12))
    print(m.dynamic.transform.position)
    c.communicate({"$type": "terminate"})
    ```

    ***

    ## Parameter types

    The types `Dict`, `Union`, and `List` are in the [`typing` module](https://docs.python.org/3/library/typing.html).

    #### Dict[str, float]

    Parameters of type `Dict[str, float]` are Vector3 dictionaries formatted like this:

    ```json
    {"x": -0.2, "y": 0.21, "z": 0.385}
    ```

    `y` is the up direction.

    To convert from or to a numpy array:

    ```python
    from tdw.tdw_utils import TDWUtils

    target = {"x": 1, "y": 0, "z": 0}
    target = TDWUtils.vector3_to_array(target)
    print(target) # [1 0 0]
    target = TDWUtils.array_to_vector3(target)
    print(target) # {'x': 1.0, 'y': 0.0, 'z': 0.0}
    ```

    #### Union[int, Dict[str, float], np.ndarray]

    Parameters of type `Union[int, Dict[str, float], np.ndarray]` can be either a Vector3, an [x, y, z] numpy array, or an integer (an object ID).

    #### Arm

    All parameters of type `Arm` require you to import the [Arm enum class](arm.md):

    ```python
    from magnebot import Arm

    print(Arm.left)
    ```

    ***
    """

    # If True, we've already checked the version.
    _CHECKED_VERSION: bool = False

    def __init__(self, robot_id: int = 0, position: Dict[str, float] = None, rotation: Dict[str, float] = None,
                 image_frequency: ImageFrequency = ImageFrequency.once, parent_camera_to_torso: bool = True,
                 visual_camera_mesh: bool = False, visual_camera_scale: Dict[str, float] = None,
                 check_version: bool = True):
        """
        :param robot_id: The ID of the robot.
        :param position: The position of the robot. If None, defaults to `{"x": 0, "y": 0, "z": 0}`.
        :param rotation: The rotation of the robot in Euler angles (degrees). If None, defaults to `{"x": 0, "y": 0, "z": 0}`.
        :param image_frequency: [The frequency of image capture.](image_frequency.md)
        :param parent_camera_to_torso: If True, the camera will be parented to the Magnebot's torso. If False, the camera will be parented to the Magnebot's column.
        :param visual_camera_mesh: If True, the camera will receive a visual mesh. The mesh won't have colliders and won't respond to physics. If False, the camera won't have a visual mesh.
        :param visual_camera_scale: The scale of the visual camera mesh as an x, y, z dictionary. If None, defaults to `{"x": 1, "y": 1, "z": 1}`. Ignored if `visual_camera_mesh == False`.
        :param check_version: If True, check whether an update to the Magnebot API or TDW API is available.
        """

        super().__init__(robot_id=robot_id, position=position, rotation=rotation)
        """:field
        [Cached static data for the Magnebot](magnebot_static.md) such as the IDs and segmentation colors of each joint:
        
        ```python
        from tdw.controller import Controller
        from tdw.tdw_utils import TDWUtils
        from magnebot.magnebot import Magnebot
    
        m = Magnebot()
        c = Controller()
        c.add_ons.append(m)
        c.communicate(TDWUtils.create_empty_room(12, 12))
        for arm_joint in m.static.arm_joints:
            joint_id = m.static.arm_joints[arm_joint]
            segmentation_color = m.static.joints[joint_id].segmentation_color
            print(arm_joint, joint_id, segmentation_color)
        c.communicate({"$type": "terminate"})
        ```
        """
        self.static: Optional[MagnebotStatic] = None
        """:field
        [Per-frame dynamic data for the Magnebot](magnebot_dynamic.md) such as its position and images:
        
        ```python
        from tdw.controller import Controller
        from tdw.tdw_utils import TDWUtils
        from magnebot.magnebot import Magnebot
    
        m = Magnebot()
        c = Controller()
        c.add_ons.append(m)
        c.communicate(TDWUtils.create_empty_room(12, 12))
        print(m.dynamic.transform.position)
        c.communicate({"$type": "terminate"})
        ```
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
        The current (roll, pitch, yaw) angles of the Magnebot's camera in degrees as a numpy array. This is handled outside of `self.state` because it isn't calculated using output data from the build. See: `magnebot.actions.RotateCamera.CAMERA_RPY_CONSTRAINTS` and `self.rotate_camera()`
        """
        self.camera_rpy: np.array = np.array([0, 0, 0])
        self._previous_resp: List[bytes] = list()
        self._previous_action: Optional[Action] = None
        self._check_version: bool = check_version
        self._parent_camera_to_torso: bool = parent_camera_to_torso
        self._visual_camera_mesh: bool = visual_camera_mesh
        if visual_camera_scale is None:
            self._visual_camera_scale: Dict[str, float] = {"x": 1, "y": 1, "z": 1}
        else:
            self._visual_camera_scale = visual_camera_scale

    def get_initialization_commands(self) -> List[dict]:
        """
        This function gets called exactly once per add-on by the controller; don't call this function yourself!

        :return: A list of commands that will initialize this add-on.
        """

        MagnebotDynamic.FRAME_COUNT = 0
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
        if not Magnebot._CHECKED_VERSION:
            commands.append({"$type": "send_version"})
        return commands

    def on_send(self, resp: List[bytes]) -> None:
        """
        This is called after commands are sent to the build and a response is received.

        This function is called automatically by the controller; you don't need to call it yourself.

        :param resp: The response from the build.
        """

        super().on_send(resp=resp)
        self._previous_resp = resp
        if self.action is None or self.action.done:
            return
        else:
            if not self.action.initialized:
                # Some actions can fail immediately.
                if self.action.status == ActionStatus.ongoing:
                    self.action.initialized = True
                    initialization_commands = self.action.get_initialization_commands(resp=resp, static=self.static,
                                                                                      dynamic=self.dynamic, image_frequency=self.image_frequency)
                    # This is an ongoing action.
                    if self.action.status == ActionStatus.ongoing:
                        self.commands.extend(initialization_commands)
                        # Set the status after initialization.
                        # This is required from one-frame actions such as RotateCamera.
                        self.action.set_status_after_initialization()
                        # This action is done. Append end commands.
                        if self.action.status != ActionStatus.ongoing:
                            self.commands.extend(self.action.get_end_commands(resp=resp,
                                                                              static=self.static,
                                                                              dynamic=self.dynamic,
                                                                              image_frequency=self.image_frequency))
            else:
                action_commands = self.action.get_ongoing_commands(resp=resp, static=self.static, dynamic=self.dynamic)
                # This is an ongoing action. Append ongoing commands.
                if self.action.status == ActionStatus.ongoing:
                    self.commands.extend(action_commands)
                # This action is done. Append end commands.
                else:
                    self.commands.extend(self.action.get_end_commands(resp=resp,
                                                                      static=self.static,
                                                                      dynamic=self.dynamic,
                                                                      image_frequency=self.image_frequency))
            # This action ended. Remember it as the previous action.
            if self.action.status != ActionStatus.ongoing:
                # Mark the action as done.
                self.action.done = True
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
                             previous=self._previous_action, dynamic=self.dynamic)

    def turn_to(self, target: Union[int, Dict[str, float], np.ndarray], aligned_at: float = 1) -> None:
        """
        Turn the Magnebot to face a target object or position.

        While turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

        :param target: The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array.
        :param aligned_at: If the difference between the current angle and the target angle is less than this value, then the action is successful.
        """

        self.action = TurnTo(target=target, resp=self._previous_resp, aligned_at=aligned_at,
                             collision_detection=self.collision_detection, previous=self._previous_action,
                             dynamic=self.dynamic)

    def move_by(self, distance: float, arrived_at: float = 0.1) -> None:
        """
        Move the Magnebot forward or backward by a given distance.

        :param distance: The target distance. If less than zero, the Magnebot will move backwards.
        :param arrived_at: If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful.
        """

        self.action = MoveBy(distance=distance, arrived_at=arrived_at, collision_detection=self.collision_detection,
                             previous=self._previous_action, dynamic=self.dynamic)

    def move_to(self, target: Union[int, Dict[str, float], np.ndarray], arrived_at: float = 0.1, aligned_at: float = 1,
                arrived_offset: float = 0) -> None:
        """
        Move to a target object or position. This combines turn_to() followed by move_by().

        :param target: The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array.
        :param arrived_at: If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful.
        :param aligned_at: If the difference between the current angle and the target angle is less than this value, then the action is successful.
        :param arrived_offset: Offset the arrival position by this value. This can be useful if the Magnebot needs to move to an object but shouldn't try to move to the object's centroid. This is distinct from `arrived_at` because it won't affect the Magnebot's braking solution.
        """

        self.action = MoveTo(target=target, resp=self._previous_resp, dynamic=self.dynamic,
                             collision_detection=self.collision_detection, arrived_at=arrived_at, aligned_at=aligned_at,
                             arrived_offset=arrived_offset, previous=self._previous_action)

    def stop(self) -> None:
        """
        Stop the Magnebot's wheels at their current positions.
        """

        self.action = Stop()

    def reach_for(self, target: Union[Dict[str, float], np.ndarray], arm: Arm, absolute: bool = True,
                  orientation_mode: OrientationMode = OrientationMode.auto,
                  target_orientation: TargetOrientation = TargetOrientation.auto, arrived_at: float = 0.125) -> None:
        """
        Reach for a target position. The action ends when the magnet is at or near the target position, or if it fails to reach the target.
        The Magnebot may try to reach for the target multiple times, trying different IK orientations each time, or no times, if it knows the action will fail.

        :param target: The target position. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array.
        :param arm: [The arm that will reach for the target.](arm.md)
        :param absolute: If True, `target` is in absolute world coordinates. If `False`, `target` is relative to the position and rotation of the Magnebot.
        :param arrived_at: If the magnet is this distance or less from `target`, then the action is successful.
        :param orientation_mode: [The orientation mode.](ik/orientation_mode.md)
        :param target_orientation: [The target orientation.](ik/target_orientation.md)
        """

        if isinstance(target, dict):
            target = TDWUtils.vector3_to_array(target)

        self.action = ReachFor(target=target, arm=arm, absolute=absolute, orientation_mode=orientation_mode,
                               target_orientation=target_orientation, arrived_at=arrived_at, dynamic=self.dynamic)

    def grasp(self, target: int, arm: Arm, orientation_mode: OrientationMode = OrientationMode.auto,
              target_orientation: TargetOrientation = TargetOrientation.auto) -> None:
        """
        Try to grasp a target object.
        The action ends when either the Magnebot grasps the object, can't grasp it, or fails arm articulation.

        :param target: The ID of the target object.
        :param arm: [The arm that will reach for and grasp the target.](arm.md)
        :param orientation_mode: [The orientation mode.](ik/orientation_mode.md)
        :param target_orientation: [The target orientation.](ik/target_orientation.md)
        """

        self.action = Grasp(target=target, arm=arm, orientation_mode=orientation_mode,
                            target_orientation=target_orientation, dynamic=self.dynamic)

    def drop(self, target: int, arm: Arm, wait_for_object: bool = True) -> None:
        """
        Drop an object held by a magnet.

        :param target: The ID of the object currently held by the magnet.
        :param arm: [The arm of the magnet holding the object.](arm.md)
        :param wait_for_object: If True, the action will continue until the object has finished falling. If False, the action advances the simulation by exactly 1 frame.
        """

        self.action = Drop(arm=arm, target=target, wait_for_object=wait_for_object, dynamic=self.dynamic)

    def reset_arm(self, arm: Arm) -> None:
        """
        Reset an arm to its neutral position.

        :param arm: [The arm to reset.](arm.md)
        """

        self.action = ResetArm(arm=arm)

    def reset_position(self) -> None:
        """
        Reset the Magnebot so that it isn't tipping over.
        This will rotate the Magnebot to the default rotation (so that it isn't tipped over) and move the Magnebot to the nearest empty space on the floor.
        It will also drop any held objects.

        This will be interpreted by the physics engine as a _very_ sudden and fast movement.
        This action should only be called if the Magnebot is a position that will prevent the simulation from continuing (for example, if the Magnebot fell over).
        """

        self.action = ResetPosition()

    def rotate_camera(self, roll: float = 0, pitch: float = 0, yaw: float = 0) -> None:
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

        self.action = RotateCamera(roll=roll, pitch=pitch, yaw=yaw, camera_rpy=self.camera_rpy)
        # Update the camera RPY angles.
        self.camera_rpy = np.array(self.action.camera_rpy[:])

    def look_at(self, target: Union[int, Dict[str, float], np.ndarray]) -> None:
        """
        Rotate the Magnebot's camera to look at a target object or position.

        This action is not compatible with `rotate_camera()` because it will ignore (roll, pitch, yaw) constraints; if you use this action, `rotate_camera()` won't work as intended until you call `reset_camera()`.

        :param target: The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array.
        """

        self.action = LookAt(target=target)

    def move_camera(self, position: Union[Dict[str, float], np.ndarray]) -> None:
        """
        Move the Magnebot's camera by an offset position.

        By default, the camera is parented to the torso and will continue to move when the torso moves. You can prevent this by setting `parent_camera_to_torso=False` in the Magnebot constructor.

        :param position: The positional offset that the camera will move by.
        """

        self.action = MoveCamera(position=position)

    def reset_camera(self, position: bool = True, rotation: bool = True) -> None:
        """
        Reset the rotation of the Magnebot's camera to its default angles and/or its default position relative to its parent (by default, its parent is the torso).

        :param position: If True, reset the camera's position.
        :param rotation: If True, reset the camera' rotation.
        """

        self.action = ResetCamera(position=position, rotation=rotation, parented_to_torso=self._parent_camera_to_torso)
        # Reset the camera RPY angles.
        if rotation:
            self.camera_rpy = np.array([0, 0, 0])

    def reset(self, position: Dict[str, float] = None, rotation: Dict[str, float] = None) -> None:
        super().reset(position=position, rotation=rotation)
        self.action = None
        self._previous_action = None
        self.camera_rpy: np.array = np.array([0, 0, 0])
        self.collision_detection = CollisionDetection()
        self._previous_resp.clear()
        self.commands.append(self._get_parent_avatar_command())

    def slide_torso(self, height: float) -> None:
        """
        Slide the Magnebot's torso up or down.

        :param height: The height of the torso. Must be between `magnebot.constants.TORSO_MIN_Y` and `magnebot.constants.TORSO_MAX_Y`.
        """

        self.action = SlideTorso(height=height)

    def _cache_static_data(self, resp: List[bytes]) -> None:
        """
        Cache static output data.

        :param resp: The response from the build.
        """

        if self._check_version and not Magnebot._CHECKED_VERSION:
            Magnebot._CHECKED_VERSION = True
            check_version()
            version_data = get_data(resp=resp, d_type=Version)
            build_version = version_data.get_tdw_version()
            PyPi.required_tdw_version_is_installed(required_version=TDW_VERSION, build_version=build_version,
                                                   comparison=">=")
        self.static = MagnebotStatic(robot_id=self.robot_id, resp=resp)
        self._set_robot_joint_ids()
        # Wait for the joints to finish moving.
        self.action = Wait()
        # Add an avatar and set up its camera.
        self.commands.extend([{"$type": "create_avatar",
                               "type": "A_Img_Caps_Kinematic",
                               "id": self.static.avatar_id},
                              {"$type": "set_pass_masks",
                               "pass_masks": ["_img", "_id", "_depth"],
                               "avatar_id": self.static.avatar_id},
                              self._get_parent_avatar_command(),
                              {"$type": "enable_image_sensor",
                               "enable": False,
                               "avatar_id": self.static.avatar_id},
                              {"$type": "set_img_pass_encoding",
                               "value": False}])
        # Visualize the camera.
        if self._visual_camera_mesh:
            self.commands.append({"$type": "add_visual_camera_mesh",
                                  "avatar_id": self.static.avatar_id,
                                  "scale": self._visual_camera_scale})

    def _set_dynamic_data(self, resp: List[bytes]) -> None:
        """
        Set dynamic data.

        :param resp: The response from the build.
        """

        if self.dynamic is None:
            frame_count = 0
        else:
            self.dynamic: MagnebotDynamic
            frame_count = self.dynamic.frame_count
        dynamic = MagnebotDynamic(static=self.static, resp=resp, frame_count=frame_count)
        wheels_moving: Dict[Wheel, bool] = dict()
        if self.dynamic is not None:
            # Set whether the wheels are moving.
            for wheel in self.static.wheels:
                wheel_id = self.static.wheels[wheel]
                wheels_moving[wheel] = np.linalg.norm(self.dynamic.joints[wheel_id].angles[0] -
                                                      dynamic.joints[wheel_id].angles[0]) > 0.1
        self.dynamic = self._set_joints_moving(dynamic)
        # Set whether the wheels are moving.
        for wheel in wheels_moving:
            self.dynamic.joints[self.static.wheels[wheel]].moving = wheels_moving[wheel]

    def _get_add_robot_command(self) -> dict:
        """
        :return: The command to add the Magnebot.
        """

        return {"$type": "add_magnebot",
                "position": self.initial_position,
                "rotation": self.initial_rotation,
                "id": self.robot_id}

    def _get_parent_avatar_command(self) -> dict:
        """
        :return: A command to parent the avatar to the Magenbot. The parent body part is determined by `self._parent_camera_to_torso` and the `parent_camera_to_torso` constructor parameter.
        """

        return {"$type": "parent_avatar_to_robot",
                "position": DEFAULT_CAMERA_POSITION_TORSO if self._parent_camera_to_torso else DEFAULT_CAMERA_POSITION_COLUMN,
                "body_part_id": self.static.arm_joints[ArmJoint.torso if self._parent_camera_to_torso else ArmJoint.column],
                "avatar_id": self.static.avatar_id,
                "id": self.static.robot_id}
