from pkg_resources import resource_filename
from json import loads
from typing import List, Dict, Optional, Union, Tuple
from csv import DictReader
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from _tkinter import TclError
from ikpy.chain import Chain
from magnebot.ikpy.link import OriginLink, URDFLink, Link
from ikpy.utils import geometry
from overrides import final
from tdw.controller import Controller
from tdw.output_data import OutputData, Version, StaticRobot, SegmentationColors, Bounds, Rigidbodies, LogMessage,\
    Robot, TriggerCollision, Raycast, MagnebotWheels
from tdw.output_data import Magnebot as Mag
from tdw.tdw_utils import TDWUtils, QuaternionUtils
from tdw.object_init_data import AudioInitData
from tdw.py_impact import PyImpact, ObjectInfo
from tdw.collisions import Collisions
from tdw.release.pypi import PyPi
from tdw.scene.scene_bounds import SceneBounds
from magnebot.util import get_data, check_version
from magnebot.object_static import ObjectStatic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.scene_state import SceneState
from magnebot.action_status import ActionStatus
from magnebot.paths import SPAWN_POSITIONS_PATH, OCCUPANCY_MAPS_DIRECTORY, TURN_CONSTANTS_PATH,\
    IK_ORIENTATIONS_LEFT_PATH, IK_ORIENTATIONS_RIGHT_PATH, IK_POSITIONS_PATH
from magnebot.arm import Arm
from magnebot.joint_type import JointType
from magnebot.arm_joint import ArmJoint
from magnebot.constants import MAGNEBOT_RADIUS, OCCUPANCY_CELL_SIZE
from magnebot.turn_constants import TurnConstants
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.ik.orientation_mode import OrientationMode
from magnebot.ik.orientation import Orientation, ORIENTATIONS
from magnebot.collision_action import CollisionAction
from magnebot.collision_detection import CollisionDetection


class Magnebot(Controller):
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
    status = m.init_floorplan_scene(scene="2a", layout=1)
    print(status) # ActionStatus.success

    # Prints the current position of the Magnebot.
    print(m.state.magnebot_transform.position)
    ```

    [TOC]

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
    # Collision detection settings if `stop_on_collision == True`.
    _COLLISION_ON: CollisionDetection = CollisionDetection()
    # Collision detection settings if `stop_on_collision == False`.
    _COLLISION_OFF: CollisionDetection = CollisionDetection(walls=False, objects=False, previous_was_same=False)

    # The y value of the column's position assuming a level floor and angle.
    _COLUMN_Y: float = 0.159
    # The minimum y value of the torso, offset from the column (see `COLUMN_Y`).
    _TORSO_MIN_Y: float = 0.2244872
    # The maximum y value of the torso, offset from the column (see `COLUMN_Y`).
    _TORSO_MAX_Y: float = 1.07721
    # The default torso position.
    _DEFAULT_TORSO_Y: float = 0.737074
    # The angle at which to start braking at while turning.
    _BRAKE_ANGLE: float = 0.5
    # The wheel friction coefficient when braking during a move action.
    _BRAKE_FRICTION: float = 0.95
    # The distance at which to start braking while moving.
    _BRAKE_DISTANCE: float = 0.1
    # The default wheel friction coefficient.
    _DEFAULT_WHEEL_FRICTION: float = 0.05

    # The order in which joint angles will be set.
    _JOINT_ORDER: Dict[Arm, List[ArmJoint]] = {Arm.left: [ArmJoint.column,
                                                          ArmJoint.torso,
                                                          ArmJoint.shoulder_left,
                                                          ArmJoint.elbow_left,
                                                          ArmJoint.wrist_left],
                                               Arm.right: [ArmJoint.column,
                                                           ArmJoint.torso,
                                                           ArmJoint.shoulder_right,
                                                           ArmJoint.elbow_right,
                                                           ArmJoint.wrist_right]}
    # The expected joint articulation per joint
    _JOINT_AXES: Dict[ArmJoint, JointType] = {ArmJoint.column: JointType.revolute,
                                              ArmJoint.torso: JointType.prismatic,
                                              ArmJoint.shoulder_left: JointType.spherical,
                                              ArmJoint.elbow_left: JointType.revolute,
                                              ArmJoint.wrist_left: JointType.spherical,
                                              ArmJoint.shoulder_right: JointType.spherical,
                                              ArmJoint.elbow_right: JointType.revolute,
                                              ArmJoint.wrist_right: JointType.spherical}
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
                 random_seed: int = None, img_is_png: bool = False, skip_frames: int = 10,
                 check_pypi_version: bool = True):
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
        :param check_pypi_version: If True, compare the locally installed version of TDW and Magnebot to the most recent versions on PyPi.
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
        m.init_floorplan_scene(scene="2a", layout=1)
        
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
        A list of objects that the Magnebot is currently colliding with.
        """
        self.colliding_objects: List[int] = list()
        """:field
        If True, the Magnebot is currently colliding with a wall.
        """
        self.colliding_with_wall: bool = False

        # A [`CollisionAction`](collision_action.md) value describing a collision from the previous action.
        # If the Magnebot tries to do the corresponding action again, the action will immediately fail.
        # For example, if `self.previous_collision == CollisionAction.move_positive` and Magnebot tries `move_by(1)`,
        # the action immediately fails because the previous `move_by()` had a positive value and ended in a collision.
        self._previous_collision: CollisionAction = CollisionAction.none

        # Commands to initialize objects.
        self._object_init_commands: Dict[int, List[dict]] = dict()

        # Used in `step_physics` per frame.
        self._skip_frames: int = skip_frames

        """:field
        [Data for all objects in the scene that that doesn't change between frames, such as object IDs, mass, etc.](object_static.md) Key = the ID of the object..
        
        ```python
        from magnebot import Magnebot
        
        m = Magnebot()
        m.init_floorplan_scene(scene="2a", layout=1)
        
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
        m.init_floorplan_scene(scene="2a", layout=1)
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
        m.init_floorplan_scene(scene="1a", layout=0)
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
        self._scene_bounds: Optional[SceneBounds] = None

        # Commands that will be sent on the next frame.
        self._next_frame_commands: List[dict] = list()

        # Send these commands every frame.
        self._per_frame_commands: List[dict] = list()

        # If True, the Magnebot is about to tip over.
        self._about_to_tip = False

        # If True, the previous action was a move or a turn.
        # This way, we don't waste time resetting the torso and column.
        self._previous_action_was_move: bool = False

        # Current collision detection settings.
        self._collision_detection: CollisionDetection = Magnebot._COLLISION_ON

        # Positions relative to the Magnebot with pre-calulated IK orientation solutions.
        self._ik_positions: np.array = np.load(str(IK_POSITIONS_PATH.resolve()))
        # The orientations in the cloud of IK targets. Each orientation corresponds to a position in self._ik_positions.
        self._ik_orientations: Dict[Arm, np.array] = dict()
        for arm, ik_path in zip([Arm.left, Arm.right], [IK_ORIENTATIONS_LEFT_PATH, IK_ORIENTATIONS_RIGHT_PATH]):
            if not ik_path.exists():
                continue
            self._ik_orientations[arm] = np.load(str(ik_path.resolve()))

        # Trigger events at the end of the most recent action.
        # Key = The trigger collider object.
        # Value = A list of trigger events that started and have continued (enter with an exit).
        self._trigger_events: Dict[int, List[int]] = dict()
        super().__init__(port=port, launch_build=launch_build, check_version=check_pypi_version)
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
        if check_pypi_version:
            check_version()

    def init_scene(self) -> ActionStatus:
        """
        Initialize the Magnebot in an empty test room.

        ```python
        from magnebot import Magnebot

        m = Magnebot()
        m.init_scene()

        # Your code here.
        ```

        :return: An `ActionStatus` (always `success`).
        """

        return self._init_scene(scene=[{"$type": "load_scene", "scene_name": "ProcGenScene"},
                                       TDWUtils.create_empty_room(12, 12)])

    def init_floorplan_scene(self, scene: str, layout: int, room: int = None) -> ActionStatus:
        """
        Initialize a scene, populate it with objects, and add the Magnebot.

        It might take a few minutes to initialize the scene. You can call `init_scene()` more than once to reset the simulation; subsequent resets at runtime should be extremely fast.

        Set the `scene` and `layout` parameters in `init_scene()` to load an interior scene with furniture and props. Set the `room` to spawn the avatar in the center of a specific room.

        ```python
        from magnebot import Magnebot

        m = Magnebot()
        m.init_floorplan_scene(scene="2b", layout=0, room=1)

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

        # Get the scene command.
        scene_commands = [self.get_add_scene(scene_name=f"floorplan_{scene}")]

        # Get object initialization commands from the floorplan layout file.
        floorplans = loads(Path(resource_filename("tdw", "floorplan_layouts.json")).
                           read_text(encoding="utf-8"))
        scene_index = scene[0]
        layout = str(layout)
        if scene_index not in floorplans:
            raise Exception(f"Floorplan not found: {scene_index}")
        if layout not in floorplans[scene_index]:
            raise Exception(f"Layout not found: {layout}")
        object_data = [AudioInitData(**o) for o in floorplans[scene_index][layout]]
        for o in object_data:
            o_id, o_commands = o.get_commands()
            self._object_init_commands[o_id] = o_commands

        # Get the spawn position of the Magnebot.
        rooms = loads(SPAWN_POSITIONS_PATH.read_text())[scene[0]][layout]
        room_keys = list(rooms.keys())
        if room is None:
            room = self._rng.choice(room_keys)
        else:
            room = str(room)
            assert room in room_keys, f"Invalid room: {room}; valid rooms are: {room_keys}"
        magnebot_position: Dict[str, float] = rooms[room]

        # Load the occupancy map.
        self.occupancy_map = np.load(str(OCCUPANCY_MAPS_DIRECTORY.joinpath(f"{scene[0]}_{layout}.npy").resolve()))
        # Initialize the scene.
        return self._init_scene(scene=scene_commands,
                                post_processing=self._get_post_processing_commands(),
                                magnebot_position=magnebot_position)

    def turn_by(self, angle: float, aligned_at: float = 1, stop_on_collision: Union[bool, CollisionDetection] = True,
                target_position: Dict[str, float] = None) -> ActionStatus:
        """
        Turn the Magnebot by an angle.

        When turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_turn`
        - `tipping`
        - `collision`

        :param angle: The target angle in degrees. Positive value = clockwise turn.
        :param aligned_at: If the difference between the current angle and the target angle is less than this value, then the action is successful.
        :param stop_on_collision: If True, if the Magnebot will stop when it detects certain collisions. If False, ignore collisions. This can also be a [`CollisionDetection`](collision_detection.md) object. [Read this](../movement.md) for more information.
        :param target_position:  This parameter is used internally by the `turn_to()` action. Do not set this parameter to anything other than None (the default).

        :return: An `ActionStatus` indicating if the Magnebot turned by the angle and if not, why.
        """

        def __set_collision_action(collision: bool) -> None:
            """
            If there was a collision, record the collision state.

            :param collision: If True, there was a collision.
            """

            if not collision:
                self._previous_collision = CollisionAction.none
            elif angle > 0:
                self._previous_collision = CollisionAction.turn_positive
            else:
                self._previous_collision = CollisionAction.turn_negative

        # Set the current collision state.
        if isinstance(stop_on_collision, bool):
            if stop_on_collision:
                self._collision_detection = Magnebot._COLLISION_ON
            else:
                self._collision_detection = Magnebot._COLLISION_OFF
        elif isinstance(stop_on_collision, CollisionDetection):
            self._collision_detection = stop_on_collision
        else:
            raise Exception("Invalid object type for stop_on_collision.")
        # Don't try to collide with the same thing twice.
        if self._collision_detection.previous_was_same and \
                ((angle > 0 and self._previous_collision == CollisionAction.turn_positive) or
                 (angle < 0 and self._previous_collision == CollisionAction.turn_negative)):
            __set_collision_action(True)
            return ActionStatus.collision

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
            __set_collision_action(False)
            return ActionStatus.success
        self._start_action()
        self._start_move_or_turn()
        attempts = 0
        if self._debug:
            print(f"turn_by: {angle}")
        wheel_state = self.state
        delta_angle = angle
        previous_delta_angle = angle
        for_0 = TDWUtils.array_to_vector3(self.state.magnebot_transform.forward)
        minimum_friction = Magnebot._DEFAULT_WHEEL_FRICTION
        while attempts < num_attempts:
            if delta_angle < 9.25:
                self._set_brake_wheel_drives()
                minimum_friction = Magnebot._BRAKE_FRICTION
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
            turn_frames = 0
            while not turn_done and turn_frames < 2000:
                if aligned_at <= 1:
                    # Turn by an angle.
                    if target_position is None:
                        resp = self.communicate([{"$type": "set_magnebot_wheels_during_turn_by",
                                                  "angle": angle,
                                                  "origin": for_0,
                                                  "arrived_at": aligned_at,
                                                  "minimum_friction": minimum_friction,
                                                  "brake_angle": Magnebot._BRAKE_ANGLE}])
                    # Check the alignment to the target position.
                    else:
                        resp = self.communicate([{"$type": "set_magnebot_wheels_during_turn_to",
                                                  "angle": angle,
                                                  "origin": for_0,
                                                  "arrived_at": aligned_at,
                                                  "position": target_position,
                                                  "minimum_friction": minimum_friction,
                                                  "brake_angle": Magnebot._BRAKE_ANGLE}])
                else:
                    resp = self.communicate([])
                state_1 = SceneState(resp=resp)
                # If the Magnebot is about to tip over, stop the action and try to correct the tip.
                # Mark this is as a collision so the Magnebot can't do the same action again.
                if self._about_to_tip:
                    self._stop_tipping(state=state_1)
                    self._end_action(previous_action_was_move=True)
                    __set_collision_action(True)
                    return ActionStatus.tipping
                # Check if we collided with the environment or with any objects.
                elif self._collided():
                    self._stop_wheels(state=state_1)
                    if self._debug:
                        print("Collision. Stopping movement.")
                    self._end_action(previous_action_was_move=True)
                    __set_collision_action(True)
                    return ActionStatus.collision
                if not self._wheels_are_turning(state_0=state_0, state_1=state_1):
                    turn_done = True
                # If the build announced that the turn is done, stop here.
                for i in range(len(resp) - 1):
                    r_id = OutputData.get_data_type_id(resp[i])
                    if r_id == "mwhe":
                        mwhe = MagnebotWheels(resp[i])
                        if mwhe.get_success():
                            self._stop_wheels(state=wheel_state)
                            self._end_action(previous_action_was_move=True)
                            __set_collision_action(False)
                            return ActionStatus.success
                        # Overshot the target.
                        else:
                            turn_done = True
                turn_frames += 1
                state_0 = state_1
            wheel_state = state_0
            # If the turn took too long, assume there was a collision.
            if not turn_done:
                self._stop_wheels(state=wheel_state)
                if self._debug:
                    print("Couldn't complete turn! Stopping movement.")
                self._end_action(previous_action_was_move=True)
                __set_collision_action(True)
                return ActionStatus.collision
            # Get the change in angle from the initial rotation.
            theta = QuaternionUtils.get_y_angle(self.state.magnebot_transform.rotation,
                                                wheel_state.magnebot_transform.rotation)
            # If the angle to the target is very small, then we're done.
            if np.abs(angle - theta) < aligned_at:
                self._stop_wheels(state=wheel_state)
                self._end_action(previous_action_was_move=True)
                __set_collision_action(False)
                if self._debug:
                    print("Turn complete!")
                return ActionStatus.success
            # Course-correct the angle.
            delta_angle = angle - theta
            # Handle cases where we flip over the axis.
            if np.abs(previous_delta_angle) < np.abs(delta_angle):
                if self._debug:
                    print(f"Overshot! Flipping delta_theta.")
                delta_angle *= -1
            previous_delta_angle = delta_angle
            if self._debug:
                print(f"angle: {angle}", f"delta_angle: {delta_angle}", f"theta: {theta}")
        self._stop_wheels(state=wheel_state)
        self._end_action(previous_action_was_move=True)
        # If the Magenbot failed to turn, mark this as a collision (even if it wasn't)
        # so the Magnebot can't choose the same action and direction again.
        __set_collision_action(True)
        return ActionStatus.failed_to_turn

    def turn_to(self, target: Union[int, Dict[str, float]], aligned_at: float = 1, stop_on_collision: Union[bool, CollisionDetection] = True) -> ActionStatus:
        """
        Turn the Magnebot to face a target object or position.

        When turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_turn`
        - `tipping`
        - `collision`

        :param target: Either the ID of an object or a Vector3 position.
        :param aligned_at: If the different between the current angle and the target angle is less than this value, then the action is successful.
        :param stop_on_collision: If True, if the Magnebot will stop when it detects certain collisions. If False, ignore collisions. This can also be a [`CollisionDetection`](collision_detection.md) object. [Read this](../movement.md) for more information.

        :return: An `ActionStatus` indicating if the Magnebot turned by the angle and if not, why.
        """

        if isinstance(target, int):
            target_arr = self.state.object_transforms[target].position
            target_dict = TDWUtils.array_to_vector3(target_arr)
        elif isinstance(target, dict):
            target_arr = TDWUtils.vector3_to_array(target)
            target_dict = target
        else:
            raise Exception(f"Invalid target: {target}")

        angle = TDWUtils.get_angle_between(v1=self.state.magnebot_transform.forward,
                                           v2=target_arr - self.state.magnebot_transform.position)
        return self.turn_by(angle=angle, aligned_at=aligned_at, stop_on_collision=stop_on_collision,
                            target_position=target_dict)

    def move_by(self, distance: float, arrived_at: float = 0.1, stop_on_collision: Union[bool, CollisionDetection] = True) -> ActionStatus:
        """
        Move the Magnebot forward or backward by a given distance.

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_move`
        - `collision`
        - `tipping`

        :param distance: The target distance. If less than zero, the Magnebot will move backwards.
        :param arrived_at: If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful.
        :param stop_on_collision: If True, if the Magnebot will stop when it detects certain collisions. If False, ignore collisions. This can also be a [`CollisionDetection`](collision_detection.md) object. [Read this](../movement.md) for more information.

        :return: An `ActionStatus` indicating if the Magnebot moved by `distance` and if not, why.
        """

        def __set_collision_action(collision: bool) -> None:
            """
            If there was a collision, record the collision state.

            :param collision: If True, there was a collision.
            """

            if not collision:
                self._previous_collision = CollisionAction.none
            elif distance > 0:
                self._previous_collision = CollisionAction.move_positive
            else:
                self._previous_collision = CollisionAction.move_negative
        # Set the current collision state.
        if isinstance(stop_on_collision, bool):
            if stop_on_collision:
                self._collision_detection = Magnebot._COLLISION_ON
            else:
                self._collision_detection = Magnebot._COLLISION_OFF
        elif isinstance(stop_on_collision, CollisionDetection):
            self._collision_detection = stop_on_collision
        else:
            raise Exception("Invalid object type for stop_on_collision.")
        # Don't try to collide with the same thing twice.
        if self._collision_detection.previous_was_same and \
                ((distance > 0 and self._previous_collision == CollisionAction.move_positive) or
                 (distance < 0 and self._previous_collision == CollisionAction.move_negative)):
            __set_collision_action(True)
            return ActionStatus.collision

        self._start_action()
        self._start_move_or_turn()

        # The initial position of the robot.
        p0 = self.state.magnebot_transform.position
        p0_v3 = TDWUtils.array_to_vector3(p0)
        target_position = self.state.magnebot_transform.position + (self.state.magnebot_transform.forward * distance)
        target_position_v3 = TDWUtils.array_to_vector3(target_position)
        minimum_friction = Magnebot._DEFAULT_WHEEL_FRICTION
        d = np.linalg.norm(target_position - p0)
        d_0 = d
        # We're already here.
        if d < arrived_at:
            self._end_action(previous_action_was_move=True)
            if self._debug:
                print(f"No movement. We're already here: {d}")
            __set_collision_action(False)
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
            move_frames = 0
            while not move_done and move_frames < 2000:
                # If the `arrived_at` threshold is very small, using this easing command to slow the Magnebot down.
                if arrived_at < 0.2:
                    resp = self.communicate([{"$type": "set_magnebot_wheels_during_move",
                                              "position": target_position_v3,
                                              "origin": p0_v3,
                                              "arrived_at": arrived_at,
                                              "brake_distance": Magnebot._BRAKE_DISTANCE,
                                              "minimum_friction": minimum_friction}])
                else:
                    resp = self.communicate([])
                move_state_1 = SceneState(resp=resp)
                # If we're about to tip over, immediately stop and try to correct the tip.
                # End the action and record it as a collision to prevent the Magnebot from trying the same action again.
                if self._about_to_tip:
                    self._stop_tipping(state=move_state_1)
                    self._end_action(previous_action_was_move=True)
                    __set_collision_action(True)
                    return ActionStatus.tipping

                dt = np.linalg.norm(move_state_1.magnebot_transform.position - move_state_0.magnebot_transform.position)
                if dt < 0.001:
                    move_done = True
                for i in range(len(resp) - 1):
                    if OutputData.get_data_type_id(resp[i]) == "mwhe":
                        mwhe = MagnebotWheels(resp[i])
                        if mwhe.get_success():
                            self._end_action(previous_action_was_move=True)
                            if self._debug:
                                print("Move complete!",
                                      TDWUtils.array_to_vector3(self.state.magnebot_transform.position), d)
                            __set_collision_action(False)
                            return ActionStatus.success
                        else:
                            move_done = True
                move_frames += 1
                move_state_0 = move_state_1

                # Check if we collided with the environment or with any objects.
                if self._collided():
                    self._stop_wheels(state=move_state_1)
                    if self._debug:
                        print("Collision. Stopping movement.")
                    self._end_action(previous_action_was_move=True)
                    __set_collision_action(True)
                    return ActionStatus.collision
            wheel_state = move_state_0
            # If the move took too long, assume there was a collision.
            if not move_done:
                self._stop_wheels(state=wheel_state)
                if self._debug:
                    print("Couldn't complete move! Stopping movement.")
                self._end_action(previous_action_was_move=True)
                __set_collision_action(True)
                return ActionStatus.collision
            # Check if we're at the destination.
            p1 = wheel_state.magnebot_transform.position
            d = np.linalg.norm(target_position - p1)

            # Arrived!
            if d < arrived_at:
                self._end_action(previous_action_was_move=True)
                if self._debug:
                    print("Move complete!", TDWUtils.array_to_vector3(self.state.magnebot_transform.position), d)
                __set_collision_action(False)
                return ActionStatus.success
            # Go until we've traversed the distance.
            if d < 0.5:
                self._set_brake_wheel_drives()
                minimum_friction = Magnebot._BRAKE_FRICTION
            # 0.5 is a magic number.
            spin = (d / Magnebot._WHEEL_CIRCUMFERENCE) * 360 * 0.5 * (1 if distance > 0 else -1)
            d_total = np.linalg.norm(p1 - p0)
            if d_total > d_0:
                spin *= -1
            if self._debug:
                print(f"distance: {distance}", f"d: {d}", f"speed: {spin}")
            attempts += 1
        p1 = wheel_state.magnebot_transform.position
        d = np.linalg.norm(p1 - p0)
        self._end_action(previous_action_was_move=True)
        # Arrived!
        if np.abs(np.abs(distance) - d) < arrived_at:
            __set_collision_action(False)
            return ActionStatus.success
        # Failed to arrive.
        else:
            # If the Magenbot failed to move, mark this as a collision (even if it wasn't)
            # so the Magnebot can't choose the same action and direction again.
            __set_collision_action(True)
            return ActionStatus.failed_to_move

    def move_to(self, target: Union[int, Dict[str, float]], arrived_at: float = 0.1,
                aligned_at: float = 1, stop_on_collision: Union[bool, CollisionDetection] = True) -> ActionStatus:
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
        :param stop_on_collision: If True, if the Magnebot will stop when it detects certain collisions. If False, ignore collisions. This can also be a [`CollisionDetection`](collision_detection.md) object. [Read this](../movement.md) for more information.

        :return: An `ActionStatus` indicating if the Magnebot moved to the target and if not, why.
        """

        # Turn to face the target.
        status = self.turn_to(target=target, aligned_at=aligned_at, stop_on_collision=stop_on_collision)
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

            return self.move_by(distance=distance, arrived_at=arrived_at, stop_on_collision=stop_on_collision)
        else:
            self._end_action()
            return status

    def reset_position(self) -> ActionStatus:
        """
        Reset the Magnebot so that it isn't tipping over. Set the Magnebot's position from `(x, y, z)` to `(x, 0, z)`, set its rotation to the default rotation (see `tdw.tdw_utils.QuaternionUtils.IDENTITY`), and drop all held objects. The action ends when all previously-held objects stop moving.

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

    def reach_for(self, target: Dict[str, float], arm: Arm, absolute: bool = True, arrived_at: float = 0.125,
                  target_orientation: TargetOrientation = TargetOrientation.auto,
                  orientation_mode: OrientationMode = OrientationMode.auto) -> ActionStatus:
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
        :param target_orientation: [The target orientation of the IK solution.](../arm_articulation.md)
        :param orientation_mode: [The orientation mode of the IK solution.](../arm_articulation.md)

        :return: An `ActionStatus` indicating if the magnet at the end of the `arm` is at the `target` and if not, why.
        """

        def __success(state):
            """
            :param state: The current scene state during arm motion.

            :return: True if the magnet is at the target position.
            """

            magnet_position = Magnebot._absolute_to_relative(
                position=state.joint_positions[self.magnebot_static.magnets[arm]],
                state=state)
            return np.linalg.norm(magnet_position - target_arr) < arrived_at

        if absolute:
            target = Magnebot._absolute_to_relative(position=TDWUtils.vector3_to_array(target), state=self.state)
            target = TDWUtils.array_to_vector3(target)
        target_arr = TDWUtils.vector3_to_array(target)
        return self._do_ik(target=target, arm=arm, arrived_at=arrived_at,
                           target_orientation=target_orientation, orientation_mode=orientation_mode,
                           is_success=__success, start=None, end=None)

    def grasp(self, target: int, arm: Arm, target_orientation: TargetOrientation = TargetOrientation.auto,
              orientation_mode: OrientationMode = OrientationMode.auto) -> ActionStatus:
        """
        Try to grasp the target object with the arm. The Magnebot will reach for the nearest position on the object.

        If the magnet grasps the object, the arm will stop moving and the action is successful.

        Possible [return values](action_status.md):

        - `success`
        - `cannot_reach`
        - `failed_to_grasp`

        :param target: The ID of the target object.
        :param arm: The arm of the magnet that will try to grasp the object.
        :param target_orientation: [The target orientation of the IK solution.](../arm_articulation.md)
        :param orientation_mode: [The orientation mode of the IK solution.](../arm_articulation.md)

        :return: An `ActionStatus` indicating if the magnet at the end of the `arm` is holding the `target` and if not, why.
        """

        def __success(state):
            """
            :param state: The current scene state during arm motion.

            :return: True if the magnet is grasping the object.
            """

            return Magnebot._is_grasping(target, arm, state)

        def __start():
            """
            Enable the magnet.
            """

            self._next_frame_commands.append({"$type": "set_magnet_targets",
                                              "arm": arm.name,
                                              "targets": [target]})

        def __end():
            """
            Stop trying to grasp the target.
            """

            self._next_frame_commands.append({"$type": "set_magnet_targets",
                                              "arm": arm.name,
                                              "targets": []})

        if target in self.state.held[arm]:
            if self._debug:
                print(f"Already holding {target}")
            return ActionStatus.success

        self._start_action()
        __start()
        # Get the bounds positions of the object.
        resp = self.communicate({"$type": "send_bounds",
                                 "ids": [target],
                                 "frequency": "once"})
        bounds = get_data(resp=resp, d_type=Bounds)
        self.state = SceneState(resp=resp)
        # Spherecast to the center of the bounds.
        magnet_position = self.state.joint_positions[self.magnebot_static.magnets[arm]]
        resp = self.communicate({"$type": "send_spherecast",
                                 "radius": 0.2,
                                 "origin": TDWUtils.array_to_vector3(magnet_position),
                                 "destination": TDWUtils.array_to_vector3(bounds.get_center(0))})
        self.state = SceneState(resp=resp)
        magnet_position = self.state.joint_positions[self.magnebot_static.magnets[arm]]

        # Get the nearest spherecasted point.
        nearest_distance = np.inf
        nearest_position = np.array([0, 0, 0])
        got_raycast_point = False
        for i in range(len(resp) - 1):
            r_id = OutputData.get_data_type_id(resp[i])
            if r_id == "rayc":
                raycast = Raycast(resp[i])
                # Ignore raycasts that didn't hit the target.
                if not raycast.get_hit() or not raycast.get_hit_object() or raycast.get_object_id() != target:
                    continue
                got_raycast_point = True
                point = np.array(raycast.get_point())
                raycast_distance = np.linalg.norm(point - magnet_position)
                if raycast_distance < nearest_distance:
                    nearest_distance = raycast_distance
                    nearest_position = point
        # We found a good target!
        if got_raycast_point:
            target_position = nearest_position
        # Try to get a target from cached bounds data.
        else:
            sides_dict = {"left": np.array(bounds.get_left(0)),
                          "right": np.array(bounds.get_right(0)),
                          "front": np.array(bounds.get_front(0)),
                          "back": np.array(bounds.get_back(0)),
                          "top": np.array(bounds.get_top(0)),
                          "bottom": np.array(bounds.get_bottom(0))}
            # If we haven't cached the bounds for this object, just return all of the sides.
            if self.objects_static[target].name not in ObjectStatic.CONVEX_SIDES:
                sides = list(sides_dict.values())
            else:
                # Get only the convex sides of the object using cached data.
                sides: List[np.array] = list()
                for i, side in enumerate(ObjectStatic.BOUNDS_SIDES):
                    if i in ObjectStatic.CONVEX_SIDES[self.objects_static[target].name]:
                        sides.append(sides_dict[side])
            center = np.array(bounds.get_center(0))
            # If there are no valid bounds sides, aim for the center and hope for the best.
            if len(sides) == 0:
                target_position = center
            else:
                # If the object is higher up than the magnet, remove the lowest side.
                if self.state.object_transforms[target].position[1] > magnet_position[1] and len(sides) > 1:
                    lowest: int = -1
                    y = np.inf
                    for i in range(len(sides)):
                        if sides[i][1] < y:
                            lowest = i
                            y = sides[i][1]
                    del sides[lowest]
                # Get the closest side to the magnet.
                nearest_side: np.array = sides[0]
                d = np.inf
                for side in sides:
                    dd = np.linalg.norm(side - magnet_position)
                    if dd < d:
                        nearest_side = side
                        d = dd
                # Raycast from the nearest side to the center.
                resp = self.communicate({"$type": "send_raycast",
                                         "origin": TDWUtils.array_to_vector3(nearest_side),
                                         "destination": TDWUtils.array_to_vector3(center)})
                self.state = SceneState(resp=resp)
                raycast = get_data(resp=resp, d_type=Raycast)
                # If the raycast hit the object, aim for that point.
                if raycast.get_hit() and raycast.get_hit_object() and raycast.get_object_id() == target:
                    target_position = np.array(raycast.get_point())
                else:
                    target_position = center
        if self._debug:
            self._next_frame_commands.append({"$type": "add_position_marker",
                                              "position": TDWUtils.array_to_vector3(target_position)})
        # Do the IK action.
        target_position = TDWUtils.array_to_vector3(self._absolute_to_relative(position=target_position,
                                                                               state=self.state))
        status = self._do_ik(target=target_position, arm=arm, arrived_at=0.05,
                             target_orientation=target_orientation, orientation_mode=orientation_mode,
                             is_success=__success, start=__start, end=__end)
        if target in self.state.held[arm]:
            return ActionStatus.success
        elif status == ActionStatus.cannot_reach:
            return status
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
        m.init_floorplan_scene(scene="2a", layout=1)
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
        m.init_floorplan_scene(scene="2a", layout=1)
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
        self._next_frame_commands.extend([{"$type": "set_pass_masks",
                                           "pass_masks": ["_img"],
                                           "avatar_id": camera_id},
                                          {"$type": "set_anti_aliasing",
                                           "mode": "subpixel",
                                           "avatar_id": camera_id}])

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
        for angle, axis in zip([roll, pitch, yaw], ["roll", "pitch", "yaw"]):
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

        This only works if you've loaded an occupancy map via `self.init_floorplan_scene()`.

        ```python
        from magnebot import Magnebot

        m = Magnebot(launch_build=False)
        m.init_floorplan_scene(scene="1a", layout=0)
        x = 30
        y = 16
        print(m.occupancy_map[x][y]) # 0 (free and navigable position)
        print(m.get_occupancy_position(x, y)) # (1.1157886505126946, 2.2528389358520506)
        ```

        :param i: The i coordinate in the occupancy map.
        :param j: The j coordinate in the occupancy map.

        :return: Tuple: (x coordinate; z coordinate) of the corresponding worldspace position.
        """

        x = self._scene_bounds.x_min + (i * OCCUPANCY_CELL_SIZE)
        z = self._scene_bounds.z_min + (j * OCCUPANCY_CELL_SIZE)
        return x, z

    def get_visible_objects(self) -> List[int]:
        """
        Get all objects visible to the Magnebot in `self.state` using the id (segmentation color) image.

        :return: A list of IDs of visible objects.
        """

        # Try to get unique colors with a reasonable number of max colors.
        # If the number of colors exceeds this, `getcolors()` returns None.
        for max_colors in [256, 512, 1024]:
            try:
                colors = [c[1] for c in self.state.get_pil_images()["id"].getcolors(maxcolors=max_colors)]
                return [o for o in self.objects_static if self.objects_static[o].segmentation_color in colors]
            except TypeError:
                continue
        # This should never happen, but it's better to prevent the build rom crashing.
        return []

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
            # Check if the Magnebot is colliding with a wall.
            for object_id in collisions.env_collisions:
                # Ignore collisions with the floor.
                if collisions.env_collisions[object_id].floor or object_id not in self.magnebot_static.joints:
                    continue
                if collisions.env_collisions[object_id].state == "enter":
                    self.colliding_with_wall = True
                    break
                else:
                    self.colliding_with_wall = False
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

    def _end_action(self, previous_action_was_move: bool = False) -> List[bytes]:
        """
        Set the scene state at the end of an action.

        :param previous_action_was_move: If True, remember that the most recent action was a move or turn.

        :return: The response from the build.
        """

        self._previous_action_was_move = previous_action_was_move

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
        resp = self.communicate([])
        self.state = SceneState(resp=resp)
        # Remove any held objects from the list of colliding objects.
        temp: List[int] = list()
        for object_id in self.colliding_objects:
            good = True
            for arm in self.state.held:
                if object_id in self.state.held[arm]:
                    good = False
                    break
            if good:
                temp.append(object_id)
        self.colliding_objects = temp
        # Save images.
        if self.auto_save_images:
            self.state.save_images(output_directory=self.images_directory)
        return resp

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

        if self._previous_action_was_move:
            return

        # Move the torso up to its default height to prevent anything from dragging.
        # Reset the column rotation.
        self._next_frame_commands.extend([{"$type": "set_immovable",
                                           "immovable": True},
                                          {"$type": "set_prismatic_target",
                                           "joint_id": self.magnebot_static.arm_joints[ArmJoint.torso],
                                           "target": 1},
                                          {"$type": "set_revolute_target",
                                           "joint_id": self.magnebot_static.arm_joints[ArmJoint.column],
                                           "target": 0}])
        # Reset the wheel drives.
        for wheel_id in self.magnebot_static.wheels.values():
            drive = self.magnebot_static.joints[wheel_id].drives["x"]
            self._next_frame_commands.append({"$type": "set_robot_joint_drive",
                                              "joint_id": wheel_id,
                                              "force_limit": drive.force_limit,
                                              "stiffness": drive.stiffness,
                                              "damping": drive.damping})
        # Wait until these two joints stop moving.
        self._do_arm_motion(joint_ids=[self.magnebot_static.arm_joints[ArmJoint.torso],
                                       self.magnebot_static.arm_joints[ArmJoint.column]], non_moving=0.01)
        # Let the Magnebot move again.
        self._next_frame_commands.append({"$type": "set_immovable",
                                          "immovable": False})

    def _start_ik(self, target: Dict[str, float], arm: Arm, absolute: bool = True, arrived_at: float = 0.125,
                  state: SceneState = None, allow_column: bool = True, fixed_torso_prismatic: float = None,
                  object_id: int = None, do_prismatic_first: bool = False,
                  orientation_mode: OrientationMode = OrientationMode.auto,
                  target_orientation: TargetOrientation = TargetOrientation.auto) -> ActionStatus:
        """
        Start an IK action.

        Regarding `target_orientation` and `orientation_mode`: These affect the IK solution and end pose of the arm. The action might succeed or fail depending on these settings. If both parameters are set to `auto`, the Magnebot will try to choose the best possible settings. For more information, [read this](https://notebook.community/Phylliade/ikpy/tutorials/Orientation).

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

        # If the `state` argument is None, work off of `self.state`.
        if state is None:
            state = self.state
        if isinstance(target, dict):
            target = TDWUtils.vector3_to_array(target)
        # Convert to relative coordinates.
        if absolute:
            target = self._absolute_to_relative(position=target, state=state)
        target: np.array
        # If the target is too far away, fail immediately.
        distance = np.linalg.norm(target - np.array([0, target[1], 0]))
        if distance > 0.99:
            return ActionStatus.cannot_reach

        # Try to get an orientation mode.
        if target_orientation == TargetOrientation.auto and orientation_mode == OrientationMode.auto:
            orientations = self._get_ik_orientations(arm=arm, target=target)
            # If we didn't get a solution, the action is VERY likely to fail.
            # See: `controllers/tests/benchmark/ik.py`
            if len(orientations) == 0:
                return ActionStatus.cannot_reach
            target_orientation = orientations[0].target_orientation
            orientation_mode = orientations[0].orientation_mode

        # Get the initial angles of each joint.
        # The first angle is always 0 (the origin link).
        initial_angles = self._get_initial_angles(arm=arm, has_object=object_id is not None)

        # Generate an IK chain, given the current desired torso height.
        # The extra height is the y position of the column's base.
        chain = self.__get_ik_chain(arm=arm, allow_column=allow_column, object_id=object_id)

        # Get the IK solution.
        ik = chain.inverse_kinematics(target_position=target,
                                      initial_position=initial_angles,
                                      orientation_mode=str(orientation_mode.value) if isinstance(orientation_mode.value, str) else None,
                                      target_orientation=np.array(target_orientation.value) if isinstance(target_orientation.value, list) else None)
        # Plot the IK solution.
        if self._debug:
            try:
                import matplotlib.pyplot
                ax = matplotlib.pyplot.figure().add_subplot(111, projection='3d')
                ax.set_xlabel("X")
                ax.set_ylabel("Y")
                ax.set_zlabel("Z")
                chain.plot(ik, ax, target=target,
                           link_names=["column", "torso", "shoulder_pitch", "elbow_pitch", "wrist_pitch"])
                matplotlib.pyplot.show()
            # This won't always work on a remote server.
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
        if d > arrived_at:
            return ActionStatus.cannot_reach

        angles = list()
        torso_prismatic = 0
        # For the purposes of getting the angles, remove the origin link, the magnet, and the object.
        if object_id is None:
            ik_angles = ik[1:-1]
        else:
            ik_angles = ik[1:-2]
        # Convert all of the angles or positions.
        for i, angle in enumerate(ik_angles):
            # This is the torso.
            if i == 1:
                if fixed_torso_prismatic is not None:
                    torso_prismatic = fixed_torso_prismatic
                    angles.append(fixed_torso_prismatic)
                else:
                    # Convert the torso value to a percentage and then to a joint position.
                    torso_prismatic = Magnebot._y_position_to_torso_position(y_position=angle)
                    angles.append(torso_prismatic)
            # Append all other angles normally.
            else:
                angles.append(float(np.rad2deg(angle)))
        if self._debug:
            print(angles)

        # Make the base of the Magnebot immovable because otherwise it might push itself off the ground and tip over.
        # Do this now, rather than in the `commands` list, to prevent a slide during arm movement.
        self.communicate({"$type": "set_immovable",
                          "immovable": True})

        if fixed_torso_prismatic is not None:
            torso_prismatic = fixed_torso_prismatic
        # Slide the torso to the desired height.
        if do_prismatic_first:
            torso_id = self.magnebot_static.arm_joints[ArmJoint.torso]
            self.communicate({"$type": "set_prismatic_target",
                              "joint_id": torso_id,
                              "target": torso_prismatic})
            self._do_arm_motion(joint_ids=[torso_id])

        # Convert the IK solution into TDW commands, using the expected joint and axis order.
        self._append_ik_commands(angles=angles, arm=arm, torso=fixed_torso_prismatic is None and not do_prismatic_first)
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

    def _append_ik_commands(self, angles: np.array, arm: Arm, torso: bool) -> None:
        """
        Convert target angles to TDW commands and append them to `_next_frame_commands`.

        :param angles: The target angles in degrees.
        :param arm: The arm.
        :param torso: If True, add torso commands.
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
            elif joint_type == JointType.prismatic:
                # Sometimes, we want the torso at its current position.
                if torso:
                    commands.append({"$type": "set_prismatic_target",
                                     "joint_id": joint_id,
                                     "target": angles[i]})
                i += 1
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
                              "target": 1},
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
            # See above for how the torso is reset.
            elif joint_type == JointType.prismatic:
                pass
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

    def _do_ik(self, target: Dict[str, float], arm: Arm, arrived_at: float, is_success, start, end,
               target_orientation: TargetOrientation = TargetOrientation.auto,
               orientation_mode: OrientationMode = OrientationMode.auto) -> ActionStatus:
        """
        Shared code for `reach_for()` and `grasp()`.
        Solve for an IK target and move the arm joints until they're done moving or the action is successful.
        If the orientation parameters are (auto, auto), try several other orientation parameters before giving up.

        :param target: The target position for the magnet at the arm to reach, RELATIVE to the Magnebot.
        :param arm: The arm that will reach for the target.
        :param is_success: A function that returns a boolean a SceneState parameter. Used to determine if the action was successful during or after arm motion.
        :param start: A function that is called at the start of this function and retry. Can be None.
        :param end: A function that is called at the end of this function and retry. Can be None.
        :param arrived_at: If the magnet is this distance or less from `target`, then the action is successful.
        :param target_orientation: [The target orientation of the IK solution.](../arm_articulation.md)
        :param orientation_mode: [The orientation mode of the IK solution.](../arm_articulation.md)

        :return: An `ActionStatus` indicating if the IK action was successful and if not, why.
        """

        self._start_action()
        if start is not None:
            start()

        # Start the IK action.
        status = self._start_ik(target=target, arm=arm, absolute=False, arrived_at=arrived_at,
                                do_prismatic_first=target["y"] > Magnebot._DEFAULT_TORSO_Y,
                                target_orientation=target_orientation, orientation_mode=orientation_mode)
        if status != ActionStatus.success:
            if end is not None:
                end()
            self._end_action()
            return status

        # Wait for the arm motion to end.
        self._do_arm_motion(conditional=lambda s: is_success(s))
        self._end_action()
        if is_success(self.state):
            if end is not None:
                end()
            return ActionStatus.success
        else:
            # Try alternative orientation parameters.
            if target_orientation == TargetOrientation.auto and orientation_mode == OrientationMode.auto:
                for orientation in self._get_ik_orientations(target=TDWUtils.vector3_to_array(target), arm=arm)[1:]:
                    self._start_action()
                    if start is not None:
                        start()
                    status = self._start_ik(target=target, arm=arm, absolute=False, arrived_at=arrived_at,
                                            do_prismatic_first=target["y"] > Magnebot._DEFAULT_TORSO_Y,
                                            target_orientation=orientation.target_orientation,
                                            orientation_mode=orientation.orientation_mode)
                    # Ignore this solution.
                    if status != ActionStatus.success:
                        continue
                    # Wait for the arm motion to end.
                    self._do_arm_motion(conditional=lambda s: is_success(s))
                    self._end_action()
                    if is_success(self.state):
                        if end is not None:
                            end()
                        return ActionStatus.success
            return ActionStatus.failed_to_reach

    @staticmethod
    def _is_grasping(target: int, arm: Arm, state: SceneState) -> bool:
        """
        :param target: The object ID.
        :param arm: The arm.
        :param state: The SceneState.

        :return: True if the arm is holding the object in this scene state.
        """

        return target in state.held[arm]

    def __get_ik_chain(self, arm: Arm, object_id: int = None, allow_column: bool = True) -> Chain:
        """
        :param arm: The arm of the chain (determines the x position).
        :param object_id: If not None, append this object to the IK chain.
        :param allow_column: If True, allow column rotation.

        :return: An IK chain for the arm.
        """

        links: List[Link] = [OriginLink()]
        if allow_column:
            links.append(URDFLink(name="column",
                                  translation_vector=np.array([0, Magnebot._COLUMN_Y, 0]),
                                  orientation=np.array([0, 0, 0]),
                                  rotation=np.array([0, 1, 0]),
                                  bounds=(np.deg2rad(-179), np.deg2rad(179))))
        else:
            links.append(URDFLink(name="column",
                                  translation_vector=np.array([0, Magnebot._COLUMN_Y, 0]),
                                  orientation=np.array([0, 0, 0]),
                                  rotation=None))
        links.extend([URDFLink(name="torso",
                               translation_vector=np.array([0, 0, 0]),
                               orientation=np.array([0, 0, 0]),
                               rotation=np.array([0, 1, 0]),
                               is_revolute=False,
                               use_symbolic_matrix=False,
                               bounds=(Magnebot._TORSO_MIN_Y, Magnebot._TORSO_MAX_Y)),
                      URDFLink(name="shoulder_pitch",
                               translation_vector=np.array([0.215 * (-1 if arm == Arm.left else 1), 0.059, 0.019]),
                               orientation=np.array([0, 0, 0]),
                               rotation=np.array([1, 0, 0]),
                               bounds=(np.deg2rad(-150), np.deg2rad(70))),
                      URDFLink(name="shoulder_roll",
                               translation_vector=np.array([0, 0, 0]),
                               orientation=np.array([0, 0, 0]),
                               rotation=np.array([0, 1, 0]),
                               bounds=(np.deg2rad(-70 if arm == Arm.left else -45),
                                       np.deg2rad(45 if arm == Arm.left else 70))),
                      URDFLink(name="shoulder_yaw",
                               translation_vector=np.array([0, 0, 0]),
                               orientation=np.array([0, 0, 0]),
                               rotation=np.array([0, 0, 1]),
                               bounds=(np.deg2rad(-110 if arm == Arm.left else -20),
                                       np.deg2rad(20 if arm == Arm.left else 110))),
                      URDFLink(name="elbow_pitch",
                               translation_vector=np.array([0.033 * (-1 if arm == Arm.left else 1), -0.33, 0]),
                               orientation=np.array([0, 0, 0]),
                               rotation=np.array([-1, 0, 0]),
                               bounds=(np.deg2rad(-90), np.deg2rad(145))),
                      URDFLink(name="wrist_pitch",
                               translation_vector=np.array([0, -0.373, 0]),
                               orientation=np.array([0, 0, 0]),
                               rotation=np.array([-1, 0, 0]),
                               bounds=(np.deg2rad(-90), np.deg2rad(90))),
                      URDFLink(name="wrist_roll",
                               translation_vector=np.array([0, 0, 0]),
                               orientation=np.array([0, 0, 0]),
                               rotation=np.array([0, -1, 0]),
                               bounds=(np.deg2rad(-90), np.deg2rad(90))),
                      URDFLink(name="wrist_yaw",
                               translation_vector=np.array([0, 0, 0]),
                               orientation=np.array([0, 0, 0]),
                               rotation=np.array([0, 0, 1]),
                               bounds=(np.deg2rad(-15), np.deg2rad(15))),
                      URDFLink(name="magnet",
                               translation_vector=np.array([0, -0.095, 0]),
                               orientation=np.array([0, 0, 0]),
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
                                  orientation=np.array([0, 0, 0]),
                                  rotation=None))

        return Chain(name=arm.name, links=links)

    def _cache_static_data(self, resp: List[bytes]) -> None:
        """
        Cache static data after initializing the scene.
        Sets the initial SceneState.

        :param resp: The response from the build.
        """

        SceneState.FRAME_COUNT = 0

        # Get the scene bounds.
        self._scene_bounds = SceneBounds(resp=resp)

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

    def _stop_wheels(self, state: SceneState) -> None:
        """
        Stop wheel movement.

        :param state: The current state.
        """
        commands = []
        for wheel in self.magnebot_static.wheels:
            # Set the target of each wheel to its current position.
            commands.append({"$type": "set_revolute_target",
                             "target": float(state.joint_angles[self.magnebot_static.wheels[wheel]][0]),
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
        self.colliding_with_wall = False
        self.camera_rpy: np.array = np.array([0, 0, 0])
        self._next_frame_commands.clear()
        self._trigger_events.clear()
        self._per_frame_commands.clear()
        self._object_init_commands.clear()
        self._about_to_tip = False
        self._previous_collision = CollisionAction.none
        self._previous_action_was_move = False
        self._collision_detection = Magnebot._COLLISION_ON

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

    def _get_ik_orientations(self, target: np.array, arm: Arm) -> List[Orientation]:
        """
        Try to automatically choose an orientation for an IK solution.
        Our best-guess approach is to load a numpy array of known IK orientation solutions per position,
        find the position in the array closest to `target`, and use that IK orientation solution.

        For more information: https://notebook.community/Phylliade/ikpy/tutorials/Orientation
        And: https://github.com/alters-mit/magnebot/blob/main/doc/arm_articulation.md

        :param arm: The arm doing the motion.
        :param target: The target position.

        :return: A list of best guesses for IK orientation. The first element in the list is almost always the best option. The other elements are neighboring options.
        """

        # Get the index of the nearest position using scipy, and use that index to get the corresponding orientation.
        # Source: https://stackoverflow.com/questions/52364222/find-closest-similar-valuevector-inside-a-matrix
        # noinspection PyArgumentList
        orientations = [self._ik_orientations[arm][cKDTree(self._ik_positions).query(target, k=1)[1]]]

        # If we couldn't find a solution, assume that there isn't one and return an empty list.
        if orientations[0] < 0:
            return []

        # Append other orientation options that are nearby.
        # noinspection PyArgumentList
        orientations.extend(list(set([self._ik_orientations[arm][i] for i in
                                      cKDTree(self._ik_positions).query(target, k=9)[1] if
                                      self._ik_orientations[arm][i] not in orientations])))
        return [ORIENTATIONS[o] for o in orientations if o >= 0]

    def _collided(self) -> bool:
        """
        :return: True if the Magnebot collided with a wall or with an object that should cause it to stop moving.
        """

        # Stop on a collision with the wall.
        if self._collision_detection.walls and self.colliding_with_wall:
            return True
        # Always check for collisions with objects in the include list.
        for object_id in self.colliding_objects:
            if object_id in self._collision_detection.include_objects:
                return True
        # If we don't care about objects, end here.
        if not self._collision_detection.objects:
            return False
        for object_id in self.colliding_objects:
            # Ignore objects in the exclude list.
            if object_id in self._collision_detection.exclude_objects:
                continue
            # Stop on a collision if the object has sufficiently high mass or is in the exclude list.
            if self.objects_static[object_id].mass > self._collision_detection.mass or \
                    object_id in self._collision_detection.include_objects:
                return True
        return False

    @staticmethod
    def _y_position_to_torso_position(y_position: float) -> float:
        """
        :param y_position: A y positional value in meters.

        :return: A corresponding joint position value for the torso prismatic joint.
        """

        # Convert the torso value to a percentage and then to a joint position.
        p = (y_position * (Magnebot._TORSO_MAX_Y - Magnebot._TORSO_MIN_Y)) + Magnebot._TORSO_MIN_Y
        return float(p * 1.5)

    @final
    def _init_scene(self, scene: List[dict], post_processing: List[dict] = None, end: List[dict] = None,
                    magnebot_position: Dict[str, float] = None) -> ActionStatus:
        """
        Add a scene to TDW. Set post-processing. Add objects (if any). Add the Magnebot. Request and cache data.

        :param scene: A list of commands to initialize the scene.
        :param post_processing: A list of commands to set post-processing values. Can be None.
        :param end: A list of commands sent at the end of scene initialization (on the same frame). Can be None.
        :param magnebot_position: The position of the Magnebot. If None, defaults to {"x": 0, "y": 0, "z": 0}.

        :return: An `ActionStatus` (always `success`).
        """

        commands: List[dict] = []
        # Initialize the scene.
        commands.extend(scene)
        # Initialize post-processing settings.
        if post_processing is not None:
            commands.extend(post_processing)
        # Add objects.
        for object_id in self._object_init_commands:
            commands.extend(self._object_init_commands[object_id])

        # Add the Magnebot. Add the avatar and set up its camera. Request output data.
        commands.extend([{"$type": "add_magnebot",
                          "position": magnebot_position if magnebot_position is not None else TDWUtils.VECTOR3_ZERO},
                         {"$type": "set_immovable",
                          "immovable": True},
                         {"$type": "create_avatar",
                          "type": "A_Img_Caps_Kinematic"},
                         {"$type": "set_pass_masks",
                          "pass_masks": ["_img", "_id", "_depth"]},
                         {"$type": "enable_image_sensor",
                          "enable": False},
                         {"$type": "set_anti_aliasing",
                          "mode": "subpixel"},
                         {"$type": "send_robots",
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
                         {"$type": "send_environments"},
                         {"$type": "send_collisions",
                          "enter": True,
                          "stay": False,
                          "exit": True,
                          "collision_types": ["obj", "env"]}])
        # Request log messages.
        if self._debug:
            commands.append({"$type": "send_log_messages"})
        # Add misc. end commands.
        if end is not None:
            commands.extend(end)
        # Clear all data from the previous scene.
        self._clear_data()
        # Send the commands.
        resp = self.communicate(commands)
        self._cache_static_data(resp=resp)
        # Wait for the Magnebot to reset to its neutral position.
        status = self._do_arm_motion()
        self._end_action()
        return status

    def _get_post_processing_commands(self) -> List[dict]:
        """
        :return: A list of post-processing commands for scene setup.
        """

        return [{"$type": "set_aperture",
                 "aperture": 8.0},
                {"$type": "set_focus_distance",
                 "focus_distance": 2.25},
                {"$type": "set_post_exposure",
                 "post_exposure": 0.4},
                {"$type": "set_ambient_occlusion_intensity",
                 "intensity": 0.175},
                {"$type": "set_ambient_occlusion_thickness_modifier",
                 "thickness": 3.5}]

    def _set_brake_wheel_drives(self) -> None:
        """
        Set the wheel drives while braking.
        """

        for wheel_id in self.magnebot_static.wheels.values():
            drive = self.magnebot_static.joints[wheel_id].drives["x"]
            self._next_frame_commands.append({"$type": "set_robot_joint_drive",
                                              "joint_id": wheel_id,
                                              "force_limit": drive.force_limit * 0.9,
                                              "stiffness": drive.stiffness,
                                              "damping": drive.damping})
