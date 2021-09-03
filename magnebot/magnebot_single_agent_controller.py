from collections import Counter
from pathlib import Path
from pkg_resources import resource_filename
from json import loads
from typing import List, Optional, Dict, Union, Tuple
import numpy as np
from overrides import final
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.scene.scene_bounds import SceneBounds
from tdw.add_ons.object_manager import ObjectManager
from tdw.add_ons.collision_manager import CollisionManager
from tdw.object_init_data import AudioInitData
from magnebot.action_status import ActionStatus
from magnebot.arm import Arm
from magnebot.ik.orientation_mode import OrientationMode
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.image_frequency import ImageFrequency
from magnebot.magnebot_agent import MagnebotAgent
from magnebot.skip_frames import SkipFrames
from magnebot.paths import SPAWN_POSITIONS_PATH, OCCUPANCY_MAPS_DIRECTORY
from magnebot.constants import OCCUPANCY_CELL_SIZE


class MagnebotSingleAgentController(Controller):
    def __init__(self, port: int = 1071, launch_build: bool = False, screen_width: int = 256, screen_height: int = 256,
                 random_seed: int = None, skip_frames: int = 10, check_pypi_version: bool = True):
        super().__init__(port=port, launch_build=launch_build, check_version=False)
        self.occupancy_map: np.array = np.array([], dtype=int)
        # Get a random seed.
        if random_seed is None:
            random_seed = self.get_unique_id()
        self._rng: np.random.RandomState = np.random.RandomState(random_seed)
        self.communicate([{"$type": "set_render_quality",
                           "render_quality": 5},
                          {"$type": "set_screen_size",
                           "width": screen_width,
                           "height": screen_height}])
        # Skip a set number of frames per communicate() call.
        self.add_ons.append(SkipFrames(skip_frames))
        self._check_pypi_version: bool = check_pypi_version
        # Commands to initialize objects.
        self._object_init_commands: Dict[int, List[dict]] = dict()
        # The scene bounds. This is used along with the occupancy map to get (x, z) worldspace positions.
        self._scene_bounds: Optional[SceneBounds] = None
        self.magnebot: Optional[MagnebotAgent] = None
        self.objects: Optional[ObjectManager] = None
        self.collisions: Optional[CollisionManager] = None

    def init_scene(self) -> None:
        """
        Initialize the Magnebot in an empty test room.

        ```python
        from magnebot import MagnebotSingleAgentController

        m = MagnebotSingleAgentController()
        m.init_scene()

        # Your code here.
        ```
        """

        return self._init_scene(scene=[{"$type": "load_scene", "scene_name": "ProcGenScene"},
                                       TDWUtils.create_empty_room(12, 12)])

    def init_floorplan_scene(self, scene: str, layout: int, room: int = None) -> None:
        """
        Initialize a scene, populate it with objects, and add the Magnebot.

        It might take a few minutes to initialize the scene. You can call `init_scene()` more than once to reset the simulation; subsequent resets at runtime should be extremely fast.

        Set the `scene` and `layout` parameters in `init_scene()` to load an interior scene with furniture and props. Set the `room` to spawn the avatar in the center of a specific room.

        ```python
        from magnebot import MagnebotSingleAgentController

        m = MagnebotSingleAgentController()
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
                                post_processing=[{"$type": "set_aperture",
                                                  "aperture": 8.0},
                                                 {"$type": "set_focus_distance",
                                                  "focus_distance": 2.25},
                                                 {"$type": "set_post_exposure",
                                                  "post_exposure": 0.4},
                                                 {"$type": "set_ambient_occlusion_intensity",
                                                  "intensity": 0.175},
                                                 {"$type": "set_ambient_occlusion_thickness_modifier",
                                                  "thickness": 3.5},
                                                 {"$type": "set_shadow_strength",
                                                  "strength": 1.0}],
                                magnebot_position=magnebot_position)

    def turn_by(self, angle: float, aligned_at: float = 1) -> ActionStatus:
        self.magnebot.turn_by(angle=angle, aligned_at=aligned_at)
        return self._do_action()

    def turn_to(self, target: Union[int, Dict[str, float], np.ndarray], aligned_at: float = 1) -> ActionStatus:
        self.magnebot.turn_to(target=target, aligned_at=aligned_at)
        return self._do_action()

    def move_by(self, distance: float, arrived_at: float = 0.1) -> ActionStatus:
        self.magnebot.move_by(distance=distance, arrived_at=arrived_at)
        return self._do_action()

    def move_to(self, target: Union[int, Dict[str, float], np.ndarray], arrived_at: float = 0.1, aligned_at: float = 1) -> ActionStatus:
        self.magnebot.move_to(target=target, arrived_at=arrived_at, aligned_at=aligned_at)
        return self._do_action()

    def reach_for(self, target: Dict[str, float], arm: Arm, absolute: bool = True,
                  orientation_mode: OrientationMode = OrientationMode.auto,
                  target_orientation: TargetOrientation = TargetOrientation.auto, arrived_at: float = 0.125) -> ActionStatus:
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

        self.magnebot.reach_for(target=target, arm=arm, absolute=absolute, orientation_mode=orientation_mode,
                                target_orientation=target_orientation, arrived_at=arrived_at)
        return self._do_action()

    def grasp(self, target: int, arm: Arm, orientation_mode: OrientationMode = OrientationMode.auto,
              target_orientation: TargetOrientation = TargetOrientation.auto) -> ActionStatus:
        """
        Try to grasp a target object.
        The action ends when either the Magnebot grasps the object, can't grasp it, or fails arm articulation.

        :param target: The ID of the target object.
        :param arm: [The arm used for this action.](../arm.md)
        :param orientation_mode: [The orientation mode.](../arm_articulation.md)
        :param target_orientation: [The target orientation.](../arm_articulation.md)
        """

        self.magnebot.grasp(target=target, arm=arm, orientation_mode=orientation_mode,
                            target_orientation=target_orientation)
        return self._do_action()

    def drop(self, target: int, arm: Arm, wait_for_object: bool) -> ActionStatus:
        """
        Drop an object held by a magnet.

        :param target: The ID of the object currently held by the magnet.
        :param arm: The arm of the magnet holding the object.
        :param wait_for_object: If True, the action will continue until the object has finished falling. If False, the action advances the simulation by exactly 1 frame.
        """

        self.magnebot.drop(target=target, arm=arm, wait_for_object=wait_for_object)
        return self._do_action()

    def reset_position(self) -> ActionStatus:
        """
        Reset the Magnebot so that it isn't tipping over.
        This will rotate the Magnebot to the default rotation (so that it isn't tipped over) and move the Magnebot to the nearest empty space on the floor.
        It will also drop any held objects.

        This will be interpreted by the physics engine as a _very_ sudden and fast movement.
        This action should only be called if the Magnebot is a position that will prevent the simulation from continuing (for example, if the Magnebot fell over).
        """

        self.magnebot.reset_position()
        return self._do_action()

    def rotate_camera(self, roll: float, pitch: float, yaw: float) -> ActionStatus:
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

        self.magnebot.rotate_camera(roll=roll, pitch=pitch, yaw=yaw)
        return self._do_action()

    def reset_camera(self) -> ActionStatus:
        """
        Reset the rotation of the Magnebot's camera to its default angles.
        """

        self.magnebot.reset_camera()
        return self._do_action()

    def get_visible_objects(self) -> List[int]:
        """
        Get all objects visible to the Magnebot.

        :return: A list of IDs of visible objects.
        """

        # Source: https://stackoverflow.com/a/59709420
        colors = set(Counter(self.magnebot.dynamic.get_pil_images()["id"].getdata()))
        return [o for o in self.objects.objects_static if self.objects.objects_static[o].segmentation_color in colors]

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

    @final
    def _init_scene(self, scene: List[dict], post_processing: List[dict] = None, end: List[dict] = None,
                    position: Dict[str, float] = None, rotation: Dict[str, float] = None) -> None:
        """
        Add a scene to TDW. Set post-processing. Add objects (if any). Add the Magnebot. Request and cache data.

        :param scene: A list of commands to initialize the scene.
        :param post_processing: A list of commands to set post-processing values. Can be None.
        :param end: A list of commands sent at the end of scene initialization (on the same frame). Can be None.
        :param position: The position of the Magnebot. If None, defaults to {"x": 0, "y": 0, "z": 0}.
        :param rotation: The rotation of the Magnebot. If None, defaults to {"x": 0, "y": 0, "z": 0}.
        """

        if position is None:
            position = TDWUtils.VECTOR3_ZERO
        if rotation is None:
            rotation = TDWUtils.VECTOR3_ZERO
        # Define the agent.
        self.magnebot = MagnebotAgent(robot_id=0, position=position, rotation=rotation,
                                      image_frequency=ImageFrequency.once, check_pypi_version=self._check_pypi_version)
        # Add the object manager and collision manager.
        self.objects = ObjectManager(transforms=True, rigidbodies=False, bounds=False)
        self.collisions = CollisionManager(objects=True, environment=True, enter=True, exit=True)
        # Add the add-ons.
        self.add_ons.extend([self.magnebot, self.objects, self.collisions])

        commands: List[dict] = []
        # Initialize the scene.
        commands.extend(scene)
        # Initialize post-processing settings.
        if post_processing is not None:
            commands.extend(post_processing)
        # Add objects.
        for object_id in self._object_init_commands:
            commands.extend(self._object_init_commands[object_id])
        # Request output data.
        commands.append({"$type": "send_environments"})
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
        return self.magnebot.action.status

