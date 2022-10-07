from collections import Counter
from json import loads
from typing import List, Optional, Dict, Union, Tuple
import numpy as np
from overrides import final
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.scene_data.scene_bounds import SceneBounds
from tdw.add_ons.object_manager import ObjectManager
from tdw.add_ons.step_physics import StepPhysics
from tdw.add_ons.floorplan import Floorplan
from magnebot.action_status import ActionStatus
from magnebot.arm import Arm
from magnebot.ik.orientation_mode import OrientationMode
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.image_frequency import ImageFrequency
from magnebot.magnebot import Magnebot
from magnebot.paths import SPAWN_POSITIONS_PATH, OCCUPANCY_MAPS_DIRECTORY
from magnebot.constants import OCCUPANCY_CELL_SIZE
from magnebot.util import get_default_post_processing_commands


class MagnebotController(Controller):
    """
    This is a simplified API for single-agent [Magnebot](magnebot.md) simulations.

    ```python
    from magnebot import MagnebotController

    c = MagnebotController()
    c.init_scene()
    c.move_by(2)
    c.end()
    ```

    Differences between the `MagnebotController` and `Magnebot` agent:

    - The `MagnebotController` *is a [controller](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/controller.md)* and will send its own commands.
    - In the `MagnebotController`, the agent's action will begin and end automatically. In the above example, `c.move_by(2)` will continuously advance the simulation until the Magnebot has moved 2 meters or stopped unexpectedly (i.e. due to a collision).
    - The `MagnebotController`, [physics frames are skipped per output data frame](skip_frames.md); see `skip_frames` in the constructor.
    - Images are always returned at the end of every action. In the above example, [`c.magnebot.dynamic.images`](magnebot_dynamic.md) will be updated at the end of `c.move_by(2)`.
    - The `MagnebotController` includes two functions that can initialize a scene optimized for the Magnebot.
    - The `MagnebotController` adds an [`ObjectManager`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/add_ons/object_manager.md).
    """

    def __init__(self, port: int = 1071, launch_build: bool = True, screen_width: int = 256, screen_height: int = 256,
                 random_seed: int = None, skip_frames: int = 10, check_pypi_version: bool = True):
        """
        :param port: The port number.
        :param launch_build: If True, automatically launch the build. If one doesn't exist, download and extract the correct version. Set this to False to use your own build, or (if you are a backend developer) to use Unity Editor.
        :param screen_width: The width of the screen in pixels.
        :param screen_height: The height of the screen in pixels.
        :param random_seed: The seed used for random numbers. If None, this is chosen randomly. In the Magnebot API this is used only when randomly selecting a start position for the Magnebot (see the `room` parameter of `init_floorplan_scene()`). The same random seed is used in higher-level APIs such as the Transport Challenge.
        :param skip_frames: The build will return output data this many physics frames per simulation frame (communicate() call). This will greatly speed up the simulation, but eventually there will be a noticeable loss in physics accuracy. If you want to render every frame, set this to 0.
        :param check_pypi_version: If True, compare the locally installed version of TDW and Magnebot to the most recent versions on PyPi.
        """

        super().__init__(port=port, launch_build=launch_build, check_version=False)
        """:field
        A numpy array of an occupancy map. This is set after calling `self.init_floorplan_scene()`.
        
        Shape = (1, width, length) where width and length are the number of cells in the grid. Each grid cell has a radius of 0.49. To convert from occupancy map (x, y) coordinates to worldspace (x, z) coordinates, see: `self.get_occupancy_position(i, j)`.
        Each element is an integer describing the occupancy at that position.
        
        | Value | Meaning |
        | --- | --- |
        | -1 | The cell is out of bounds of the scene or not navigable. |
        | 0 | The cell is unoccupied; there is a floor at this position but there are no objects. |
        | 1 | The cell is occupied by at least one object or a wall. |
        
        ```python
        from magnebot import MagnebotController

        c = MagnebotController()
        c.init_floorplan_scene(scene="1a", layout=0, room=0)
        x = 30
        z = 16
        print(c.occupancy_map[x][z]) # 0 (free and navigable position)
        print(c.get_occupancy_position(x, z)) # (1.1157886505126946, 2.2528389358520506)
        c.end()
        ```
        
        Images of occupancy maps can be found [here](https://github.com/alters-mit/magnebot/tree/master/doc/images/occupancy_maps). The blue squares are free navigable positions. Images are named `[scene]_[layout].jpg` For example, the occupancy map image for scene "2a" layout 0 is: `2_0.jpg`.

        The occupancy map is static, meaning that it won't update when objects are moved.

        Note that it is possible for the Magnebot to go to positions that aren't "free". The Magnebot's base is a rectangle that is longer on the sides than the front and back. The occupancy grid cell size is defined by the longer axis, so it is possible for the Magnebot to move forward and squeeze into a smaller space. The Magnebot can also push, lift, or otherwise move objects out of its way.
        """
        self.occupancy_map: np.array = np.array([], dtype=int)
        # Get a random seed.
        if random_seed is None:
            random_seed = self.get_unique_id()
        """:field
        A random number generator.
        """
        self.rng: np.random.RandomState = np.random.RandomState(random_seed)
        # Set the screen and render quality.
        self.communicate([{"$type": "set_render_quality",
                           "render_quality": 5},
                          {"$type": "set_screen_size",
                           "width": screen_width,
                           "height": screen_height}])
        # Skip a set number of frames per communicate() call.
        self._step_physics: StepPhysics = StepPhysics(skip_frames)
        self.add_ons.append(self._step_physics)
        self._check_pypi_version: bool = check_pypi_version
        # The scene bounds. This is used along with the occupancy map to get (x, z) worldspace positions.
        self._scene_bounds: Optional[SceneBounds] = None
        """:field
        [The Magnebot agent.](magnebot.md). Call this to access static or dynamic data:
        
        ```python
        from magnebot import MagnebotController

        m = MagnebotController()
        m.init_scene()
        print(m.magnebot.dynamic.transform.position)
        m.end()
        ```
        """
        self.magnebot: Optional[Magnebot] = None
        """:field
        [An `ObjectManager`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/add_ons/object_manager.md) for tracking static and dynamic object data:
        
        ```python
        from magnebot import MagnebotController

        m = MagnebotController()
        m.init_floorplan_scene(scene="1a", layout=0, room=0)
        for object_id in m.objects.objects_static:
            name = m.objects.objects_static[object_id].name
            segmentation_color = m.objects.objects_static[object_id].segmentation_color
            print(object_id, name, segmentation_color)
        for object_id in m.objects.transforms:
            position = m.objects.transforms[object_id].position
            print(object_id, position)
        m.end()
        ```
        """
        self.objects: Optional[ObjectManager] = None

    def init_scene(self) -> None:
        """
        Initialize the Magnebot in an empty test room.

        ```python
        from magnebot import MagnebotController

        m = MagnebotController()
        m.init_scene()

        # Your code here.

        m.end()
        ```
        """

        return self._init_scene(scene=[{"$type": "load_scene",
                                        "scene_name": "ProcGenScene"},
                                       TDWUtils.create_empty_room(12, 12)])

    def init_floorplan_scene(self, scene: str, layout: int, room: int = None) -> None:
        """
        Initialize a scene, populate it with objects, and add the Magnebot.

        It might take a few minutes to initialize the scene. You can call `init_scene()` more than once to reset the simulation; subsequent resets at runtime should be extremely fast.

        Set the `scene` and `layout` parameters in `init_scene()` to load an interior scene with furniture and props. Set the `room` to spawn the avatar in the center of a specific room.

        ```python
        from magnebot import MagnebotController

        m = MagnebotController()
        m.init_floorplan_scene(scene="2b", layout=0, room=1)

        # Your code here.

        m.end()
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

        :param scene: The name of an interior floorplan scene. Each number (1, 2, etc.) has a different shape, different rooms, etc. Each letter (a, b, c) is a cosmetically distinct variant with the same floorplan.
        :param layout: The furniture layout of the floorplan. Each number (0, 1, 2) will populate the floorplan with different furniture in different positions.
        :param room: The index of the room that the Magnebot will spawn in the center of. If None, the room will be chosen randomly.

        :return: An `ActionStatus` (always success).
        """

        f = Floorplan()
        f.init_scene(scene=scene, layout=layout)
        # Get the spawn position of the Magnebot.
        rooms = loads(SPAWN_POSITIONS_PATH.read_text())[scene[0]][str(layout)]
        room_keys = list(rooms.keys())
        if room is None:
            room = self.rng.choice(room_keys)
        else:
            room = str(room)
            assert room in room_keys, f"Invalid room: {room}; valid rooms are: {room_keys}"
        magnebot_position: Dict[str, float] = rooms[room]

        # Load the occupancy map.
        self.occupancy_map = np.load(str(OCCUPANCY_MAPS_DIRECTORY.joinpath(f"{scene[0]}_{layout}.npy").resolve()))
        # Initialize the scene.
        return self._init_scene(scene=f.commands,
                                post_processing=get_default_post_processing_commands(),
                                position=magnebot_position)

    def turn_by(self, angle: float, aligned_at: float = 1) -> ActionStatus:
        """
        Turn the Magnebot by an angle.

        While turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

        :param angle: The target angle in degrees. Positive value = clockwise turn.
        :param aligned_at: If the difference between the current angle and the target angle is less than this value, then the action is successful.

        :return: An `ActionStatus` indicating whether the Magnebot succeeded in turning and if not, why.
        """

        self.magnebot.turn_by(angle=angle, aligned_at=aligned_at)
        return self._do_action()

    def turn_to(self, target: Union[int, Dict[str, float], np.ndarray], aligned_at: float = 1) -> ActionStatus:
        """
        Turn the Magnebot to face a target object or position.

        While turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

        :param target: The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array.
        :param aligned_at: If the difference between the current angle and the target angle is less than this value, then the action is successful.

        :return: An `ActionStatus` indicating whether the Magnebot succeeded in turning and if not, why.
        """

        self.magnebot.turn_to(target=target, aligned_at=aligned_at)
        return self._do_action()

    def move_by(self, distance: float, arrived_at: float = 0.1) -> ActionStatus:
        """
        Move the Magnebot forward or backward by a given distance.

        :param distance: The target distance. If less than zero, the Magnebot will move backwards.
        :param arrived_at: If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful.

        :return: An `ActionStatus` indicating whether the Magnebot succeeded in moving and if not, why.
        """

        self.magnebot.move_by(distance=distance, arrived_at=arrived_at)
        return self._do_action()

    def move_to(self, target: Union[int, Dict[str, float], np.ndarray], arrived_at: float = 0.1, aligned_at: float = 1,
                arrived_offset: float = 0) -> ActionStatus:
        """
        Move to a target object or position. This combines turn_to() followed by move_by().

        :param target: The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array.
        :param arrived_at: If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful.
        :param aligned_at: If the difference between the current angle and the target angle is less than this value, then the action is successful.
        :param arrived_offset: Offset the arrival position by this value. This can be useful if the Magnebot needs to move to an object but shouldn't try to move to the object's centroid. This is distinct from `arrived_at` because it won't affect the Magnebot's braking solution.

        :return: An `ActionStatus` indicating whether the Magnebot succeeded in moving and if not, why.
        """

        self.magnebot.move_to(target=target, arrived_at=arrived_at, aligned_at=aligned_at,
                              arrived_offset=arrived_offset)
        return self._do_action()

    def reach_for(self, target: Union[Dict[str, float], np.ndarray], arm: Arm, absolute: bool = True,
                  orientation_mode: OrientationMode = OrientationMode.auto,
                  target_orientation: TargetOrientation = TargetOrientation.auto, arrived_at: float = 0.125) -> ActionStatus:
        """
        Reach for a target position. The action ends when the magnet is at or near the target position, or if it fails to reach the target.
        The Magnebot may try to reach for the target multiple times, trying different IK orientations each time, or no times, if it knows the action will fail.

        :param target: The target position. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array.
        :param arm: [The arm that will reach for the target.](arm.md)
        :param absolute: If True, `target` is in absolute world coordinates. If `False`, `target` is relative to the position and rotation of the Magnebot.
        :param arrived_at: If the magnet is this distance or less from `target`, then the action is successful.
        :param orientation_mode: [The orientation mode.](ik/orientation_mode.md)
        :param target_orientation: [The target orientation.](ik/target_orientation.md)

        :return: An `ActionStatus` indicating whether the Magnebot's magnet reached the target position and if not, why.
        """

        self.magnebot.reach_for(target=target, arm=arm, absolute=absolute, orientation_mode=orientation_mode,
                                target_orientation=target_orientation, arrived_at=arrived_at)
        return self._do_action()

    def grasp(self, target: int, arm: Arm, orientation_mode: OrientationMode = OrientationMode.auto,
              target_orientation: TargetOrientation = TargetOrientation.auto) -> ActionStatus:
        """
        Try to grasp a target object.
        The action ends when either the Magnebot grasps the object, can't grasp it, or fails arm articulation.

        :param target: The ID of the target object.
        :param arm: [The arm that will reach for and grasp the target.](arm.md)
        :param orientation_mode: [The orientation mode.](ik/orientation_mode.md)
        :param target_orientation: [The target orientation.](ik/target_orientation.md)

        :return: An `ActionStatus` indicating whether the Magnebot succeeded in grasping the object and if not, why.
        """

        self.magnebot.grasp(target=target, arm=arm, orientation_mode=orientation_mode,
                            target_orientation=target_orientation)
        return self._do_action()

    def drop(self, target: int, arm: Arm, wait_for_object: bool = True) -> ActionStatus:
        """
        Drop an object held by a magnet.

        :param target: The ID of the object currently held by the magnet.
        :param arm: [The arm of the magnet holding the object.](arm.md)
        :param wait_for_object: If True, the action will continue until the object has finished falling. If False, the action advances the simulation by exactly 1 frame.

        :return: An `ActionStatus` indicating whether the Magnebot succeeded in dropping the object and if not, why.
        """

        self.magnebot.drop(target=target, arm=arm, wait_for_object=wait_for_object)
        return self._do_action()

    def reset_arm(self, arm: Arm) -> ActionStatus:
        """
        Reset the Magnebot so that it isn't tipping over.
        This will rotate the Magnebot to the default rotation (so that it isn't tipped over) and move the Magnebot to the nearest empty space on the floor.
        It will also drop any held objects.

        This will be interpreted by the physics engine as a _very_ sudden and fast movement.
        This action should only be called if the Magnebot is a position that will prevent the simulation from continuing (for example, if the Magnebot fell over).

        :param arm: [The arm to reset.](arm.md)

        :return: An `ActionStatus` indicating whether the Magnebot reset its arm and if not, why.
        """

        self.magnebot.reset_arm(arm=arm)
        return self._do_action()

    def reset_position(self) -> ActionStatus:
        """
        Reset the Magnebot so that it isn't tipping over.
        This will rotate the Magnebot to the default rotation (so that it isn't tipped over) and move the Magnebot to the nearest empty space on the floor.
        It will also drop any held objects.

        This will be interpreted by the physics engine as a _very_ sudden and fast movement.
        This action should only be called if the Magnebot is a position that will prevent the simulation from continuing (for example, if the Magnebot fell over).

        :return: An `ActionStatus` indicating whether the Magnebot reset its position and if not, why.
        """

        self.magnebot.reset_position()
        return self._do_action()

    def rotate_camera(self, roll: float = 0, pitch: float = 0, yaw: float = 0) -> ActionStatus:
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

        :return: An `ActionStatus` indicating whether the Magnebot rotated its camera freely or if the rotation was clamped at a limit.
        """

        self.magnebot.rotate_camera(roll=roll, pitch=pitch, yaw=yaw)
        return self._do_action()

    def look_at(self, target: Union[int, Dict[str, float], np.ndarray]) -> ActionStatus:
        """
        Rotate the Magnebot's camera to look at a target object or position.

        This action is not compatible with `rotate_camera()` because it will ignore (roll, pitch, yaw) constraints; if you use this action, `rotate_camera()` won't work as intended until you call `reset_camera()`.

        :param target: The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array.

        :return: An `ActionStatus` (always success).
        """

        self.magnebot.look_at(target=target)
        return self._do_action()

    def move_camera(self, position: Union[Dict[str, float], np.ndarray]) -> ActionStatus:
        """
        Move the Magnebot's camera by an offset position.

        By default, the camera is parented to the torso and will continue to move when the torso moves. You can prevent this by setting `parent_camera_to_torso=False` in the Magnebot constructor.

        :param position: The positional offset that the camera will move by.

        :return: An `ActionStatus` (always success).
        """

        self.magnebot.move_camera(position=position)
        return self._do_action()

    def reset_camera(self, position: bool = True, rotation: bool = True) -> ActionStatus:
        """
        Reset the rotation of the Magnebot's camera to its default angles and/or its default position relative to its parent (by default, its parent is the torso).

        :param position: If True, reset the camera's position.
        :param rotation: If True, reset the camera' rotation.

        :return: An `ActionStatus` (always success).
        """

        self.magnebot.reset_camera(position=position, rotation=rotation)
        return self._do_action()

    def slide_torso(self, height: float) -> ActionStatus:
        """
        Slide the Magnebot's torso up or down.

        :param height: The height of the torso. Must be between `magnebot.constants.TORSO_MIN_Y` and `magnebot.constants.TORSO_MAX_Y`.

        :return: An `ActionStatus` (always success).
        """

        self.magnebot.slide_torso(height=height)
        return self._do_action()

    def get_visible_objects(self) -> List[int]:
        """
        Get all objects visible to the Magnebot.

        :return: A list of IDs of visible objects.
        """

        # Source: https://stackoverflow.com/a/59709420
        colors = list(set(Counter(self.magnebot.dynamic.get_pil_images()["id"].getdata())))
        visible: List[int] = list()
        for o in self.objects.objects_static:
            segmentation_color = self.objects.objects_static[o].segmentation_color
            color = (segmentation_color[0], segmentation_color[1], segmentation_color[2])
            if color in colors:
                visible.append(o)
        return visible

    def end(self) -> None:
        """
        End the simulation. Terminate the build process.
        """

        self.communicate({"$type": "terminate"})

    def get_occupancy_position(self, i: int, j: int) -> Tuple[float, float]:
        """
        Converts the position `(i, j)` in the occupancy map to `(x, z)` worldspace coordinates.

        This only works if you've loaded an occupancy map via `self.init_floorplan_scene()`.

        :param i: The i coordinate in the occupancy map.
        :param j: The j coordinate in the occupancy map.

        :return: Tuple: (x coordinate; z coordinate) of the corresponding worldspace position.
        """

        x = self._scene_bounds.x_min + (i * OCCUPANCY_CELL_SIZE)
        z = self._scene_bounds.z_min + (j * OCCUPANCY_CELL_SIZE)
        return x, z

    def communicate(self, commands: Union[dict, List[dict]]) -> list:
        """
        Send commands and receive output data in response.

        :param commands: A list of JSON commands.

        :return The output data from the build.
        """

        return super().communicate(commands=commands)

    @final
    def _init_scene(self, scene: List[dict], post_processing: List[dict] = None, objects: List[dict] = None,
                    end: List[dict] = None, position: Dict[str, float] = None,
                    rotation: Dict[str, float] = None) -> None:
        """
        Add a scene to TDW. Set post-processing. Add objects (if any). Add the Magnebot. Request and cache data.

        :param scene: A list of commands to initialize the scene.
        :param post_processing: A list of commands to set post-processing values. Can be None.
        :param objects: A list of object initialization commands.
        :param end: A list of commands sent at the end of scene initialization (on the same frame). Can be None.
        :param position: The position of the Magnebot. If None, defaults to {"x": 0, "y": 0, "z": 0}.
        :param rotation: The rotation of the Magnebot. If None, defaults to {"x": 0, "y": 0, "z": 0}.
        """

        if position is None:
            position = TDWUtils.VECTOR3_ZERO
        if rotation is None:
            rotation = TDWUtils.VECTOR3_ZERO
        if objects is None:
            objects = []

        # Add the Magnebot.
        if self.magnebot is None:
            self.magnebot = Magnebot(robot_id=0, position=position, rotation=rotation,
                                     image_frequency=ImageFrequency.once, check_version=self._check_pypi_version)
            self.add_ons.append(self.magnebot)
        else:
            self.magnebot.reset(position=position, rotation=rotation)
        # Add the object manager.
        if self.objects is None:
            self.objects = ObjectManager(transforms=True, rigidbodies=False, bounds=False)
            self.add_ons.append(self.objects)
        # Reset the object manager.
        else:
            self.objects.initialized = False
        commands: List[dict] = []
        # Initialize the scene.
        commands.extend(scene)
        # Add objects.
        commands.extend(objects)
        # Initialize post-processing settings.
        if post_processing is not None:
            commands.extend(post_processing)
        # Request output data.
        commands.append({"$type": "send_scene_regions"})
        # Add misc. end commands.
        if end is not None:
            commands.extend(end)
        # Send the commands.
        resp = self.communicate(commands)
        # Set the scene bounds.
        self._scene_bounds = SceneBounds(resp=resp)
        self._do_action()

    def _do_action(self) -> ActionStatus:
        while self.magnebot.action.status == ActionStatus.ongoing:
            self.communicate([])
        self.communicate([])
        return self.magnebot.action.status
