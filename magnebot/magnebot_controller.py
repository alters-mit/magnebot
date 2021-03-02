from json import loads
from typing import List, Dict, Optional, Union, Tuple
from csv import DictReader
from pathlib import Path
import numpy as np
from _tkinter import TclError
from ikpy.chain import Chain
from ikpy.link import OriginLink, URDFLink, Link
from ikpy.utils import geometry
from tdw.floorplan_controller import FloorplanController
from tdw.output_data import OutputData, Version, StaticRobot, SegmentationColors, Bounds, Rigidbodies, LogMessage,\
    Robot, TriggerCollision
from tdw.output_data import Magnebot as Mag
from tdw.tdw_utils import TDWUtils, QuaternionUtils
from tdw.object_init_data import AudioInitData
from tdw.py_impact import PyImpact, ObjectInfo
from tdw.collisions import Collisions
from tdw.release.pypi import PyPi
from magnebot.util import get_data, check_version
from magnebot.object_static import ObjectStatic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.scene_state import SceneState
from magnebot.action_status import ActionStatus
from magnebot.paths import SPAWN_POSITIONS_PATH, TORSO_Y, OCCUPANCY_MAPS_DIRECTORY, SCENE_BOUNDS_PATH, \
    TURN_CONSTANTS_PATH
from magnebot.arm import Arm
from magnebot.joint_type import JointType
from magnebot.arm_joint import ArmJoint
from magnebot.constants import MAGNEBOT_RADIUS, OCCUPANCY_CELL_SIZE
from magnebot.turn_constants import TurnConstants


class Magnebot(FloorplanController):
    """
    [TDW controller](https://github.com/threedworld-mit/tdw) for Magnebots. This high-level API supports:

    - Creating a complex interior environment
    - Directional movement
    - Turning
    - Arm articulation via inverse kinematics (IK)
    - Grasping and dropping objects
    - Image rendering
    - Scene state metadata

    Unless otherwise stated, each of these functions is an "action" that the Magnebot can do. Each action advances the simulation by at least 1 physics frame, returns an [`ActionStatus`](action_status.md), and updates the `state` field.

    ```python
    from magnebot import Magnebot

    m = Magnebot()
    # Initializes the scene.
    status = m.init_scene(scene="2a", layout=1)
    print(status) # ActionStatus.success

    # Prints the current position of the Magnebot.
    print(m.state.magnebot_transform.position)
    ```

    ***

    ## Frames

    Every action advances the simulation by 1 or more _simulation frames_. This occurs every time the `communicate()` function is called (which all actions call internally).

    Every simulation frame advances the simulation by contains `1 + n` _physics frames_. `n` is defined in the `skip_frames` parameter of the Magnebot constructor. This greatly increases the speed of the simulation.

    Unless otherwise stated, "frame" in the Magnebot API documentation always refers to a simulation frame rather than a physics frame.

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

    #### Union[Dict[str, float], int]]

    Parameters of type `Union[Dict[str, float], int]]` can be either a Vector3 or an integer (an object ID).

    #### Arm

    All parameters of type `Arm` require you to import the [Arm enum class](arm.md):

    ```python
    from magnebot import Arm

    print(Arm.left)
    ```

    ***

    """

    # Load default audio values for objects.
    _OBJECT_AUDIO = PyImpact.get_object_info()
    """:class_var
    The camera roll, pitch, yaw constraints in degrees.
    """
    CAMERA_RPY_CONSTRAINTS: List[float] = [55, 70, 85]

    # The order in which joint angles will be set.
    _JOINT_ORDER: Dict[Arm, List[ArmJoint]] = {Arm.left: [ArmJoint.column,
                                                          ArmJoint.shoulder_left,
                                                          ArmJoint.elbow_left,
                                                          ArmJoint.wrist_left],
                                               Arm.right: [ArmJoint.column,
                                                           ArmJoint.shoulder_right,
                                                           ArmJoint.elbow_right,
                                                           ArmJoint.wrist_right]}
    # The expected joint articulation per joint
    _JOINT_AXES: Dict[ArmJoint, JointType] = {ArmJoint.column: JointType.revolute,
                                              ArmJoint.shoulder_left: JointType.spherical,
                                              ArmJoint.elbow_left: JointType.revolute,
                                              ArmJoint.wrist_left: JointType.spherical,
                                              ArmJoint.shoulder_right: JointType.spherical,
                                              ArmJoint.elbow_right: JointType.revolute,
                                              ArmJoint.wrist_right: JointType.spherical}

    # The ratio of prisimatic joint y values for the torso vs. worldspace y values.
    # These aren't always an exact ratio (ok, Unity...), so they're cached here.
    _TORSO_Y: Dict[float, float] = dict()
    with TORSO_Y.open(encoding='utf-8-sig') as f:
        r = DictReader(f)
        for row in r:
            _TORSO_Y[float(row["prismatic"])] = float(row["actual"])
    # The default height of the torso.
    _DEFAULT_TORSO_Y: float = 1

    # Turn constants by angle.
    _TURN_CONSTANTS: Dict[int, TurnConstants] = dict()
    with TURN_CONSTANTS_PATH.open(encoding='utf-8-sig') as f:
        r = DictReader(f)
        for row in r:
            _TURN_CONSTANTS[int(row["angle"])] = TurnConstants(angle=int(row["angle"]),
                                                               magic_number=float(row["magic_number"]),
                                                               outer_track=float(row["outer_track"]),
                                                               front=float(row["front"]))

    # The circumference of the Magnebot.
    _MAGNEBOT_CIRCUMFERENCE: float = np.pi * 2 * MAGNEBOT_RADIUS
    # The radius of the Magnebot wheel.
    _WHEEL_RADIUS: float = 0.1
    # The circumference of the Magnebot wheel.
    _WHEEL_CIRCUMFERENCE: float = 2 * np.pi * _WHEEL_RADIUS

    def __init__(self, port: int = 1071, launch_build: bool = False, screen_width: int = 256, screen_height: int = 256,
                 debug: bool = False, auto_save_images: bool = False, images_directory: str = "images",
                 random_seed: int = None, img_is_png: bool = False, skip_frames: int = 10):
        """
        :param port: The socket port. [Read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/getting_started.md#command-line-arguments) for more information.
        :param launch_build: If True, the build will launch automatically on the default port (1071). If False, you will need to launch the build yourself (for example, from a Docker container).
        :param screen_width: The width of the screen in pixels.
        :param screen_height: The height of the screen in pixels.
        :param auto_save_images: If True, automatically save images to `images_directory` at the end of every action.
        :param images_directory: The output directory for images if `auto_save_images == True`.
        :param random_seed: The seed used for random numbers. If None, this is chosen randomly. In the Magnebot API this is used only when randomly selecting a start position for the Magnebot (see the `room` parameter of `init_scene()`). The same random seed is used in higher-level APIs such as the Transport Challenge.
        :param debug: If True, enable debug mode. This controller will output messages to the console, including any warnings or errors sent by the build. It will also create 3D plots of arm articulation IK solutions.
        :param img_is_png: If True, the `img` pass images will be .png files. If False,  the `img` pass images will be .jpg files, which are smaller; the build will run approximately 2% faster.
        :param skip_frames: The build will return output data this many physics frames per simulation frame (`communicate()` call). This will greatly speed up the simulation, but eventually there will be a noticeable loss in physics accuracy. If you want to render every frame, set this to 0.
        """

        self._debug = debug

        # Get a random seed.
        if random_seed is None:
            random_seed = self.get_unique_id()
        self._rng = np.random.RandomState(random_seed)

        """:field
        [Dynamic data for all of the most recent frame after doing an action.](scene_state.md) This includes image data, physics metadata, etc.       
        
        ```python
        from magnebot import Magnebot
        
        m = Magnebot()
        m.init_scene(scene="2a", layout=1)
        
        # Print the initial position of the Magnebot.
        print(m.state.magnebot_transform.position)
        
        m.move_by(1)
        
        # Print the new position of the Magnebot.
        print(m.state.magnebot_transform.position)
        ```
        """
        self.state: Optional[SceneState] = None

        """:field
        If True, automatically save images to `images_directory` at the end of every action.
        """
        self.auto_save_images = auto_save_images

        """:field
        The output directory for images if `auto_save_images == True`. This is a [`Path` object from `pathlib`](https://docs.python.org/3/library/pathlib.html).
        """
        self.images_directory = Path(images_directory)
        if not self.images_directory.exists():
            self.images_directory.mkdir(parents=True)
        if self.auto_save_images:
            print(f"Images will be saved to: {self.images_directory.resolve()}")

        """:field
        The current (roll, pitch, yaw) angles of the Magnebot's camera in degrees as a numpy array. This is handled outside of `self.state` because it isn't calculated using output data from the build. See: `Magnebot.CAMERA_RPY_CONSTRAINTS` and `self.rotate_camera()`
        """
        self.camera_rpy: np.array = np.array([0, 0, 0])

        """:field
        A list of objects that the Magnebot is colliding with at the end of the most recent action.
        """
        self.colliding_objects: List[int] = list()

        # Commands to initialize objects.
        self._object_init_commands: Dict[int, List[dict]] = dict()

        # Used in `step_physics` per frame.
        self._skip_frames: int = skip_frames

        """:field
        [Data for all objects in the scene that that doesn't change between frames, such as object IDs, mass, etc.](object_static.md) Key = the ID of the object..
        
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
        [Data for the Magnebot that doesn't change between frames.](magnebot_static.md)
        
        ```python
        from magnebot import Magnebot

        m = Magnebot()
        m.init_scene(scene="2a", layout=1)
        print(m.magnebot_static.magnets)
        ```
        """
        self.magnebot_static: Optional[MagnebotStatic] = None

        """:field
        A numpy array of the occupancy map. This is None until you call `init_scene()`.
        
        Shape = `(1, width, length)` where `width` and `length` are the number of cells in the grid. Each grid cell has a radius of 0.245. To convert from occupancy map `(x, y)` coordinates to worldspace `(x, z)` coordinates, see: `get_occupancy_position()`.
        
        Each element is an integer describing the occupancy at that position.
        
        | Value | Meaning |
        | --- | --- |
        | -1 | This position is outside of the scene. |
        | 0 | Unoccupied and navigable; the Magnebot can go here. |
        | 1 | This position is occupied by an object(s) or a wall. |
        | 2 | This position is free but not navigable (usually because there are objects in the way. |
        
        ```python
        from magnebot import Magnebot

        m = Magnebot(launch_build=False)
        m.init_scene(scene="1a", layout=0)
        x = 30
        y = 16
        print(m.occupancy_map[x][y]) # 0 (free and navigable position)
        print(m.get_occupancy_position(x, y)) # (1.1157886505126946, 2.2528389358520506)
        ```
        
        Images of occupancy maps can be found [here](https://github.com/alters-mit/magnebot/tree/master/doc/images/occupancy_maps). The blue squares are free navigable positions. Images are named `[scene]_[layout].jpg` For example, the occupancy map image for scene "2a" layout 0 is: `2_0.jpg`.
        
        The occupancy map is static, meaning that it won't update when objects are moved.

        Note that it is possible for the Magnebot to go to positions that aren't "free". The Magnebot's base is a rectangle that is longer on the sides than the front and back. The occupancy grid cell size is defined by the longer axis, so it is possible for the Magnebot to move forward and squeeze into a smaller space. The Magnebot can also push, lift, or otherwise move objects out of its way.
        """
        self.occupancy_map: Optional[np.array] = None

        # The scene bounds. This is used along with the occupancy map to get (x, z) worldspace positions.
        self._scene_bounds: Optional[dict] = None

        # Commands that will be sent on the next frame.
        self._next_frame_commands: List[dict] = list()

        # Send these commands every frame.
        self._per_frame_commands: List[dict] = list()

        # If True, the Magnebot is about to tip over.
        self._about_to_tip = False

        # Trigger events at the end of the most recent action.
        # Key = The trigger collider object.
        # Value = A list of trigger events that started and have continued (enter with an exit).
        self._trigger_events: Dict[int, List[int]] = dict()
        super().__init__(port=port, launch_build=launch_build)


        # Set image encoding to .png (default) or .jpg
        # Set the highest render quality.
        # Set global physics values.
        resp = self.communicate([{"$type": "set_img_pass_encoding",
                                  "value": img_is_png},
                                 {"$type": "set_render_quality",
                                  "render_quality": 5},
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
        # Make sure that the Magnebot API is up to date.
        check_version()

    def init_scene(self, scene: str, layout: int, room: int = None) -> ActionStatus:
        """
        **Always call this function before any other API calls.** Initialize a scene, populate it with objects, and add the Magnebot.

        It might take a few minutes to initialize the scene. You can call `init_scene()` more than once to reset the simulation; subsequent resets at runtime should be extremely fast.

        Set the `scene` and `layout` parameters in `init_scene()` to load an interior scene with furniture and props. Set the `room` to spawn the avatar in the center of a specific room.

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

        Images of each scene+layout combination can be found [here](https://github.com/alters-mit/magnebot/tree/master/doc/images/floorplans). Images are named `[scene]_[layout].jpg` For example, the image for scene "2a" layout 0 is: `2a_0.jpg`.

        Images of where each room in a scene is can be found [here](https://github.com/alters-mit/magnebot/tree/master/doc/images/rooms). Images are named `[scene].jpg` For example, the image for scene "2a" layout 0 is: `2.jpg`.

        Possible [return values](action_status.md):

        - `success`

        :param scene: The name of an interior floorplan scene. Each number (1, 2, etc.) has a different shape, different rooms, etc. Each letter (a, b, c) is a cosmetically distinct variant with the same floorplan.
        :param layout: The furniture layout of the floorplan. Each number (0, 1, 2) will populate the floorplan with different furniture in different positions.
        :param room: The index of the room that the Magnebot will spawn in the center of. If None, the room will be chosen randomly.

        :return: An `ActionStatus` (always success).
        """

        # Clear all data from the previous scene.
        self._clear_data()
        # Load the occupancy map.
        self.occupancy_map = np.load(str(OCCUPANCY_MAPS_DIRECTORY.joinpath(f"{scene[0]}_{layout}.npy").resolve()))
        # Get the scene bounds.
        self._scene_bounds = loads(SCENE_BOUNDS_PATH.read_text())[scene[0]]

        commands = self.get_scene_init_commands(scene=scene, layout=layout, audio=True)

        # Spawn the Magnebot in the center of a room.
        rooms = loads(SPAWN_POSITIONS_PATH.read_text())[scene[0]][str(layout)]
        room_keys = list(rooms.keys())
        if room is None:
            room = self._rng.choice(room_keys)
        else:
            room = str(room)
            assert room in room_keys, f"Invalid room: {room}; valid rooms are: {room_keys}"
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

        When turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_turn`
        - `tipping`

        :param angle: The target angle in degrees. Positive value = clockwise turn.
        :param aligned_at: If the difference between the current angle and the target angle is less than this value, then the action is successful.

        :return: An `ActionStatus` indicating if the Magnebot turned by the angle and if not, why.
        """

        if np.abs(angle) > 180:
            if angle > 0:
                angle -= 360
            else:
                angle += 360

        # Get the angle to the target.
        # The approximate number of iterations required, given the distance and speed.
        num_attempts = int((np.abs(angle) + 1) / 2)

        # If 0 attempts are required, then we're already aligned.
        if num_attempts == 0:
            return ActionStatus.success

        self._start_action()
        self._start_move_or_turn()
        attempts = 0
        if self._debug:
            print(f"turn_by: {angle}")
        wheel_state = self.state
        target_angle = angle
        delta_angle = target_angle
        while attempts < num_attempts:
            # Get the nearest turn constants.
            da = int(np.abs(delta_angle))
            if da >= 179:
                turn_constants = Magnebot._TURN_CONSTANTS[179]
            else:
                turn_constants = Magnebot._TURN_CONSTANTS[120]
                for turn_constants_angle in Magnebot._TURN_CONSTANTS:
                    if da <= turn_constants_angle:
                        turn_constants = Magnebot._TURN_CONSTANTS[turn_constants_angle]
                        break

            attempts += 1

            # Calculate the delta angler of the wheels, given the target angle of the Magnebot.
            # Source: https://answers.unity.com/questions/1120115/tank-wheels-and-treads.html
            # The distance that the Magnebot needs to travel, defined as a fraction of its circumference.
            d = (delta_angle / 360.0) * Magnebot._MAGNEBOT_CIRCUMFERENCE
            spin = (d / Magnebot._WHEEL_CIRCUMFERENCE) * 360 * turn_constants.magic_number
            # Set the direction of the wheels for the turn and send commands.
            commands = []
            if spin > 0:
                inner_track = "right"
            else:
                inner_track = "left"
            for wheel in self.magnebot_static.wheels:
                if inner_track in wheel.name:
                    wheel_spin = spin
                else:
                    wheel_spin = spin * turn_constants.outer_track
                if "front" in wheel.name:
                    wheel_spin *= turn_constants.front
                # Spin one side of the wheels forward and the other backward to effect a turn.
                if "left" in wheel.name:
                    target = wheel_state.joint_angles[self.magnebot_static.wheels[wheel]][0] + wheel_spin
                else:
                    target = wheel_state.joint_angles[self.magnebot_static.wheels[wheel]][0] - wheel_spin

                commands.append({"$type": "set_revolute_target",
                                 "target": target,
                                 "joint_id": self.magnebot_static.wheels[wheel]})
            # Wait until the wheels are done turning.
            state_0 = SceneState(resp=self.communicate(commands))
            turn_done = False
            while not turn_done:
                state_1 = SceneState(resp=self.communicate([]))
                if self._about_to_tip:
                    self._stop_tipping(state=state_1)
                    self._end_action()
                    return ActionStatus.tipping

                if not self._wheels_are_turning(state_0=state_0, state_1=state_1):
                    turn_done = True
                state_0 = state_1
            wheel_state = state_0
            # Get the change in angle from the initial rotation.
            theta = QuaternionUtils.get_y_angle(self.state.magnebot_transform.rotation,
                                                wheel_state.magnebot_transform.rotation)
            # If the angle to the target is very small, then we're done.
            if np.abs(angle - theta) < aligned_at:
                self._stop_wheels(state=wheel_state)
                self._end_action()
                if self._debug:
                    print("Turn complete!")
                return ActionStatus.success
            # Course-correct the angle.
            delta_angle = angle - theta
            # Handle cases where we flip over the axis.
            if angle + delta_angle <= -180:
                delta_angle *= -1
            if self._debug:
                print(f"angle: {angle}", f"delta_angle: {delta_angle}", f"spin: {spin}", f"d: {d}", f"theta: {theta}")
        self._stop_wheels(state=wheel_state)
        self._end_action()
        return ActionStatus.failed_to_turn

    def turn_to(self, target: Union[int, Dict[str, float]], aligned_at: float = 3) -> ActionStatus:
        """
        Turn the Magnebot to face a target object or position.

        When turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_turn`
        - `tipping`

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

        angle = TDWUtils.get_angle_between(v1=self.state.magnebot_transform.forward,
                                           v2=target - self.state.magnebot_transform.position)
        return self.turn_by(angle=angle, aligned_at=aligned_at)

    def move_by(self, distance: float, arrived_at: float = 0.3) -> ActionStatus:
        """
        Move the Magnebot forward or backward by a given distance.

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_move`
        - `collision`
        - `tipping`

        :param distance: The target distance. If less than zero, the Magnebot will move backwards.
        :param arrived_at: If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful.

        :return: An `ActionStatus` indicating if the Magnebot moved by `distance` and if not, why.
        """

        self._start_action()
        self._start_move_or_turn()

        # The initial position of the robot.
        p0 = self.state.magnebot_transform.position
        target_position = self.state.magnebot_transform.position + (self.state.magnebot_transform.forward * distance)
        d = np.linalg.norm(target_position - p0)
        d_0 = d
        # We're already here.
        if d < arrived_at:
            self._end_action()
            if self._debug:
                print(f"No movement. We're already here: {d}")
            return ActionStatus.success

        # Get the angle that we expect the wheels should turn to in order to move the Magnebot.
        spin = (distance / Magnebot._WHEEL_CIRCUMFERENCE) * 360
        # The approximately number of iterations required, given the distance and speed.
        num_attempts = int(np.abs(distance) * 10)
        attempts = 0
        if self._debug:
            print(f"move_by: {distance}")
        # The approximately number of iterations required, given the distance and speed.
        # Wait for the wheels to stop turning.
        wheel_state = SceneState(resp=self.communicate([]))
        while attempts < num_attempts:
            # We are trying to adjust the distance.
            if self._debug:
                print(f"num_attempts: {num_attempts}", f"distance: {distance}", f"spin: {spin}")
            # Move forward a bit and see if we've arrived.
            commands = []
            for wheel in self.magnebot_static.wheels:
                # Get the target from the current joint angles. Add or subtract the speed.
                target = wheel_state.joint_angles[self.magnebot_static.wheels[wheel]][0] + spin
                commands.append({"$type": "set_revolute_target",
                                 "target": target,
                                 "joint_id": self.magnebot_static.wheels[wheel]})
            # Wait for the wheels to stop turning.
            move_state_0 = SceneState(resp=self.communicate(commands))
            move_done = False
            while not move_done:
                resp = self.communicate([])
                move_state_1 = SceneState(resp=resp)

                if self._about_to_tip:
                    self._stop_tipping(state=move_state_1)
                    self._end_action()
                    return ActionStatus.tipping

                dt = np.linalg.norm(move_state_1.magnebot_transform.position - move_state_0.magnebot_transform.position)
                if dt < 0.001:
                    move_done = True
                move_state_0 = move_state_1

                # Check if we collided with the environment or with any objects.
                collisions = Collisions(resp=resp)
                for object_id in collisions.env_collisions:
                    # Ignore collisions with the floor.
                    if collisions.env_collisions[object_id].floor:
                        continue
                    if object_id in self.magnebot_static.joints:
                        self._stop_wheels(state=move_state_1)
                        if self._debug:
                            print("Collision. Stopping movement.")
                        self._end_action()
                        return ActionStatus.collision
                for id_pair in collisions.obj_collisions:
                    if collisions.obj_collisions[id_pair].state != "enter":
                        continue
                    # Listen only for collisions between a body part and a scene object.
                    if (id_pair.int1 in self.magnebot_static.joints and
                        id_pair.int2 not in self.magnebot_static.joints) or \
                            (id_pair.int1 not in self.magnebot_static.joints and
                             id_pair.int2 in self.magnebot_static.joints):
                        # Ignore very small objects.
                        if (id_pair.int1 in self.objects_static and
                            self.objects_static[id_pair.int1].mass > 8) or \
                                (id_pair.int2 in self.objects_static and
                                 self.objects_static[id_pair.int2].mass > 8):
                            self._stop_wheels(state=move_state_1)
                            if self._debug:
                                print("Collision. Stopping movement.")
                            self._end_action()
                            return ActionStatus.collision

            wheel_state = move_state_0
            # Check if we're at the destination.
            p1 = wheel_state.magnebot_transform.position
            d = np.linalg.norm(target_position - p1)

            # Arrived!
            if d < arrived_at:
                self._end_action()
                if self._debug:
                    print("Move complete!", TDWUtils.array_to_vector3(self.state.magnebot_transform.position), d)
                return ActionStatus.success
            # Go until we've traversed the distance.
            # 0.5 is a magic number.
            spin = (d / Magnebot._WHEEL_CIRCUMFERENCE) * 360 * 0.5 * (1 if distance > 0 else -1)
            d_total = np.linalg.norm(p1 - p0)
            if d_total > d_0:
                spin *= -1
            if self._debug:
                print(f"distance: {distance}", f"d: {d}", f"speed: {spin}")
            attempts += 1
        self._end_action()
        p1 = wheel_state.magnebot_transform.position
        d = np.linalg.norm(p1 - p0)
        # Arrived!
        if np.abs(np.abs(distance) - d) < arrived_at:
            return ActionStatus.success
        # Failed to arrive.
        else:
            return ActionStatus.failed_to_move

    def move_to(self, target: Union[int, Dict[str, float]], arrived_at: float = 0.3,
                aligned_at: float = 3) -> ActionStatus:
        """
        Move the Magnebot to a target object or position.

        This is a wrapper function for `turn_to()` followed by `move_by()`.

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_move`
        - `collision`
        - `failed_to_turn`
        - `tipping`

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
                # Try to stop before colliding with an object.
                distance = np.linalg.norm(self.state.magnebot_transform.position - target) - arrived_at
            elif isinstance(target, dict):
                target = TDWUtils.vector3_to_array(target)
                distance = np.linalg.norm(self.state.magnebot_transform.position - target)
            else:
                raise Exception(f"Invalid target: {target}")

            return self.move_by(distance=distance, arrived_at=arrived_at)
        else:
            self._end_action()
            return status

    def reset_position(self) -> ActionStatus:
        """
        Set the Magnebot's position from `(x, y, z)` to `(x, 0, z)`, set its rotation to the default rotation (see `tdw.tdw_utils.QuaternionUtils.IDENTITY`), and drop all held objects. The action ends when all previously-held objects stop moving.

        This will be interpreted by the physics engine as a _very_ sudden and fast movement. This action should only be called if the Magnebot is a position that will prevent the simulation from continuing (for example, if the Magnebot fell over).

        Possible [return values](action_status.md):

        - `success`

        :return: An `ActionStatus` (always success).
        """

        self._start_action()
        position = TDWUtils.array_to_vector3(self.state.magnebot_transform.position)
        position["y"] = 0
        self._next_frame_commands.extend([{"$type": "teleport_robot",
                                           "position": position},
                                          {"$type": "set_immovable",
                                           "immovable": True}])
        self._stop_tipping(state=self.state)
        self._end_action()
        return ActionStatus.success

    def reach_for(self, target: Dict[str, float], arm: Arm, absolute: bool = True, arrived_at: float = 0.125) -> ActionStatus:
        """
        Reach for a target position.

        The action ends when the arm stops moving. The arm might stop moving if it succeeded at finishing the motion, in which case the action is successful. Or, the arms might stop moving because the motion is impossible, there's an obstacle in the way, if the arm is holding something heavy, and so on.

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
        status = self._start_ik(target=target, arm=arm, absolute=absolute, arrived_at=arrived_at,
                                do_prismatic_first=target["y"] > Magnebot._TORSO_Y[Magnebot._DEFAULT_TORSO_Y])
        if status != ActionStatus.success:
            self._end_action()
            return status

        # Wait for the arm motion to end.
        self._do_arm_motion(conditional=lambda state: self._magnet_is_at_target(target=destination,
                                                                                arm=arm,
                                                                                state=state))
        self._end_action()

        # Check how close the magnet is to the expected relative position.
        magnet_position = Magnebot._absolute_to_relative(
            position=self.state.joint_positions[self.magnebot_static.magnets[arm]],
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

        If the magnet grasps the object, the arm will stop moving and the action is successful.

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
        # Enable grasping.
        self._next_frame_commands.append({"$type": "set_magnet_targets",
                                          "arm": arm.name,
                                          "targets": [target]})
        sides, resp = self._get_bounds_sides(target=target)
        state = SceneState(resp=resp)
        # Get the position of the magnet.
        magnet_position = state.joint_positions[self.magnebot_static.magnets[arm]]
        # Get the closest side to the magnet.
        closest: np.array = sides[0]
        d = np.inf
        for side in sides:
            dd = np.linalg.norm(side - magnet_position)
            if dd < d:
                closest = side
                d = dd
        target_position = TDWUtils.array_to_vector3(closest)

        if self._debug:
            self._next_frame_commands.append({"$type": "add_position_marker",
                                              "position": target_position})
        # Start the IK action.
        status = self._start_ik(target=target_position, arm=arm, absolute=True,
                                do_prismatic_first=target_position["y"] > Magnebot._TORSO_Y[Magnebot._DEFAULT_TORSO_Y])
        if status != ActionStatus.success:
            # Disable grasping.
            self._next_frame_commands.append({"$type": "set_magnet_targets",
                                              "arm": arm.name,
                                              "targets": []})
            self._end_action()
            return status

        # Wait for the arm motion to end.
        self._do_arm_motion(conditional=lambda s: Magnebot._is_grasping(target, arm, s))
        self._end_action()

        if target in self.state.held[arm]:
            return ActionStatus.success
        else:
            return ActionStatus.failed_to_grasp

    def drop(self, target: int, arm: Arm, wait_for_objects: bool = True) -> ActionStatus:
        """
        Drop an object held by a magnet.

        See [`SceneState.held`](scene_state.md) for a dictionary of held objects.

        Possible [return values](action_status.md):

        - `success`
        - `not_holding`

        :param target: The ID of the object currently held by the magnet.
        :param arm: The arm of the magnet holding the object.
        :param wait_for_objects: If True, the action will continue until the objects have finished falling. If False, the action advances the simulation by exactly 1 frame.

        :return: An `ActionStatus` indicating if the magnet at the end of the `arm` dropped the `target`.
        """

        self._start_action()

        if target not in self.state.held[arm]:
            if self._debug:
                print(f"Can't drop {target} because it isn't being held by {arm}: {self.state.held[arm]}")
            self._end_action()
            return ActionStatus.not_holding

        self._append_drop_commands(object_id=target, arm=arm)
        # Wait for the objects to finish falling.
        if wait_for_objects:
            # Wait a few frames just to let it start falling.
            for i in range(5):
                self.communicate([])
            self._wait_until_objects_stop(object_ids=[target])
        self._end_action()
        return ActionStatus.success

    def reset_arm(self, arm: Arm, reset_torso: bool = True) -> ActionStatus:
        """
        Reset an arm to its neutral position.

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_bend`

        :param arm: The arm that will be reset.
        :param reset_torso: If True, rotate and slide the torso to its neutral rotation and height.

        :return: An `ActionStatus` indicating if the arm reset and if not, why.
        """

        self._start_action()
        self._next_frame_commands.extend(self._get_reset_arm_commands(arm=arm, reset_torso=reset_torso))

        status = self._do_arm_motion()
        self._end_action()
        return status

    def rotate_camera(self, roll: float = 0, pitch: float = 0, yaw: float = 0) -> ActionStatus:
        """
        Rotate the Magnebot's camera by the (roll, pitch, yaw) axes.

        Each axis of rotation is constrained (see `Magnebot.CAMERA_RPY_CONSTRAINTS`).

        | Axis | Minimum | Maximum |
        | --- | --- | --- |
        | roll | -55 | 55 |
        | pitch | -70 | 70 |
        | yaw | -85 | 85 |

        See `self.camera_rpy` for the current (roll, pitch, yaw) angles of the camera.

        ```python
        from magnebot import Magnebot

        m = Magnebot()
        m.init_scene(scene="2a", layout=1)
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
        Reset the rotation of the Magnebot's camera to its default angles.

        ```python
        from magnebot import Magnebot

        m = Magnebot()
        m.init_scene(scene="2a", layout=1)
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

    def add_camera(self, position: Dict[str, float], roll: float = 0, pitch: float = 0, yaw: float = 0,
                   look_at: bool = True, follow: bool = False, camera_id: str = "c") -> ActionStatus:
        """
        Add a third person camera (i.e. a camera not attached to the any object) to the scene. This camera will render concurrently with the camera attached to the Magnebot and will output images at the end of every action (see [`SceneState.third_person_images`](scene_state.md)).

        This should only be sent per `init_scene()` call. When `init_scene()` is called to reset the simulation, you'll need to send `add_camera()` again too.

        Possible [return values](action_status.md):

        - `success`

        :param position: The initial position of the camera. If `follow == True`, this is relative to the Magnebot. If `follow == False`, this is in absolute worldspace coordinates.
        :param roll: The initial roll of the camera in degrees.
        :param pitch: The initial pitch of the camera in degrees.
        :param yaw: The initial yaw of the camera in degrees.
        :param look_at: If True, on every frame, the camera will rotate to look at the Magnebot.
        :param follow: If True, on every frame, the camera will follow the Magnebot, maintaining a constant relative position and rotation.
        :param camera_id: The ID of this camera.

        :return: An `ActionStatus` (always `success`).
        """

        self._next_frame_commands.extend(TDWUtils.create_avatar(avatar_id="c"))
        self._next_frame_commands.append({"$type": "set_pass_masks",
                                          "pass_masks": ["_img"],
                                          "avatar_id": camera_id})

        if follow:
            # Follow the Magnebot. `object_id` is the Magnebot's assumed ID.
            self._per_frame_commands.append({"$type": "follow_object",
                                             "avatar_id": camera_id,
                                             "position": position,
                                             "object_id": 0})
        else:
            self._next_frame_commands.append({"$type": "teleport_avatar_to",
                                              "avatar_id": camera_id,
                                              "position": position})
        # Set the initial rotation.
        for angle, axis in zip([roll, pitch, yaw], ["roll", "yaw", "pitch"]):
            self._next_frame_commands.append({"$type": "rotate_sensor_container_by",
                                              "axis": axis,
                                              "angle": angle,
                                              "avatar_id": camera_id})
        if look_at:
            self._per_frame_commands.append({"$type": "look_at",
                                             "avatar_id": camera_id})

        self._end_action()
        return ActionStatus.success

    def get_occupancy_position(self, i: int, j: int) -> Tuple[float, float]:
        """
        Converts the position `(i, j)` in the occupancy map to `(x, z)` worldspace coordinates.

        ```python
        from magnebot import Magnebot

        m = Magnebot(launch_build=False)
        m.init_scene(scene="1a", layout=0)
        x = 30
        y = 16
        print(m.occupancy_map[x][y]) # 0 (free and navigable position)
        print(m.get_occupancy_position(x, y)) # (1.1157886505126946, 2.2528389358520506)
        ```

        :param i: The i coordinate in the occupancy map.
        :param j: The j coordinate in the occupancy map.

        :return: Tuple: (x coordinate; z coordinate) of the corresponding worldspace position.
        """

        x = self._scene_bounds["x_min"] + (i * OCCUPANCY_CELL_SIZE)
        z = self._scene_bounds["z_min"] + (j * OCCUPANCY_CELL_SIZE)
        return x, z

    def get_visible_objects(self) -> List[int]:
        """
        Get all objects visible to the Magnebot in `self.state` using the id (segmentation color) image.

        :return: A list of IDs of visible objects.
        """

        colors = [c[1] for c in self.state.get_pil_images()["id"].getcolors()]
        return [o for o in self.objects_static if self.objects_static[o].segmentation_color in colors]

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
        # Add commands for this frame only.
        commands.extend(self._next_frame_commands)
        self._next_frame_commands.clear()
        # Add per-frame commands.
        commands.extend(self._per_frame_commands)
        # Skip some frames to speed up the simulation.
        commands.append({"$type": "step_physics",
                         "frames": self._skip_frames})

        if not self._debug:
            # Send the commands and get a response.
            resp = super().communicate(commands)
        else:
            resp = super().communicate(commands)
            # Print log messages.
            for i in range(len(resp) - 1):
                r_id = OutputData.get_data_type_id(resp[i])
                if r_id == "logm":
                    log_message = LogMessage(resp[i])
                    print(f"[Build]: {log_message.get_message_type()}, {log_message.get_message()}\t"
                          f"{log_message.get_object_type()}")
        # Get collisions.
        if self.magnebot_static is not None:
            collisions = Collisions(resp=resp)
            for int_pair in collisions.obj_collisions:
                # Ignore collisions unless they are with the Magnebot.
                if int_pair.int1 not in self.magnebot_static.body_parts and int_pair.int2 not in \
                        self.magnebot_static.body_parts:
                    continue
                # Ignore collisions that don't involve an object.
                if int_pair.int1 not in self.objects_static and int_pair.int2 not in self.objects_static:
                    continue
                if int_pair.int1 in self.objects_static:
                    object_id = int_pair.int1
                else:
                    object_id = int_pair.int2
                # Remove object IDs if this is an exit event.
                if collisions.obj_collisions[int_pair].state == "exit" and object_id in self.colliding_objects:
                    self.colliding_objects.remove(object_id)
                # Add object IDs if this is a new enter event.
                elif collisions.obj_collisions[int_pair].state == "enter" and object_id not in self.colliding_objects:
                    self.colliding_objects.append(object_id)
            # Get trigger events.
            trigger_enters: Dict[int, List[int]] = dict()
            trigger_stays: Dict[int, List[int]] = dict()
            for i in range(len(resp) - 1):
                r_id = OutputData.get_data_type_id(resp[i])
                if r_id == "trco":
                    trigger = TriggerCollision(resp[i])
                    trigger_id = trigger.get_collidee_id()
                    if trigger_id not in self._trigger_events:
                        self._trigger_events[trigger_id] = list()
                    collider_id = trigger.get_collider_id()
                    state = trigger.get_state()
                    # New trigger event.
                    if state == "enter" and collider_id not in self._trigger_events[trigger_id]:
                        self._trigger_events[trigger_id].append(collider_id)
                        if trigger_id not in trigger_enters:
                            trigger_enters[trigger_id] = list()
                        trigger_enters[trigger_id].append(collider_id)
                    # Ongoing trigger event.
                    else:
                        if trigger_id not in trigger_stays:
                            trigger_stays[trigger_id] = list()
                        trigger_stays[trigger_id].append(collider_id)
            temp: Dict[int, List[int]] = dict()
            # Remove any enter collisions that don't have stays.
            for trigger_id in self._trigger_events:
                if trigger_id not in trigger_stays:
                    continue
                stays: List[int] = list()
                for collider_id in self._trigger_events[trigger_id]:
                    if trigger_id in trigger_enters and collider_id in trigger_enters[trigger_id]:
                        stays.append(collider_id)
                    elif trigger_id in trigger_stays and collider_id in trigger_stays[trigger_id]:
                        stays.append(collider_id)
                temp[trigger_id] = stays
            self._trigger_events = temp

        # Check if the Magnebot is about to tip.
        r = get_data(resp=resp, d_type=Robot)
        m = get_data(resp=resp, d_type=Mag)
        if r is not None and m is not None:
            bottom = np.array(r.get_position())
            top = np.array(m.get_top())
            bottom_top_distance = np.linalg.norm(np.array([bottom[0], bottom[2]]) - np.array([top[0], top[2]]))
            self._about_to_tip = bottom_top_distance > 0.2
        return resp

    def _add_object(self, model_name: str, position: Dict[str, float] = None,
                    rotation: Dict[str, float] = None, library: str = "models_core.json",
                    scale: Dict[str, float] = None, audio: ObjectInfo = None,
                    mass: float = None) -> int:
        """
        Add an object to the scene.

        :param model_name: The name of the model.
        :param position: The position of the model.
        :param rotation: The starting rotation of the model. Can be Euler angles or a quaternion.
        :param library: The path to the records file. If left empty, the default library will be selected. See `ModelLibrarian.get_library_filenames()` and `ModelLibrarian.get_default_library()`.
        :param scale: The scale factor of the object. If None, the scale factor is (1, 1, 1)
        :param audio: Audio values for the object. If None, use default values.
        :param mass: If not None, use this mass instead of the default.

        :return: The ID of the object.
        """

        # Get the data.
        # There isn't any audio in this simulation, but we use `AudioInitData` anyway to derive physics values.
        if audio is None:
            audio = Magnebot._OBJECT_AUDIO[model_name]
        if mass is not None:
            audio.mass = mass
        init_data = AudioInitData(name=model_name, position=position, rotation=rotation, scale_factor=scale,
                                  audio=audio, library=library)
        object_id, object_commands = init_data.get_commands()
        self._object_init_commands[object_id] = object_commands
        return object_id

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

        # Save images.
        if self.auto_save_images:
            self.state.save_images(output_directory=self.images_directory)

    def _get_scene_init_commands(self, magnebot_position: Dict[str, float] = None) -> List[dict]:
        """
        :param magnebot_position: The position of the Magnebot. If none, the position is (0, 0, 0).

        :return: A list of commands that every controller needs for initializing the scene.
        """

        if magnebot_position is None:
            magnebot_position = TDWUtils.VECTOR3_ZERO

        # Destroy the previous Magnebot, if any.
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
                    {"$type": "set_pass_masks",
                     "pass_masks": ["_img", "_id", "_depth"]},
                    {"$type": "enable_image_sensor",
                     "enable": False},
                    {"$type": "set_anti_aliasing",
                     "mode": "subpixel"}]
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
                          "exit": True,
                          "collision_types": ["obj", "env"]}])
        if self._debug:
            commands.append({"$type": "send_log_messages"})
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
        # Reset the column rotation.
        self._next_frame_commands.extend([{"$type": "set_immovable",
                                           "immovable": True},
                                          {"$type": "set_prismatic_target",
                                           "joint_id": self.magnebot_static.arm_joints[ArmJoint.torso],
                                           "target": Magnebot._DEFAULT_TORSO_Y},
                                          {"$type": "set_revolute_target",
                                           "joint_id": self.magnebot_static.arm_joints[ArmJoint.column],
                                           "target": 0}])
        # Wait until these two joints stop moving.
        self._do_arm_motion(joint_ids=[self.magnebot_static.arm_joints[ArmJoint.torso],
                                       self.magnebot_static.arm_joints[ArmJoint.column]], non_moving=0.01)
        # Let the Magnebot move again.
        self._next_frame_commands.append({"$type": "set_immovable",
                                          "immovable": False})

    def _start_ik(self, target: Dict[str, float], arm: Arm, absolute: bool = True, arrived_at: float = 0.125,
                  state: SceneState = None, allow_column: bool = True, fixed_torso_prismatic: float = None,
                  object_id: int = None, do_prismatic_first: bool = False,
                  orientation_mode: str = None, target_orientation: np.array = None) -> ActionStatus:
        """
        Start an IK action.

        :param target: The target position.
        :param arm: The arm that will be bending.
        :param absolute: If True, `target` is in absolute world coordinates. If False, `target` is relative to the position and rotation of the Magnebot.
        :param arrived_at: If the magnet is this distance or less from `target`, then the action is successful.
        :param state: The scene state. If None, this uses `self.state`
        :param allow_column: If True, allow column rotation.
        :param fixed_torso_prismatic: If not None, use this value for the torso prismatic joint and don't try to change it.
        :param object_id: If not None, and if the object is held by the arm, make the object the end effector in the IK chain.
        :param do_prismatic_first: If True, do the prismatic (torso) motion first. If False, move the torso while the arm moves.
        :param orientation_mode: The IK orientation mode.
        :param target_orientation: The target IK orientation.

        :return: An `ActionStatus` describing whether the IK action began.
        """

        def __get_ik_solution() -> Tuple[bool, List[float]]:
            """
            Get an IK solution to a target given the height of the torso.

            :return: Tuple: True if this solution will bring the end of the IK chain to the target position; the IK solution.
            """

            # Generate an IK chain, given the current desired torso height.
            # The extra height is the y position of the column's base.
            chain = self.__get_ik_chain(arm=arm, torso_y=Magnebot._TORSO_Y[round(torso_prismatic, 2)],
                                        allow_column=allow_column, object_id=object_id)

            # Get the IK solution.
            ik = chain.inverse_kinematics(target_position=target,
                                          initial_position=initial_angles,
                                          orientation_mode=orientation_mode, target_orientation=target_orientation)

            if self._debug:
                # Plot the IK solution.
                # This won't always work on a remote server.
                try:
                    import matplotlib.pyplot
                    ax = matplotlib.pyplot.figure().add_subplot(111, projection='3d')
                    ax.set_xlabel("X")
                    ax.set_ylabel("Y")
                    ax.set_zlabel("Z")
                    chain.plot(ik, ax, target=target)
                    matplotlib.pyplot.show()
                except TclError as e:
                    print(f"Tried creating a debug plot of the IK solution with but got an error:\n{e}\n"
                          f"(This is probably because you're using a remote server.)")

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
        if isinstance(target, dict):
            target = TDWUtils.vector3_to_array(target)
        # Convert to relative coordinates.
        if absolute:
            target = self._absolute_to_relative(position=target, state=state)

        # Get the initial angles of each joint.
        # The first angle is always 0 (the origin link).
        initial_angles = self._get_initial_angles(arm=arm, has_object=object_id is not None)

        # Try to get an IK solution from various heights.
        # Start at the default height and incrementally raise the torso.
        # We need to do this iteratively because ikpy doesn't support prismatic joints!
        # But it should be ok because there's only one prismatic joint in this robot.
        angles: List[float] = list()
        if target[1] > Magnebot._TORSO_Y[Magnebot._DEFAULT_TORSO_Y]:
            torso_prismatic = max(Magnebot._TORSO_Y.keys())
        else:
            torso_prismatic = Magnebot._DEFAULT_TORSO_Y
        got_solution = False
        while not got_solution and torso_prismatic > 0.6:
            got_solution, angles = __get_ik_solution()
            if not got_solution:
                torso_prismatic -= 0.1
        if not got_solution:
            torso_prismatic = self._DEFAULT_TORSO_Y
            while not got_solution and torso_prismatic <= 1.5:
                    got_solution, angles = __get_ik_solution()
                    if not got_solution:
                        torso_prismatic += 0.1
        # If we couldn't find a solution at any torso height, then there isn't a solution.
        if not got_solution:
            return ActionStatus.cannot_reach

        # Convert the angles to degrees. Remove the first node (the origin link) and last node (the magnet).
        if object_id is not None:
            # Remove the object.
            angles = [float(np.rad2deg(a)) for a in angles[1:-2]]
        else:
            angles = [float(np.rad2deg(a)) for a in angles[1:-1]]

        if self._debug:
            print(angles)

        # Make the base of the Magnebot immovable because otherwise it might push itself off the ground and tip over.
        # Do this now, rather than in the `commands` list, to prevent a slide during arm movement.
        self.communicate({"$type": "set_immovable",
                          "immovable": True})

        if fixed_torso_prismatic is not None:
            torso_prismatic = fixed_torso_prismatic
        # Slide the torso to the desired height.
        torso_id = self.magnebot_static.arm_joints[ArmJoint.torso]
        torso_command = {"$type": "set_prismatic_target",
                         "joint_id": torso_id,
                         "target": torso_prismatic}
        if do_prismatic_first:
            self.communicate(torso_command)
            self._do_arm_motion(joint_ids=[torso_id])

        # Convert the IK solution into TDW commands, using the expected joint and axis order.
        self._append_ik_commands(angles=angles, arm=arm)
        if not do_prismatic_first:
            self._next_frame_commands.append(torso_command)
        return ActionStatus.success

    def _get_initial_angles(self, arm: Arm, has_object: bool = False) -> np.array:
        """
        :param arm: The arm.
        :param has_object: If True, there is an object in the joint chain.

        :return: The angles of the arm in the current state.
        """

        # Get the initial angles of each joint.
        # The first angle is always 0 (the origin link).
        initial_angles = [0]
        for j in Magnebot._JOINT_ORDER[arm]:
            j_id = self.magnebot_static.arm_joints[j]
            initial_angles.extend(self.state.joint_angles[j_id])
        # Add the magnet.
        initial_angles.append(0)
        # Add the object.
        if has_object:
            initial_angles.append(0)
        return np.radians(initial_angles)

    def _append_ik_commands(self, angles: np.array, arm: Arm) -> None:
        """
        Convert target angles to TDW commands and append them to `_next_frame_commands`.

        :param angles: The target angles in degrees.
        :param arm: The arm.
        """

        # Convert the IK solution into TDW commands, using the expected joint and axis order.
        commands = []
        i = 0
        joint_order_index = 0
        while i < len(angles):
            joint_name = Magnebot._JOINT_ORDER[arm][joint_order_index]
            joint_type = Magnebot._JOINT_AXES[joint_name]
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

    def _get_reset_arm_commands(self, arm: Arm, reset_torso: bool) -> List[dict]:
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
                              "target": Magnebot._DEFAULT_TORSO_Y},
                             {"$type": "set_revolute_target",
                              "joint_id": self.magnebot_static.arm_joints[ArmJoint.column],
                              "target": 0}])
        # Reset every arm joint after the torso.
        for joint_name in Magnebot._JOINT_ORDER[arm][1:]:
            joint_id = self.magnebot_static.arm_joints[joint_name]
            joint_type = Magnebot._JOINT_AXES[joint_name]
            if joint_type == JointType.revolute:
                # Set the revolute joints to 0 except for the elbow, which should be held at a right angle.
                commands.append({"$type": "set_revolute_target",
                                 "joint_id": joint_id,
                                 "target": 0 if "elbow" not in joint_name.name else 90})
            elif joint_type == JointType.spherical:
                commands.append({"$type": "set_spherical_target",
                                 "joint_id": joint_id,
                                 "target": {"x": 0, "y": 0, "z": 0}})
            else:
                raise Exception(f"Joint type not defined: {joint_type} for {joint_name}.")
        return commands

    def _do_arm_motion(self, conditional=None, joint_ids: List[int] = None, non_moving: float = 0.001) -> ActionStatus:
        """
        Wait until the arms have stopped moving.

        :param conditional: a conditional function (returns bool) that can stop the arm motion and has a SceneState parameter.
        :param joint_ids: The joint IDs to listen for. If None, listen for all joint IDs.
        :param non_moving: If a joint has less than this many angles since the last frame, we consider it to be non-moving.

        :return: An `ActionStatus` indicating if the arms stopped moving and if not, why.
        """

        state_0 = SceneState(self.communicate([]))
        if joint_ids is None:
            joint_ids = self.magnebot_static.arm_joints.values()
        # Continue the motion. Per frame, check if the movement is done.
        attempts = 0
        moving = True
        while moving and attempts < 200:
            state_1 = SceneState(self.communicate([]))
            # Check if the action should stop here because of a conditional. If so, stop arm motion.
            if conditional is not None and conditional(state_1):
                moving = False
                state_0 = state_1
                break

            moving = False
            for a_id in joint_ids:
                for i in range(len(state_0.joint_angles[a_id])):
                    if np.linalg.norm(state_0.joint_angles[a_id][i] -
                                      state_1.joint_angles[a_id][i]) > non_moving:
                        moving = True
                        break
            state_0 = state_1
            attempts += 1
        self._stop_joints(state=state_0, joint_ids=joint_ids)
        if moving:
            return ActionStatus.failed_to_bend
        else:
            return ActionStatus.success

    @staticmethod
    def _is_grasping(target: int, arm: Arm, state: SceneState) -> bool:
        """
        :param target: The object ID.
        :param arm: The arm.
        :param state: The SceneState.

        :return: True if the arm is holding the object in this scene state.
        """

        return target in state.held[arm]

    def __get_ik_chain(self, arm: Arm, torso_y: float, object_id: int = None, allow_column: bool = True) -> Chain:
        """
        :param arm: The arm of the chain (determines the x position).
        :param torso_y: The y coordinate of the torso.
        :param object_id: If not None, append this object to the IK chain.
        :param allow_column: If True, allow column rotation.

        :return: An IK chain for the arm.
        """

        links: List[Link] = [OriginLink()]
        if allow_column:
            links.append(URDFLink(name="column",
                                  translation_vector=[0, torso_y, 0],
                                  orientation=[0, 0, 0],
                                  rotation=[0, 1, 0],
                                  bounds=(np.deg2rad(-179), np.deg2rad(179))))
        else:
            links.append(URDFLink(name="column",
                                  translation_vector=[0, torso_y, 0],
                                  orientation=[0, 0, 0],
                                  rotation=None))
        links.extend([URDFLink(name="shoulder_pitch",
                               translation_vector=[0.215 * (-1 if arm == Arm.left else 1), 0.059, 0.019],
                               orientation=[0, 0, 0],
                               rotation=[1, 0, 0],
                               bounds=(np.deg2rad(-150), np.deg2rad(70))),
                      URDFLink(name="shoulder_roll",
                               translation_vector=[0, 0, 0],
                               orientation=[0, 0, 0],
                               rotation=[0, 1, 0],
                               bounds=(np.deg2rad(-70 if arm == Arm.left else -45),
                                       np.deg2rad(45 if arm == Arm.left else 70))),
                      URDFLink(name="shoulder_yaw",
                               translation_vector=[0, 0, 0],
                               orientation=[0, 0, 0],
                               rotation=[0, 0, 1],
                               bounds=(np.deg2rad(-110 if arm == Arm.left else -20),
                                       np.deg2rad(20 if arm == Arm.left else 110))),
                      URDFLink(name="elbow_pitch",
                               translation_vector=[0.033 * (-1 if arm == Arm.left else 1), -0.33, 0],
                               orientation=[0, 0, 0],
                               rotation=[-1, 0, 0],
                               bounds=(np.deg2rad(-90), np.deg2rad(145))),
                      URDFLink(name="wrist_pitch",
                               translation_vector=[0, -0.373, 0],
                               orientation=[0, 0, 0],
                               rotation=[-1, 0, 0],
                               bounds=(np.deg2rad(-90), np.deg2rad(90))),
                      URDFLink(name="wrist_roll",
                               translation_vector=[0, 0, 0],
                               orientation=[0, 0, 0],
                               rotation=[0, -1, 0],
                               bounds=(np.deg2rad(-90), np.deg2rad(90))),
                      URDFLink(name="wrist_yaw",
                               translation_vector=[0, 0, 0],
                               orientation=[0, 0, 0],
                               rotation=[0, 0, 1],
                               bounds=(np.deg2rad(-15), np.deg2rad(15))),
                      URDFLink(name="magnet",
                               translation_vector=[0, -0.095, 0],
                               orientation=[0, 0, 0],
                               rotation=None)])
        # Add the object.
        if object_id is not None:
            # Get the center of the object.
            resp = self.communicate({"$type": "send_bounds",
                                     "ids": [int(object_id)]})
            obj_position = np.array(get_data(resp=resp, d_type=Bounds).get_center(0))
            # Get the position of the magnet.
            state = SceneState(resp=resp)
            magnet = state.joint_positions[self.magnebot_static.magnets[arm]]
            translation_vector = magnet - obj_position
            # Add the object as an IK link.
            links.append(URDFLink(name="obj",
                                  translation_vector=translation_vector,
                                  orientation=[0, 0, 0],
                                  rotation=None))

        return Chain(name=arm.name, links=links)

    def _cache_static_data(self, resp: List[bytes]) -> None:
        """
        Cache static data after initializing the scene.
        Sets the initial SceneState.

        :param resp: The response from the build.
        """

        SceneState.FRAME_COUNT = 0

        # Get segmentation color data.
        segmentation_colors = get_data(resp=resp, d_type=SegmentationColors)
        names: Dict[int, str] = dict()
        colors: Dict[int, np.array] = dict()
        for i in range(segmentation_colors.get_num()):
            object_id = segmentation_colors.get_object_id(i)
            names[object_id] = segmentation_colors.get_object_name(i)
            color = segmentation_colors.get_object_color(i)
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

        # Parent the avatar camera to the torso.
        # We do this here rather then at the first frame because we need the ID of the torso.
        self._next_frame_commands.append({"$type": "parent_avatar_to_robot",
                                          "position": {"x": 0, "y": 0.053, "z": 0.1838},
                                          "body_part_id": self.magnebot_static.arm_joints[ArmJoint.torso]})

    def _append_drop_commands(self, object_id: int, arm: Arm) -> None:
        """
        Append commands to drop an object to `_next_frame_commands`
        :param object_id: The ID of the object.
        :param arm: The arm holding the object.
        """

        # Drop the object.
        self._next_frame_commands.append({"$type": "detach_from_magnet",
                                          "arm": arm.name,
                                          "object_id": int(object_id)})

    def _wait_until_objects_stop(self, object_ids: List[int], state: SceneState = None) -> bool:
        """
        Wait until all objects in the list stop moving.

        :param object_ids: A list of object IDs.
        :param state: The state to use. If None, use `self.state`

        :return: True if the objects stopped moving after 200 frames and they're all above floor level.
        """

        if state is None:
            state_0 = self.state
        else:
            state_0 = state
        moving = True
        # Set a maximum number of frames to prevent an infinite loop.
        num_frames = 0
        # Wait for the object to stop moving.
        while moving and num_frames < 200:
            moving = False
            state_1 = SceneState(resp=self.communicate([]))
            for object_id in object_ids:
                # Stop if the object somehow fell below the floor.
                if state_1.object_transforms[object_id].position[1] < -1:
                    return False
                if np.linalg.norm(state_0.object_transforms[object_id].position -
                                  state_1.object_transforms[object_id].position) > 0.01:
                    moving = True
                num_frames += 1
                state_0 = state_1
        return not moving

    @staticmethod
    def _absolute_to_relative(position: np.array, state: SceneState) -> np.array:
        """
        :param position: The position in absolute world coordinates.
        :param state: The current state.

        :return: The converted position relative to the Magnebot's position and rotation.
        """

        return QuaternionUtils.world_to_local_vector(position=position,
                                                     origin=state.magnebot_transform.position,
                                                     rotation=state.magnebot_transform.rotation)

    def _magnet_is_at_target(self, target: np.array, arm: Arm, state: SceneState) -> bool:
        """
        :param target: The target position.
        :param arm: The arm.
        :param state: The state.

        :return: True if the magnet is at the target position.
        """

        magnet_position = Magnebot._absolute_to_relative(
            position=state.joint_positions[self.magnebot_static.magnets[arm]],
            state=state)
        return np.linalg.norm(magnet_position - target) < 0.001

    def _stop_wheels(self, state: SceneState) -> None:
        """
        Stop wheel movement.

        :param state: The current state.
        """
        commands = []
        for wheel in self.magnebot_static.wheels:
            # Set the target of each wheel to its current position.
            commands.append({"$type": "set_revolute_target",
                             "target": float(state.joint_angles[
                                                 self.magnebot_static.wheels[wheel]][0]),
                             "joint_id": self.magnebot_static.wheels[wheel]})
        self._next_frame_commands.extend(commands)

    def _stop_tipping(self, state: SceneState) -> None:
        """
        Handle situations where the Magnebot is tipping by dropping all heavy objects.

        :param state: The current state.
        """

        if self._debug:
            print("About to tip over. Stopping.")
        held_objects: List[int] = list()
        for arm in state.held:
            for held_object in state.held[arm]:
                if self.objects_static[held_object].mass > 8:
                    self._append_drop_commands(object_id=held_object, arm=arm)
                    held_objects.append(held_object)
        # Stop the wheels.
        self._stop_wheels(state=state)
        # Wait for the objects to stop moving.
        self._wait_until_objects_stop(object_ids=held_objects)

    def _get_bounds_sides(self, target: int) -> Tuple[List[np.array], List[bytes]]:
        """
        :param target: The ID of the target object.

        :return: Tuple: Sides on the bounds of the object that can be used for an action; the response from the build.
        """

        # Reach for the center of the object.
        resp = self.communicate([{"$type": "send_bounds",
                                  "ids": [target],
                                  "frequency": "once"}])
        # Get the side on the bounds closet to the magnet.
        bounds = get_data(resp=resp, d_type=Bounds)
        sides = [bounds.get_left(0), bounds.get_right(0), bounds.get_front(0), bounds.get_back(0),
                 bounds.get_top(0), bounds.get_bottom(0)]
        return [np.array(s) for s in sides], resp

    def _wheels_are_turning(self, state_0: SceneState, state_1: SceneState) -> bool:
        """
        :param state_0: The previous scene state.
        :param state_1: The current scene state.

        :return: True if the wheels are done turning.
        """

        for w_id in self.magnebot_static.wheels.values():
            if np.linalg.norm(state_0.joint_angles[w_id][0] -
                              state_1.joint_angles[w_id][0]) > 0.1:
                return True
        return False

    def _clear_data(self) -> None:
        """
        Clear persistent simulation data from the previous simulation.
        """

        self.objects_static.clear()
        self.colliding_objects.clear()
        self.camera_rpy: np.array = np.array([0, 0, 0])
        self._next_frame_commands.clear()
        self._trigger_events.clear()
        self._per_frame_commands.clear()
        self._object_init_commands.clear()
        self._about_to_tip = False

    def _stop_joints(self, state: SceneState, joint_ids: List[int] = None) -> None:
        """
        Set the target angle of joints to their current angle.

        :param state: The SceneState.
        :param joint_ids: The joints to stop. If empty, stop all arm joints.
        """

        if joint_ids is None:
            joint_ids = self.magnebot_static.arm_joints.values()

        for joint_id in joint_ids:
            joint_angles = state.joint_angles[joint_id]
            arm_joint = ArmJoint[self.magnebot_static.joints[joint_id].name]
            # Ignore the prismatic joint.
            if self.magnebot_static.joints[joint_id].name == "torso":
                continue
            joint_axis = Magnebot._JOINT_AXES[arm_joint]
            # Set the arm joints to their current positions.
            if joint_axis == JointType.revolute:
                self._next_frame_commands.append({"$type": "set_revolute_target",
                                                  "joint_id": joint_id,
                                                  "target": float(joint_angles[0])})
            elif joint_axis == JointType.spherical:
                self._next_frame_commands.append({"$type": "set_spherical_target",
                                                  "joint_id": joint_id,
                                                  "target": TDWUtils.array_to_vector3(joint_angles)})
