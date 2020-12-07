import random
from json import loads
import numpy as np
import matplotlib.pyplot
from typing import List, Dict, Optional, Union, Tuple
from ikpy.chain import Chain
from ikpy.link import OriginLink, URDFLink
from ikpy.utils import geometry
from tdw.floorplan_controller import FloorplanController
from tdw.output_data import Version, StaticRobot, SegmentationColors, Bounds, Rigidbodies, Raycast
from tdw.tdw_utils import TDWUtils
from tdw.object_init_data import AudioInitData
from tdw.py_impact import PyImpact, ObjectInfo
from tdw.release.pypi import PyPi
from magnebot.util import get_data
from magnebot.object_static import ObjectStatic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.scene_state import SceneState
from magnebot.action_status import ActionStatus
from magnebot.paths import SPAWN_POSITIONS_PATH
from magnebot.arm import Arm
from magnebot.joint_type import JointType
from magnebot.arm_joint import ArmJoint


class Magnebot(FloorplanController):
    """
    [TDW controller](https://github.com/threedworld-mit/tdw) for Magnebots.

    ```python
    from magnebot import Magnebot

    m = Magnebot()
    # Initializes the scene.
    m.init_scene(scene="2a", layout=1)
    ```

    ***

    ## Parameter types

    #### Dict[str, float]

    All parameters of type `Dict[str, float]` are Vector3 dictionaries formatted like this:

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

    A parameter of type `Union[Dict[str, float], int]]` can be either a Vector3 or an integer (an object ID).

    The types `Dict`, `Union`, and `List` are in the [`typing` module](https://docs.python.org/3/library/typing.html).

    #### Arm

    All parameters of type `Arm` require you to import the [Arm enum class](arm.md):

    ```python
    from magnebot import Arm

    print(Arm.left)
    ```

    ***

    """

    # Global forward directional vector.
    _FORWARD = np.array([0, 0, 1])

    # Load default audio values for objects.
    __OBJECT_AUDIO = PyImpact.get_object_info()
    # The camera roll, pitch, yaw constraints in degrees.
    CAMERA_RPY_CONSTRAINTS = [55, 70, 85]

    # The order in which joint angles will be set.
    JOINT_ORDER: Dict[Arm, List[ArmJoint]] = {Arm.left: [ArmJoint.column,
                                                         ArmJoint.shoulder_left,
                                                         ArmJoint.elbow_left,
                                                         ArmJoint.wrist_left],
                                              Arm.right: [ArmJoint.column,
                                                          ArmJoint.shoulder_right,
                                                          ArmJoint.elbow_right,
                                                          ArmJoint.wrist_right]}
    # The expected joint articulation per joint
    JOINT_AXES: Dict[ArmJoint, JointType] = {ArmJoint.column: JointType.revolute,
                                             ArmJoint.shoulder_left: JointType.spherical,
                                             ArmJoint.elbow_left: JointType.revolute,
                                             ArmJoint.wrist_left: JointType.spherical,
                                             ArmJoint.shoulder_right: JointType.spherical,
                                             ArmJoint.elbow_right: JointType.revolute,
                                             ArmJoint.wrist_right: JointType.spherical}
    # Prismatic joint limits for the torso.
    TORSO_LIMITS = [0.21, 1.5]
    # The default height of the torso.
    DEFAULT_TORSO_Y = 1

    def __init__(self, port: int = 1071, launch_build: bool = True,
                 screen_width: int = 256, screen_height: int = 256, debug: bool = False):
        """
        :param port: The socket port. [Read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/getting_started.md#command-line-arguments) for more information.
        :param launch_build: If True, the build will launch automatically on the default port (1071). If False, you will need to launch the build yourself (for example, from a Docker container).
        :param screen_width: The width of the screen in pixels.
        :param screen_height: The height of the screen in pixels.
        :param debug: If True, enable debug mode and output debug messages to the console.
        """

        super().__init__(port=port, launch_build=launch_build)

        self._debug = debug

        """:field
        Dynamic data for all of the most recent frame (i.e. the frame after doing an action such as `move_to()`). [Read this](scene_state.md) for a full API.
        """
        self.state: Optional[SceneState] = None

        """:field
        The current (roll, pitch, yaw) angles of the Magnebot's camera in degrees.
        
        This is handled outside of `self.state` because it isn't calculated using output data from the build.
        
        See: `Magnebot.CAMERA_RPY_CONSTRAINTS` and `Magnebot.rotate_camera()`
        """
        self.camera_rpy: np.array([0, 0, 0])

        # Commands to initialize objects.
        self._object_init_commands: Dict[int, List[dict]] = dict()

        """
        Data for all objects in the scene that is static (won't change between frames), such as object IDs, mass, etc. Key = the ID of the object. [Read the full API here](object_static.md).
        
        ```python
        from magnebot import Magnebot
        
        m = Magnebot()
        m.init_scene(scene="2a", layout=1)
        
        # Print each object ID and segmentation color.     
        for object_id in m.objects_static:
            o = m.objects_static[object_id]
            print(object_id, o.segmentation_color)
        ```
        """
        self.objects_static: Dict[int, ObjectStatic] = dict()

        """:field
        A dictionary. Key = a hashable representation of the object's segmentation color. Value = The object ID. See `static_object_info` for a dictionary mapped to object ID with additional data.

        ```python
        from tdw.tdw_utils import TDWUtils
        from magnebot import Magnebot

        m = Magnebot()
        m.init_scene(scene="2a", layout=1)

        for hashable_color in m.segmentation_color_to_id:
            object_id = m.segmentation_color_to_id[hashable_color]
            # Convert the hashable color back to an [r, g, b] array.
            color = TDWUtils.hashable_to_color(hashable_color)
        ```
        """
        self.segmentation_color_to_id: Dict[int, int] = dict()

        """:field
        Static data for the Magnebot that doesn't change between frames. [Read this for a full API](magnebot_static.md)
        
        ```python
        from magnebot import Magnebot

        m = Magnebot()
        m.init_scene(scene="2a", layout=1)
        print(m.magnebot_static.magnets)
        ```
        """
        self.magnebot_static: Optional[MagnebotStatic] = None

        # Commands that will be sent on the next frame.
        self._next_frame_commands: List[dict] = list()

        # Set image encoding to .jpg
        # Set the highest render quality.
        # Set global physics values.
        resp = self.communicate([{"$type": "set_img_pass_encoding",
                                  "value": False},
                                 {"$type": "set_render_quality",
                                  "render_quality": 5},
                                 {"$type": "set_physics_solver_iterations",
                                  "iterations": 16},
                                 {"$type": "set_vignette",
                                  "enabled": False},
                                 {"$type": "set_shadow_strength",
                                  "strength": 1.0},
                                 {"$type": "set_screen_size",
                                  "width": screen_width,
                                  "height": screen_height},
                                 {"$type": "send_version"}])

        # Make sure that the build is the correct version.
        if not launch_build:
            version = get_data(resp=resp, d_type=Version)
            build_version = version.get_tdw_version()
            python_version = PyPi.get_installed_tdw_version(truncate=True)
            if build_version != python_version:
                print(f"Your installed version of tdw ({python_version}) doesn't match the version of the build "
                      f"{build_version}. This might cause errors!")

    def init_scene(self, scene: str, layout: int, room: int = -1) -> ActionStatus:
        """
        Initialize a scene, populate it with objects, and add the Magnebot. The simulation will advance through frames until the Magnebot's body is in its neutral position.

        **Always call this function before any other API calls.**

        Set the `scene` and `layout` parameters in `init_scene()` to load an interior scene with furniture and props. Set the `room` to spawn the avatar in the center of a room.

        ```python
        from magnebot import Magnebot

        m = Magnebot()
        m.init_scene(scene="2b", layout=0, room=1)

        # Your code here.
        ```

        Valid scenes, layouts, and rooms:

        | `scene` | `layout` | `room` |
        | --- | --- | --- |
        | 1a, 1b, 1c | 0, 1, 2 | 0, 1, 2, 3, 4, 5, 6 |
        | 2a, 2b, 2c | 0, 1, 2 | 0, 1, 2, 3, 4, 5, 6, 7, 8 |
        | 4a, 4b, 4c | 0, 1, 2 | 0, 1, 2, 3, 4, 5, 6, 7 |
        | 5a, 5b, 5c | 0, 1, 2 | 0, 1, 2, 3 |

        Images of each scene+layout combination can be found [here](https://github.com/alters-mit/magnebot/tree/master/Documentation/images/floorplans).

        You can safely call `init_scene()` more than once to reset the simulation.

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_bend` (Technically this is _possible_, but it shouldn't ever happen.)

        :param scene: The name of an interior floorplan scene. Each number (1, 2, etc.) has a different shape, different rooms, etc. Each letter (a, b, c) is a cosmetically distinct variant with the same floorplan.
        :param layout: The furniture layout of the floorplan. Each number (0, 1, 2) will populate the floorplan with different furniture in different positions.
        :param room: The index of the room that the Magnebot will spawn in the center of. If `room == -1` the room will be chosen randomly.
        """

        commands = self.get_scene_init_commands(scene=scene, layout=layout, audio=True)
        rooms = loads(SPAWN_POSITIONS_PATH.read_text())[scene[0]][str(layout)]
        if room == -1:
            room = random.randint(0, len(rooms) - 1)
        assert 0 <= room < len(rooms), f"Invalid room: {room}"
        commands.extend(self._get_scene_init_commands(magnebot_position=rooms[room]))
        resp = self.communicate(commands)
        self._cache_static_data(resp=resp)
        # Wait for the Magnebot to reset to its neutral position.
        status = self._do_arm_motion()
        self._end_action()
        return status

    def turn_by(self, angle: float, aligned_at: float = 3) -> ActionStatus:
        """
        Turn the Magnebot by an angle.

        The Magnebot will turn by small increments to align with the target angle.

        When turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_turn`

        :param angle: The target angle in degrees. Positive value = clockwise turn.
        :param aligned_at: If the different between the current angle and the target angle is less than this value, then the action is successful.

        :return: An `ActionStatus` indicating if the Magnebot turned by the angle and if not, why.
        """

        def _get_angle_1() -> float:
            """
            :return: The current angle.
            """

            a = TDWUtils.get_angle_between(wheel_state.magnebot_transform.forward, f0)
            if angle_0 < 0:
                a *= -1
            elif a > 180:
                a = 360 - a
            return a

        self._start_action()
        self._start_move_or_turn()
        wheel_state = SceneState(resp=self.communicate([]))
        # The initial forward vector.
        f0 = self.state.magnebot_transform.forward
        speed = angle * 2.5
        # The approximately number of iterations required, given the distance and speed.
        num_attempts = int((np.abs(angle) + 1) / 2)
        attempts = 0
        angle_0 = angle
        if self._debug:
            print(f"num_attempts: {num_attempts}", f"angle_0: {angle_0}", f"speed: {speed}")
        while attempts < num_attempts:
            attempts += 1
            # Set the direction of the wheels for the turn and send commands.
            commands = []
            for wheel in self.magnebot_static.wheels:
                # Get the target from the current joint angles.
                if "left" in wheel.name:
                    target = wheel_state.joint_angles[self.magnebot_static.wheels[wheel]][0] + \
                             (speed if angle > 0 else -speed)
                else:
                    target = wheel_state.joint_angles[self.magnebot_static.wheels[wheel]][0] - \
                             (speed if angle > 0 else -speed)

                commands.append({"$type": "set_revolute_target",
                                 "target": target,
                                 "joint_id": self.magnebot_static.wheels[wheel]})
            # Wait until the wheels are done turning.
            wheels_done = False
            wheel_state = SceneState(resp=self.communicate(commands))
            while not wheels_done:
                wheels_done, wheel_state = self._wheels_are_done(state_0=wheel_state)
            # Get the new angle.
            angle_1 = _get_angle_1()
            if self._debug:
                print(f"speed: {speed}", f"angle_1: {angle_1}")
            # If the difference between the target angle and the current angle is very small, we're done.
            if np.abs(angle_1 - angle_0) < aligned_at:
                self._end_action()
                return ActionStatus.success
            # Adjust the speed.
            if np.abs(angle_1) > np.abs(angle_0):
                if angle_1 > angle_0:
                    speed = (angle_0 - angle_1) * 3.5
                else:
                    speed = (angle_1 - angle_0) * 3.5
        self._end_action()
        angle_1 = _get_angle_1()
        if np.abs(angle_1 - angle_0) < aligned_at:
            return ActionStatus.success
        else:
            return ActionStatus.failed_to_turn

    def turn_to(self, target: Union[int, Dict[str, float]], aligned_at: float = 3) -> ActionStatus:
        """
        Turn the Magnebot to face a target object or position.

        The Magnebot will turn by small increments to align with the target angle.

        When turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_turn`

        :param target: Either the ID of an object or a Vector3 position.
        :param aligned_at: If the different between the current angle and the target angle is less than this value, then the action is successful.

        :return: An `ActionStatus` indicating if the Magnebot turned by the angle and if not, why.
        """

        if isinstance(target, int):
            target = self.state.object_transforms[target].position
        elif isinstance(target, dict):
            target = TDWUtils.vector3_to_array(target)
        else:
            raise Exception(f"Invalid target: {target}")

        angle = TDWUtils.get_angle(forward=self.state.magnebot_transform.forward, origin=self.state.magnebot_transform.position,
                                   position=target)
        return self.turn_by(angle=angle, aligned_at=aligned_at)

    def move_by(self, distance: float, arrived_at: float = 0.1) -> ActionStatus:
        """
        Move the Magnebot forward or backward by a given distance.

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_move`

        :param distance: The target distance. If less than zero, the Magnebot will move backwards.
        :param arrived_at: If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful.

        :return: An `ActionStatus` indicating if the Magnebot moved by `distance` and if not, why.
        """

        self._start_action()
        self._start_move_or_turn()

        # The initial position of the robot.
        p0 = self.state.magnebot_transform.position
        p1 = self.state.magnebot_transform.position + (self.state.magnebot_transform.forward * distance)
        d = np.linalg.norm(p1 - p0)
        # We're already here.
        if d < arrived_at:
            self._end_action()
            if self._debug:
                print(f"No movement. We're already here: {d}")
            return ActionStatus.success

        # Go until we've traversed the distance.
        speed = distance * 150
        # The approximately number of iterations required, given the distance and speed.
        num_attempts = int(np.abs(speed))
        attempts = 0
        # We are trying to adjust the distance.
        if self._debug:
            print(f"num_attempts: {num_attempts}", f"distance: {distance}", f"speed: {speed}")
        # The approximately number of iterations required, given the distance and speed.
        # Wait for the wheels to stop turning.
        wheel_state = SceneState(resp=self.communicate([]))
        while attempts < num_attempts:
            # Move forward a bit and see if we've arrived.
            commands = []
            for wheel in self.magnebot_static.wheels:
                # Get the target from the current joint angles. Add or subtract the speed.
                target = wheel_state.joint_angles[self.magnebot_static.wheels[wheel]][0] + speed
                commands.append({"$type": "set_revolute_target",
                                 "target": target,
                                 "joint_id": self.magnebot_static.wheels[wheel]})
            # Wait for the wheels to stop turning.
            wheel_state = SceneState(resp=self.communicate(commands))
            wheels_turning = True
            while wheels_turning:
                wheels_turning, wheel_state = self._wheels_are_done(state_0=wheel_state)
            # Check if we're at the destination.
            p1 = wheel_state.magnebot_transform.position
            d = np.linalg.norm(p1 - p0)

            # Arrived!
            if np.abs(np.abs(distance) - d) < arrived_at:
                self._end_action()
                return ActionStatus.success
            # Overshot. Adjust the speed.
            if d > np.abs(distance):
                # Go until we've traversed the distance.
                speed = np.abs(d - distance) * 225 * (-1 if speed > 0 else 1)
            attempts += 1
        if self._debug and distance < 0:
            print(f"distance: {distance}", f"d: {d}", f"speed: {speed}")
        self._end_action()
        p1 = wheel_state.magnebot_transform.position
        d = np.linalg.norm(p1 - p0)
        # Arrived!
        if np.abs(np.abs(distance) - d) < arrived_at:
            return ActionStatus.success
        # Failed to arrive.
        else:
            return ActionStatus.failed_to_move

    def move_to(self, target: Union[int, Dict[str, float]], arrived_at: float = 0.1,
                aligned_at: float = 3) -> ActionStatus:
        """
        Move the Magnebot to a target object or position.

        The Magnebot will first try to turn to face the target by internally calling a `turn_to()` action.

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_move`
        - `failed_to_turn`

        :param target: Either the ID of an object or a Vector3 position.
        :param arrived_at: While moving, if at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful.
        :param aligned_at: While turning, if the different between the current angle and the target angle is less than this value, then the action is successful.

        :return: An `ActionStatus` indicating if the Magnebot moved to the target and if not, why.
        """

        # Turn to face the target.
        status = self.turn_to(target=target, aligned_at=aligned_at)
        # Move to the target.
        if status == ActionStatus.success:
            if isinstance(target, int):
                target = self.state.object_transforms[target].position
            elif isinstance(target, dict):
                target = TDWUtils.vector3_to_array(target)
            else:
                raise Exception(f"Invalid target: {target}")

            return self.move_by(distance=np.linalg.norm(self.state.magnebot_transform.position - target),
                                arrived_at=arrived_at)
        else:
            self._end_action()
            return status

    def reach_for(self, target: Dict[str, float], arm: Arm, absolute: bool = False, arrived_at: float = 0.125) -> ActionStatus:
        """
        Reach for a target position.

        The action ends when the Magnebot's magnet reaches arm stops moving. The arm might stop moving if it succeeded at finishing the motion, in which case the action is successful. Or, the arms might stop moving because the motion is impossible, there's an obstacle in the way, if the arm is holding something heavy, and so on.

        Possible [return values](action_status.md):

        - `success`
        - `cannot_reach`
        - `failed_to_reach`

        :param target: The target position for the magnet at the arm to reach.
        :param arm: The arm that will reach for the target.
        :param absolute: If True, `target` is in absolute world coordinates. If `False`, `target` is relative to the position and rotation of the Magnebot.
        :param arrived_at: If the magnet is this distance or less from `target`, then the action is successful.

        :return: An `ActionStatus` indicating if the magnet at the end of the `arm` is at the `target` and if not, why.
        """

        self._start_action()

        # Get the destination, which will be used to determine if the action was a success.
        destination = TDWUtils.vector3_to_array(target)
        if absolute:
            destination = Magnebot._absolute_to_relative(position=destination, state=self.state)

        # Start the IK action.
        status = self._start_ik(target=target, arm=arm, absolute=absolute, arrived_at=arrived_at)
        if status != ActionStatus.success:
            self._end_action()
            return status

        # Wait for the arm motion to end.
        self._do_arm_motion()
        self._end_action()

        # Check how close the magnet is to the expected relative position.
        magnet_position = Magnebot._absolute_to_relative(
            position=self.state.body_part_transforms[self.magnebot_static.magnets[arm]].position,
            state=self.state)
        d = np.linalg.norm(destination - magnet_position)
        if d < arrived_at:
            return ActionStatus.success
        else:
            if self._debug:
                print(f"Tried and failed to reach for target: {d}")
            return ActionStatus.failed_to_reach

    def grasp(self, target: int, arm: Arm) -> ActionStatus:
        """
        Try to grasp the target object with the arm. The Magnebot will reach for the nearest position on the object.
        If, after bending the arm, the magnet is holding the object, then the action is successful.

        Possible [return values](action_status.md):

        - `success`
        - `cannot_reach`
        - `failed_to_grasp`

        :param target: The ID of the target object.
        :param arm: The arm of the magnet that will try to grasp the object.

        :return: An `ActionStatus` indicating if the magnet at the end of the `arm` is holding the `target` and if not, why.
        """

        if target in self.state.held[arm]:
            if self._debug:
                print(f"Already holding {target}")
            return ActionStatus.success

        self._start_action()

        # Get the mitten's position.
        m_pos = self.state.body_part_transforms[self.magnebot_static.magnets[arm]]
        # Raycast to the target to get a target position.
        # If the raycast fails, just aim for the centroid of the object.
        raycast_ok, target_position = self._get_raycast(origin=m_pos, object_id=target)

        target_position = Magnebot._absolute_to_relative(position=target_position, state=self.state)
        # Start the IK action.
        status = self._start_ik(target=target_position, arm=arm, absolute=True)

        # Enable grasping.
        self._next_frame_commands.append({"$type": "set_magnet_targets",
                                          "arm": arm.name,
                                          "targets": [target]})

        if status != ActionStatus.success:
            self._end_action()
            return status

        # Wait for the arm motion to end.
        self._do_arm_motion()
        self._end_action()

        if target in self.state.held[arm]:
            return ActionStatus.success
        else:
            return ActionStatus.failed_to_grasp

    def drop(self, target: int, arm: Arm) -> ActionStatus:
        """
        Drop an object held by a magnet. This action takes exactly 1 frame; it won't wait for the object to finish falling.

        See [`SceneState.held`](scene_state.md) for a dictionary of held objects.

        Possible [return values](action_status.md):

        - `success`
        - `not_holding`

        :param target: The ID of the object currently held by the magnet.
        :param arm: The arm of the magnet holding the object.

        :return: An `ActionStatus` indicating if the magnet at the end of the `arm` dropped the `target`.
        """

        self._start_action()

        if target in self.state.held[arm]:
            if self._debug:
                print(f"Can't drop {target} because it isn't being held by {arm}")
            self._end_action()
            return ActionStatus.not_holding

        self._next_frame_commands.append({"$type": "drop_from_magnet",
                                          "arm": arm.name,
                                          "object_id": target})
        self._end_action()
        return ActionStatus.success

    def drop_all(self) -> ActionStatus:
        """
        Drop all objects held by either magnet. This action takes exactly 1 frame; it won't wait for the object to finish falling.

        Possible [return values](action_status.md):

        - `success`
        - `not_holding`

        :return: An `ActionStatus` if the Magnebot dropped any objects.
        """

        self._start_action()
        if len(self.state.held[Arm.left]) == 0 and len(self.state.held[Arm.right]) == 0:
            self._end_action()
            return ActionStatus.not_holding

        for arm in self.state.held:
            for object_id in self.state.held[arm]:
                self._next_frame_commands.append({"$type": "drop_from_magnet",
                                                  "arm": arm.name,
                                                  "object_id": object_id})
        self._end_action()
        return ActionStatus.success

    def reset_arm(self, arm: Arm, reset_torso: bool = True) -> ActionStatus:
        """
        Reset an arm to its neutral position. If the arm is holding any objects, it will continue to do so.

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_bend`

        :param arm: The arm that will be reset.
        :param reset_torso: If True, rotate and slide the torso to its neutral rotation and height.

        :return: An `ActionStatus` indicating if the arm reset and if not, why.
        """

        self._start_action()
        self._next_frame_commands.extend(self.__get_reset_arm_commands(arm=arm, reset_torso=reset_torso))

        status = self._do_arm_motion()
        self._end_action()
        return status

    def reset_arms(self) -> ActionStatus:
        """
        Reset both arms and the torso to their neutral positions. If either arm is holding any objects, it will continue to do so.

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_bend`

        :return: An `ActionStatus` indicating if the arms reset and if not, why.
        """

        self._start_action()
        # Reset both arms.
        self._next_frame_commands.extend(self.__get_reset_arm_commands(arm=Arm.left, reset_torso=True))
        self._next_frame_commands.extend(self.__get_reset_arm_commands(arm=Arm.right, reset_torso=False))
        # Wait for both arms to stop moving.
        status = self._do_arm_motion()
        self._end_action()
        return status

    def rotate_camera(self, roll: float = 0, pitch: float = 0, yaw: float = 0) -> ActionStatus:
        """
        Rotate the camera by the (roll, pitch, yaw) axes. This action takes exactly 1 frame.

        Each axis of rotation is constrained (see `Magnebot.CAMERA_RPY_CONSTRAINTS`).

        | Axis | Minimum | Maximum |
        | --- | --- | --- |
        | roll | -55 | 55 |
        | pitch | -70 | 70 |
        | yaw | -85 | 85 |

        See `Magnebot.camera_rpy` for the current (roll, pitch, yaw) angles of the camera.

        ```python
        from magnebot import Magnebot

        m = Magnebot()
        m.init_test_scene()
        status = m.rotate_camera(roll=-10, pitch=-90, yaw=45)
        print(status) # ActionStatus.clamped_camera_rotation
        print(m.camera_rpy) # [-10 -70 45]
        ```

        Possible [return values](action_status.md):

        - `success`
        - `clamped_camera_rotation`

        :param roll: The roll angle in degrees.
        :param pitch: The pitch angle in degrees.
        :param yaw: The yaw angle in degrees.

        :return: An `ActionStatus` indicating if the camera rotated fully or if the rotation was clamped..
        """

        self._start_action()
        deltas = [roll, pitch, yaw]
        # Clamp the rotation.
        clamped = False
        for i in range(len(self.camera_rpy)):
            a = self.camera_rpy[i] + deltas[i]
            if np.abs(a) > Magnebot.CAMERA_RPY_CONSTRAINTS[i]:
                clamped = True
                # Clamp the angle to either the minimum or maximum bound.
                if a > 0:
                    deltas[i] = Magnebot.CAMERA_RPY_CONSTRAINTS[i] - self.camera_rpy[i]
                else:
                    deltas[i] = -Magnebot.CAMERA_RPY_CONSTRAINTS[i] - self.camera_rpy[i]
        # Get the clamped delta.
        if self._debug:
            print(f"Old RPY: {self.camera_rpy}", f"Delta RPY: {deltas}")
        for angle, axis in zip(deltas, ["roll", "pitch", "yaw"]):
            self._next_frame_commands.append({"$type": "rotate_sensor_container_by",
                                              "axis": axis,
                                              "angle": float(angle)})
        self._end_action()
        for i in range(len(self.camera_rpy)):
            self.camera_rpy[i] += deltas[i]
        if self._debug:
            print(f"\tNew RPY: {self.camera_rpy}")
        if clamped:
            return ActionStatus.clamped_camera_rotation
        else:
            return ActionStatus.success

    def reset_camera(self) -> ActionStatus:
        """
        Reset the rotation of the Magnebot's camera to its default angles. This action takes exactly 1 frame.

        ```python
        from magnebot import Magnebot

        m = Magnebot()
        m.init_test_scene()
        m.rotate_camera(roll=-10, pitch=-90, yaw=45)
        m.reset_camera()
        print(m.camera_rpy) # [0 0 0]
        ```

        Possible [return values](action_status.md):

        - `success`

        :return: An `ActionStatus` (always `success`).
        """

        for i in range(len(self.camera_rpy)):
            self.camera_rpy[i] = 0
        self._start_action()
        self._next_frame_commands.append({"$type": "reset_sensor_container_rotation"})
        self._end_action()
        return ActionStatus.success

    def end(self) -> None:
        """
        End the simulation. Terminate the build process.
        """

        self.communicate({"$type": "terminate"})

    def communicate(self, commands: Union[dict, List[dict]]) -> List[bytes]:
        """
        Use this function to send low-level TDW API commands and receive low-level output data. See: [`Controller.communicate()`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/controller.md)

        You shouldn't ever need to use this function, but you might see it in some of the example controllers because they might require a custom scene setup.

        :param commands: Commands to send to the build. See: [Command API](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md).

        :return: The response from the build as a list of byte arrays. See: [Output Data](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/output_data.md).
        """

        if not isinstance(commands, list):
            commands = [commands]
        # Add avatar commands from the previous frame.
        commands.extend(self._next_frame_commands)

        # Clear avatar commands.
        self._next_frame_commands.clear()

        # Send the commands and get a response.
        return super().communicate(commands)

    def _add_object(self, model_name: str, position: Dict[str, float] = None,
                    rotation: Dict[str, float] = None, library: str = "models_core.json",
                    scale: Dict[str, float] = None, audio: ObjectInfo = None,
                    mass: float = None) -> None:
        """
        Add an object to the scene.

        :param model_name: The name of the model.
        :param position: The position of the model.
        :param rotation: The starting rotation of the model. Can be Euler angles or a quaternion.
        :param library: The path to the records file. If left empty, the default library will be selected. See `ModelLibrarian.get_library_filenames()` and `ModelLibrarian.get_default_library()`.
        :param scale: The scale factor of the object. If None, the scale factor is (1, 1, 1)
        :param audio: Audio values for the object. If None, use default values.
        :param mass: If not None, use this mass instead of the default.
        """

        # Get the data.
        # There isn't any audio in this simulation, but we use `AudioInitData` anyway to derive physics values.
        if audio is None:
            audio = Magnebot.__OBJECT_AUDIO[model_name]
        if mass is not None:
            audio.mass = mass
        init_data = AudioInitData(name=model_name, position=position, rotation=rotation, scale_factor=scale,
                                  audio=audio, library=library)
        object_id, object_commands = init_data.get_commands()
        self._object_init_commands[object_id] = object_commands

    def _end_action(self) -> None:
        """
        Set the scene state at the end of an action.
        """

        # These commands can't be added directly as a parameter to `communicate()`
        # because sometimes `_start_action()` will be called on the same frame, which disables the camera.
        self._next_frame_commands.extend([{"$type": "enable_image_sensor",
                                           "enable": True},
                                          {"$type": "send_images"},
                                          {"$type": "send_camera_matrices",
                                           "ids": ["a"]},
                                          {"$type": "set_immovable",
                                           "immovable": False},
                                          {"$type": "set_magnet_targets",
                                           "arm": Arm.left.name,
                                           "targets": []},
                                          {"$type": "set_magnet_targets",
                                           "arm": Arm.right.name,
                                           "targets": []}])
        # Send the commands (see `communicate()` for how `_next_frame_commands` are handled).
        self.state = SceneState(resp=self.communicate([]))

    def _wheels_are_done(self, state_0: SceneState) -> Tuple[bool, SceneState]:
        """
        Advances one frame and then determines if the wheels are still turning.

        :param state_0: The scene state from the previous frame.

        :return: True if none of the wheels are turning.
        """

        resp = self.communicate([])
        state_1 = SceneState(resp=resp)
        for w_id in self.magnebot_static.wheels.values():
            if np.linalg.norm(state_0.joint_angles[w_id][0] -
                              state_1.joint_angles[w_id][0]) > 0.1:
                return False, state_1
        return True, state_1

    def _get_scene_init_commands(self, magnebot_position: Dict[str, float]) -> List[dict]:
        """
        :param magnebot_position: The position of the Magnebot.

        :return: A list of commands that every controller needs for initializing the scene.
        """

        # Add the Magnebot.
        # Set the maximum number of held objects per magnet.
        # Set the number of objects that the Magnebot can hold.
        # Add the avatar (camera).
        # Parent the avatar to the Magnebot.
        # Set pass masks.
        # Disable the image sensor.
        commands = [{"$type": "add_magnebot",
                     "position": magnebot_position},
                    {"$type": "set_immovable",
                     "immovable": True},
                    {"$type": "create_avatar",
                     "type": "A_Img_Caps_Kinematic"},
                    {"$type": "parent_avatar_to_robot",
                     "position": {"x": 0, "y": 0.923, "z": 0.1838}},
                    {"$type": "set_pass_masks",
                     "pass_masks": ["_img", "_id", "_depth"]},
                    {"$type": "enable_image_sensor",
                     "enable": False}]
        # Add the objects.
        for object_id in self._object_init_commands:
            commands.extend(self._object_init_commands[object_id])
        # Request output data.
        commands.extend([{"$type": "send_robots",
                          "frequency": "always"},
                         {"$type": "send_transforms",
                          "frequency": "always"},
                         {"$type": "send_magnebots",
                          "frequency": "always"},
                         {"$type": "send_static_robots",
                          "frequency": "once"},
                         {"$type": "send_segmentation_colors",
                          "frequency": "once"},
                         {"$type": "send_rigidbodies",
                          "frequency": "once"},
                         {"$type": "send_bounds",
                          "frequency": "once"},
                         {"$type": "send_collisions",
                          "enter": True,
                          "stay": False,
                          "exit": False,
                          "collision_types": ["obj", "env"]}])
        return commands

    def _start_action(self) -> None:
        """
        Start the next action.
        """

        self._next_frame_commands.append({"$type": "enable_image_sensor",
                                          "enable": False})

    def _start_move_or_turn(self) -> None:
        """
        Start a move or turn action.
        """

        # Move the torso up to its default height to prevent anything from dragging.
        self._next_frame_commands.append({"$type": "set_prismatic_target",
                                          "joint_id": self.magnebot_static.arm_joints[ArmJoint.torso],
                                          "target": Magnebot.DEFAULT_TORSO_Y,
                                          "axis": "y"})
        self._do_arm_motion()

    def _start_ik(self, target: Dict[str, float], arm: Arm, absolute: bool = False, arrived_at: float = 0.125,
                  state: SceneState = None) -> ActionStatus:
        """
        Start an IK action.

        :param target: The target position.
        :param arm: The arm that will be bending.
        :param absolute: If True, `target` is in absolute world coordinates. If False, `target` is relative to the position and rotation of the Magnebot.
        :param arrived_at: If the magnet is this distance or less from `target`, then the action is successful.
        :param state: The scene state. If None, this uses `self.state`

        :return: An `ActionStatus` describing whether the IK action began.
        """

        def __get_ik_solution() -> Tuple[bool, List[float]]:
            """
            Get an IK solution to a target given the height of the torso.

            :return: Tuple: True if this solution will bring the end of the IK chain to the target position; the IK solution.
            """

            # Generate an IK chain, given the current desired torso height.
            chain = self.__get_ik_chain(arm=arm, torso_y=torso_y)

            # Get the IK solution.
            ik = chain.inverse_kinematics_frame(target=frame_target,
                                                initial_position=initial_angles,
                                                no_position=False)
            # Get the forward kinematics matrix of the IK solution.
            transformation_matrices = chain.forward_kinematics(ik, full_kinematics=True)
            # Convert the matrix into positions (this is pulled from ikpy).
            nodes = []
            for (index, link) in enumerate(chain.links):
                (node, orientation) = geometry.from_transformation_matrix(transformation_matrices[index])
                nodes.append(node)
            # Check if the last position on the node is very close to the target.
            # If so, this IK solution is expected to succeed.
            end_node = np.array(nodes[-1][:-1])
            d = np.linalg.norm(end_node - target)
            # Return whether the IK solution is expected to succeed; and the IK solution.
            return d <= arrived_at, ik

        # If the `state` argument is None, work off of `self.state`.
        if state is None:
            state = self.state
        target = TDWUtils.vector3_to_array(target)
        # Convert to relative coordinates.
        if absolute:
            target = self._absolute_to_relative(position=target, state=state)

        self._next_frame_commands.append({"$type": "add_position_marker",
                                          "position": TDWUtils.array_to_vector3(target)})

        # Get the initial angles of each joint.
        # The first angle is always 0 (the origin link).
        initial_angles = [0]
        for j in Magnebot.JOINT_ORDER[arm]:
            j_id = self.magnebot_static.arm_joints[j]
            initial_angles.extend(self.state.joint_angles[j_id])
        # Insert a 0 degree torso rotation.
        initial_angles.insert(2, 0)
        # Add the magnet.
        initial_angles.append(0)
        initial_angles = np.array([np.deg2rad(ia) for ia in initial_angles])

        # Get the IK solution using the current angles.
        # This is from ikpy.
        frame_target = np.eye(4)
        frame_target[:3, 3] = target

        # Try to get an IK solution from various heights.
        # Start at the default height and incrementally raise the torso.
        # We need to do this iteratively because ikpy doesn't support prismatic joints!
        # But it should be ok because there's only one prismatic joint in this robot.
        angles: List[float] = list()
        torso_y = Magnebot.DEFAULT_TORSO_Y
        got_solution = False
        while not got_solution and torso_y <= Magnebot.TORSO_LIMITS[1]:
            got_solution, angles = __get_ik_solution()
            if not got_solution:
                torso_y += 0.1
        # If we couldn't find a solution, try to lower the torso.
        if not got_solution:
            torso_y = Magnebot.DEFAULT_TORSO_Y
            while not got_solution and torso_y >= Magnebot.TORSO_LIMITS[0]:
                got_solution, angles = __get_ik_solution()
                if not got_solution:
                    torso_y -= 0.1
        # If we couldn't find a solution at any torso height, then there isn't a solution.
        if not got_solution:
            return ActionStatus.cannot_reach
        if self._debug:
            ax = matplotlib.pyplot.figure().add_subplot(111, projection='3d')
            chain = self.__get_ik_chain(arm=arm, torso_y=torso_y)
            chain.plot(angles, ax, target=target)
            matplotlib.pyplot.show()
        # Convert the angles to degrees. Remove the first node (the origin link) and last node (the magnet).
        angles = [float(np.rad2deg(a)) for a in angles[1:-1]]
        if self._debug:
            print(angles)

        # Convert the IK solution into TDW commands, using the expected joint and axis order.
        # Make the base of the Magnebot immovable because otherwise it might push itself off the ground and tip over.
        # Slide the torso to the desired height.
        commands = [{"$type": "set_immovable",
                     "immovable": True},
                    {"$type": "set_prismatic_target",
                     "joint_id": self.magnebot_static.arm_joints[ArmJoint.torso],
                     "target": torso_y,
                     "axis": "y"}]
        i = 0
        joint_order_index = 0
        while i < len(angles):
            # The second angle in the chain is the torso, which is considered a fixed joint
            # (because we're handling it iteratively). So we ignore this node in the IK solution.
            if i == 1:
                i += 1
                continue
            joint_name = Magnebot.JOINT_ORDER[arm][joint_order_index]
            joint_type = Magnebot.JOINT_AXES[joint_name]
            joint_id = self.magnebot_static.arm_joints[joint_name]
            # If this is a revolute joint, the next command includes only the next angle.
            if joint_type == JointType.revolute:
                commands.append({"$type": "set_revolute_target",
                                 "joint_id": joint_id,
                                 "target": angles[i]})
                i += 1
            # If this is a spherical joint, the next command includes the next 3 angles.
            elif joint_type == JointType.spherical:
                commands.append({"$type": "set_spherical_target",
                                 "joint_id": joint_id,
                                 "target": {"x": angles[i], "y": angles[i + 1], "z": angles[i + 2]}})
                i += 3
            else:
                raise Exception(f"Joint type not defined: {joint_type} for {joint_name}.")
            # Increment to the next joint in the order.
            joint_order_index += 1
        self._next_frame_commands.extend(commands)
        return ActionStatus.success

    def __get_reset_arm_commands(self, arm: Arm, reset_torso: bool) -> List[dict]:
        """
        :param arm: The arm to reset.
        :param reset_torso: If True, reset the torso.

        :return: A list of commands to reset the position of the arm.
        """

        commands = [{"$type": "set_immovable",
                     "immovable": True}]
        # Reset the column rotation and the torso height.
        if reset_torso:
            commands.extend([{"$type": "set_prismatic_target",
                              "joint_id": self.magnebot_static.arm_joints[ArmJoint.torso],
                              "target": Magnebot.DEFAULT_TORSO_Y,
                              "axis": "y"},
                             {"$type": "set_revolute_target",
                              "joint_id": self.magnebot_static.arm_joints[ArmJoint.column],
                              "target": 0}])
        # Reset every arm joint after the torso.
        for joint_name in Magnebot.JOINT_ORDER[arm][1:]:
            joint_id = self.magnebot_static.arm_joints[joint_name]
            joint_type = Magnebot.JOINT_AXES[joint_name]
            if joint_type == JointType.revolute:
                # Set the revolute joints to 0 except for the elbow, which should be held at a right angle.
                commands.append({"$type": "set_revolute_target",
                                 "joint_id": joint_id,
                                 "target": 0 if "elbow" not in joint_type.name else 90})
            elif joint_type == JointType.spherical:
                commands.append({"$type": "set_spherical_target",
                                 "joint_id": joint_id,
                                 "target": {"x": 0, "y": 0, "z": 0}})
            else:
                raise Exception(f"Joint type not defined: {joint_type} for {joint_name}.")
        return commands

    def _do_arm_motion(self) -> ActionStatus:
        """
        Wait until the arms have stopped moving.

        :return: An `ActionStatus` indicating if the arms stopped moving and if not, why.
        """

        state_0 = SceneState(self.communicate([]))
        # Continue the motion. Per frame, check if the movement is done.
        attempts = 0
        moving = True
        while moving and attempts < 200:
            state_1 = SceneState(self.communicate([]))
            moving = False
            for a_id in self.magnebot_static.arm_joints.values():
                if np.linalg.norm(state_0.joint_angles[a_id][0] -
                                  state_1.joint_angles[a_id][0]) > 0.001:
                    moving = True
                    break
            state_0 = state_1
            attempts += 1
        if moving:
            return ActionStatus.failed_to_bend
        else:
            return ActionStatus.success

    def _get_raycast(self, object_id: int, origin: np.array) -> Tuple[bool, np.array]:
        """
        Raycast to a target object from an origin.

        :param object_id: The object ID.

        :return: Tuple: The point of the raycast hit or the centroid of the object; and whether the raycast hit the object.
        """

        resp = self.communicate({"$type": "send_bounds",
                                 "ids": [object_id],
                                 "frequency": "once"})
        bounds = get_data(resp=resp, d_type=Bounds)
        # Raycast to the center of the bounds to get the nearest point.
        destination = TDWUtils.array_to_vector3(bounds.get_center(0))
        state = SceneState(resp=resp)
        # Add a forward directional vector.
        origin += np.array(state.magnebot_transform.forward) * 0.01
        resp = self.communicate({"$type": "send_raycast",
                                 "origin": TDWUtils.array_to_vector3(origin),
                                 "destination": destination})
        raycast = get_data(resp=resp, d_type=Raycast)
        point = np.array(raycast.get_point())
        hit = raycast.get_hit() and raycast.get_object_id() is not None and raycast.get_object_id() == object_id
        return hit, point if hit else destination

    @staticmethod
    def __get_ik_chain(arm: Arm, torso_y: float) -> Chain:
        """
        :param arm: The arm of the chain (determines the x position).
        :param torso_y: The y coordinate of the torso.

        :return: An IK chain for the arm.
        """

        return Chain(name=arm.name, links=[
            OriginLink(),
            URDFLink(name="column",
                     translation_vector=[0, 0.159, 0],
                     orientation=[0, 0, 0],
                     rotation=[0, -1, 0],
                     bounds=(np.deg2rad(-179), np.deg2rad(179))),
            URDFLink(name="torso",
                     translation_vector=[0, torso_y, 0],
                     orientation=[0, 0, 0],
                     rotation=None),
            URDFLink(name="shoulder_pitch",
                     translation_vector=[-0.215 * -1 if arm == Arm.left else 1,  0.059, 0.019],
                     orientation=[0, 0, 0],
                     rotation=[0, 0, 1],
                     bounds=(np.deg2rad(-150), np.deg2rad(70))),
            URDFLink(name="shoulder_yaw",
                     translation_vector=[0, 0, 0],
                     orientation=[0, 0, 0],
                     rotation=[1, 0, 0],
                     bounds=(np.deg2rad(-110 if arm == Arm.left else -20), np.deg2rad(20 if arm == Arm.left else 110))),
            URDFLink(name="shoulder_roll",
                     translation_vector=[0, 0, 0],
                     orientation=[0, 0, 0],
                     rotation=[0, -1, 0],
                     bounds=(np.deg2rad(-70 if arm == Arm.left else -45), np.deg2rad(45 if arm == Arm.left else 70))),
            URDFLink(name="elbow_pitch",
                     translation_vector=[0.051 * -1 if arm == Arm.left else 1, -0.29, 0.015],
                     orientation=[0, 0, 0],
                     rotation=[0, 0, 1],
                     bounds=(np.deg2rad(-90), np.deg2rad(145))),
            URDFLink(name="wrist_pitch",
                     translation_vector=[0, -0.373, 0],
                     orientation=[0, 0, 0],
                     rotation=[0, 0, 1],
                     bounds=(np.deg2rad(-90), np.deg2rad(90))),
            URDFLink(name="wrist_yaw",
                     translation_vector=[0, 0, 0],
                     orientation=[0, 0, 0],
                     rotation=[1, 0, 0],
                     bounds=(np.deg2rad(-15), np.deg2rad(15))),
            URDFLink(name="wrist_roll",
                     translation_vector=[0, 0, 0],
                     orientation=[0, 0, 0],
                     rotation=[0, -1, 0],
                     bounds=(np.deg2rad(-90), np.deg2rad(90))),
            URDFLink(name="magnet",
                     translation_vector=[0, -0.095, 0],
                     orientation=[0, 0, 0],
                     rotation=None)])

    def _cache_static_data(self, resp: List[bytes]) -> None:
        """
        Cache static data after initializing the scene.
        Sets the initial SceneState.

        :param resp: The response from the build.
        """

        # Clear static data.
        self.objects_static.clear()
        self.segmentation_color_to_id.clear()
        self._next_frame_commands.clear()
        self.camera_rpy: np.array = np.array([0, 0, 0])
        SceneState.FRAME_COUNT = 0

        # Get segmentation color data.
        segmentation_colors = get_data(resp=resp, d_type=SegmentationColors)
        names: Dict[int, str] = dict()
        colors: Dict[int, np.array] = dict()
        for i in range(segmentation_colors.get_num()):
            object_id = segmentation_colors.get_object_id(i)
            names[object_id] = segmentation_colors.get_object_name(i)
            color = segmentation_colors.get_object_color(i)
            self.segmentation_color_to_id[TDWUtils.color_to_hashable(color)] = object_id
            colors[object_id] = color
        # Get the bounds data.
        bounds = get_data(resp=resp, d_type=Bounds)
        bs: Dict[int, np.array] = dict()
        for i in range(bounds.get_num()):
            bs[bounds.get_id(i)] = np.array([float(np.abs(bounds.get_right(i)[0] - bounds.get_left(i)[0])),
                                             float(np.abs(bounds.get_top(i)[1] - bounds.get_bottom(i)[1])),
                                             float(np.abs(bounds.get_front(i)[2] - bounds.get_back(i)[2]))])
        # Get the mass and object ID from the Rigidbodies. If the object ID isn't in this, we'll ignore that object.
        # (This is very unlikely!)
        rigidbodies = get_data(resp=resp, d_type=Rigidbodies)
        # Cache the static object. data.
        for i in range(rigidbodies.get_num()):
            object_id = rigidbodies.get_id(i)
            self.objects_static[object_id] = ObjectStatic(name=names[object_id], object_id=object_id,
                                                          segmentation_color=colors[object_id], size=bs[object_id],
                                                          mass=rigidbodies.get_mass(i))
        # Cache the static robot data.
        self.magnebot_static = MagnebotStatic(static_robot=get_data(resp=resp, d_type=StaticRobot))
        self._end_action()

    @staticmethod
    def _absolute_to_relative(position: np.array, state: SceneState) -> np.array:
        """
        :param position: The position in absolute world coordinates.
        :param state: The current state.

        :return: The converted position relative to the Magnebot's position and rotation.
        """

        return TDWUtils.rotate_position_around(position=position - state.magnebot_transform.position,
                                               angle=-TDWUtils.get_angle_between(v1=Magnebot._FORWARD,
                                                                                 v2=state.magnebot_transform.forward))


