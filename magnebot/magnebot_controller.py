import random
from json import loads
import numpy as np
from typing import List, Dict, Optional, Union, Tuple
from ikpy.chain import Chain
from ikpy.link import OriginLink, URDFLink
from ikpy.utils import geometry
from tdw.floorplan_controller import FloorplanController
from tdw.output_data import Version, StaticRobot, SegmentationColors, Bounds, Rigidbodies
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


class Magnebot(FloorplanController):
    # Global forward directional vector.
    _FORWARD = np.array([0, 0, 1])

    # Load default audio values for objects.
    __OBJECT_AUDIO = PyImpact.get_object_info()

    def __init__(self, port: int = 1071, launch_build: bool = True, id_pass: bool = True,
                 screen_width: int = 256, screen_height: int = 256, debug: bool = False, hold_limit: int = 1):
        super().__init__(port=port, launch_build=launch_build)

        self._id_pass = id_pass
        self._debug = debug
        self._hold_limit = hold_limit

        # Set the expected IK chains.
        self.__ik_chains: Dict[Arm, Chain] = {Arm.left: Magnebot.__get_arm(Arm.left),
                                              Arm.right: Magnebot.__get_arm(Arm.right)}

        self.state: Optional[SceneState] = None

        # Commands to initialize objects.
        self._object_init_commands: Dict[int, List[dict]] = dict()

        # Cache static data.
        self.objects_static: Dict[int, ObjectStatic] = dict()
        self.segmentation_color_to_id: Dict[int, int] = dict()
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

    def init_scene(self, scene: str, layout: int, room: int = -1) -> None:
        """
        Initialize a scene, populate it with objects, and add the avatar.

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
        self.__cache_static_data(resp=resp)

    def init_test_scene(self) -> None:
        """
        Initialize an empty test room with a Magnebot.

        This function can be called instead of `init_scene()` for testing purposes. If so, it must be called before any other API calls.

        ```python
        from magnebot import Magnebot

        m = Magnebot()
        m.init_test_scene()

        # Your code here.
        ```

        You can safely call `init_test_scene()` more than once to reset the simulation.
        """

        commands = [{"$type": "load_scene",
                     "scene_name": "ProcGenScene"},
                    TDWUtils.create_empty_room(12, 12)]
        commands.extend(self._get_scene_init_commands(magnebot_position={"x": 0, "y": 0, "z": 0}))
        resp = self.communicate(commands)
        self.__cache_static_data(resp=resp)

    def turn_by(self, angle: float, speed: float = 15, aligned_at: float = 3) -> ActionStatus:
        """
        Turn the Magnebot by an angle.

        The Magnebot will turn by small increments to align with the target angle.

        When turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

        Possible [return values](action_status.md):

        - `success`
        - `too_many_attempts`
        - `unaligned`

        :param angle: The target angle in degrees. Positive value = clockwise turn.
        :param aligned_at: If the different between the current angle and the target angle is less than this value, then the action is successful.
        :param speed: The wheels will turn this many degrees per attempt to turn.

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
        wheel_state = SceneState(resp=self.communicate([]))
        # The initial forward vector.
        f0 = self.state.magnebot_transform.forward
        # The approximately number of iterations required, given the distance and speed.
        num_attempts = int(np.abs(angle) + 1) * speed * 50
        attempts = 0
        angle_0 = angle
        while attempts < num_attempts:
            attempts += 1
            # Set the direction of the wheels for the turn and send commands.
            commands = []
            for wheel in self.magnebot_static.wheels:
                # Get the target from the current joint angles.
                if "left" in wheel:
                    target = wheel_state.joint_angles[self.magnebot_static.wheels[wheel]].angles[
                                 0] + speed if angle > 0 else -speed
                else:
                    target = wheel_state.joint_angles[self.magnebot_static.wheels[wheel]].angles[
                                 0] - speed if angle > 0 else -speed
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
            # If the difference between the target angle and the current angle is very small, we're done.
            if np.abs(angle_1 - angle_0) < aligned_at:
                self._set_state()
                return ActionStatus.success
        self._set_state()
        angle_1 = _get_angle_1()
        if np.abs(angle_1 - angle_0) < aligned_at:
            return ActionStatus.success
        elif attempts >= num_attempts:
            return ActionStatus.too_many_attempts
        else:
            return ActionStatus.unaligned

    def turn_to(self, target: Union[int, Dict[str, float]], speed: float = 15, aligned_at: float = 3) -> ActionStatus:
        """
        Turn the Magnebot to face a target object or position.

        The Magnebot will turn by small increments to align with the target angle.

        When turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

        Possible [return values](action_status.md):

        - `success`
        - `too_many_attempts`
        - `unaligned`

        :param target: Either the ID of an object or a Vector3 position.
        :param aligned_at: If the different between the current angle and the target angle is less than this value, then the action is successful.
        :param speed: The wheels will turn this many degrees per attempt to turn.

        :return: An `ActionStatus` indicating if the Magnebot turned by the angle and if not, why.
        """

        if isinstance(target, int):
            target = self.state.object_transforms[target].position
        elif isinstance(target, dict):
            target = TDWUtils.vector3_to_array(target)
        else:
            raise Exception(f"Invalid target: {target}")

        self._start_action()
        angle = TDWUtils.get_angle(forward=self.state.magnebot_transform.forward, origin=self.state.magnebot_transform.position,
                                   position=target)
        return self.turn_by(angle=angle, speed=speed, aligned_at=aligned_at)

    def move_by(self, distance: float, speed: float = 15, arrived_at: float = 0.1) -> ActionStatus:
        """
        Move the Magnebot forward or backward by a given distance.

        Possible [return values](action_status.md):

        - `success`
        - `overshot_move`
        - `too_many_attempts`

        :param distance: The target distance. If less than zero, the Magnebot will move backwards.
        :param speed: The Magnebot's wheels will rotate by this many degrees per iteration.
        :param arrived_at: If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful.

        :return: An `ActionStatus` indicating if the Magnebot moved by `distance` and if not, why.
        """

        self._start_action()
        # The initial position of the robot.
        p0 = self.state.magnebot_transform.position

        # Go until we've traversed the distance.
        d = 0
        # The approximately number of iterations required, given the distance and speed.
        num_attempts = int(np.abs(distance) + 1) * speed * 50
        attempts = 0
        # Wait for the wheels to stop turning.
        wheel_state = SceneState(resp=self.communicate([]))
        while d < np.abs(distance) and attempts < num_attempts:
            # Move forward a bit and see if we've arrived.
            commands = []
            for wheel in self.magnebot_static.wheels:
                # Get the target from the current joint angles. Add or subtract the speed.
                target = wheel_state.joint_angles[self.magnebot_static.wheels[wheel]].angles[
                             0] + speed if distance > 0 else -speed
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
            attempts += 1
        self._set_state()
        if np.abs(np.abs(distance) - d) < arrived_at:
            return ActionStatus.success
        elif attempts >= num_attempts:
            return ActionStatus.too_many_attempts
        else:
            return ActionStatus.overshot_move

    def move_to(self, target: Union[int, Dict[str, float]], move_speed: float = 15, arrived_at: float = 0.1,
                turn_speed: float = 15, aligned_at: float = 3,
                move_on_turn_fail: bool = False) -> ActionStatus:
        """
        Move the Magnebot to a target object or position.

        The Magnebot will first try to turn to face the target by internally calling a `turn_to()` action.

        - `success`
        - `overshot_move`
        - `too_many_attempts` (when moving, and also when turning if `move_on_turn_fail == False`)
        - `unaligned` (when turning if `move_on_turn_fail == False`)

        :param target: Either the ID of an object or a Vector3 position.
        :param move_speed: The Magnebot's wheels will rotate by this many degrees per iteration when moving.
        :param arrived_at: While moving, if at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful.
        :param turn_speed: The Magnebot's wheels will rotate by this many degrees per iteration when turning.
        :param aligned_at: While turning, if the different between the current angle and the target angle is less than this value, then the action is successful.
        :param move_on_turn_fail: If True, the Magnebot will move forward even if the internal `turn_to()` action didn't return `success`.

        :return: An `ActionStatus` indicating if the Magnebot moved to the target and if not, why.
        """

        # Turn to face the target.
        status = self.turn_to(target=target, speed=turn_speed, aligned_at=aligned_at)
        self._start_action()
        # Move to the target unless the turn failed (and if we care about the turn failing).
        if status == ActionStatus.success or move_on_turn_fail:
            if isinstance(target, int):
                target = self.state.object_transforms[target].position
            elif isinstance(target, dict):
                target = TDWUtils.vector3_to_array(target)
            else:
                raise Exception(f"Invalid target: {target}")

            return self.move_by(distance=np.linalg.norm(self.state.magnebot_transform.position - target), speed=move_speed,
                                arrived_at=arrived_at)
        else:
            self._set_state()
            return status

    def reach_for(self, target: Dict[str, float], arm: Arm, check_if_possible: bool = True,
                  absolute: bool = False, arrived_at: float = 0.125) -> ActionStatus:
        target = TDWUtils.vector3_to_array(target)
        # Convert to relative coordinates.
        if absolute:
            target = self.__absolute_to_relative(position=target, state=self.state)

        angles = self.__get_ik(target_position=target, arm=arm)
        # Check if the IK solution reaches the target.
        chain = self.__ik_chains[arm]
        transformation_matrices = chain.forward_kinematics(angles, full_kinematics=True)
        nodes = []
        for (index, link) in enumerate(chain.links):
            (node, orientation) = geometry.from_transformation_matrix(transformation_matrices[index])
            nodes.append(node)
        # The expected destination.
        destination = np.array(nodes[-1][:-1])

        if check_if_possible:
            d = np.linalg.norm(destination - target)
            if d > arrived_at:
                if self._debug:
                    print(f"Target {target} is too far away from {arm}: {d}")
                return ActionStatus.too_far_to_reach
        angles = [float(np.rad2deg(a)) for a in angles[1:-1]]

        raise Exception("TODO: send command and then wait for everything to stop turning.")

        resp = self.communicate([])  # TODO remove this
        state = SceneState(resp=resp)
        angles = []  # TODO Record the IK solution.
        # Record the IK solution.
        self.__joint_angles[arm] = angles
        self._set_state()

        # Check how close the magnet is to the expected relative position.
        magnet_position = self.__absolute_to_relative(position=self.state.robot_joints[self.magnebot_static.magnets[arm]].position,
                                                      state=self.state)
        d = np.linalg.norm(destination - magnet_position)
        if d < arrived_at:
            return ActionStatus.success
        else:
            if self._debug:
                print(f"Tried and failed to reach for {target}: {d}")
            return ActionStatus.failed_to_reach

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

    def _set_state(self) -> None:
        """
        Set the scene state at the end of an action.
        """

        self.state = SceneState(resp=self.communicate([{"$type": "enable_image_sensor",
                                                        "enable": True},
                                                       {"$type": "send_images"},
                                                       {"$type": "send_camera_matrices"}]))

    def _wheels_are_done(self, state_0: SceneState) -> Tuple[bool, SceneState]:
        """
        Advances one frame and then determines if the wheels are still turning.

        :param state_0: The scene state from the previous frame.

        :return: True if none of the wheels are tunring.
        """

        resp = self.communicate([])
        state_1 = SceneState(resp=resp)
        for w_id in self.magnebot_static.wheels.values():
            if np.linalg.norm(state_0.joint_angles[w_id].angles[0] -
                              state_1.joint_angles[w_id].angles[0]) > 0.001:
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
                    {"$type": "set_magnebot_magnet_hold_limit",
                     "Arm": "left",
                     "limit": self._hold_limit},
                    {"$type": "set_magnebot_magnet_hold_limit",
                     "Arm": "right",
                     "limit": self._hold_limit},
                    {"$type": "create_avatar",
                     "type": "A_Img_Caps_Kinematic"},
                    {"$type": "parent_avatar_to_robot",
                     "position": {"x": 0, "y": 0.8, "z": 0.24}},
                    {"$type": "set_pass_masks",
                     "pass_masks": ["_img", "_id", "_depth"] if self._id_pass else ["_img", "_depth"]},
                    {"$type": "enable_image_sensor",
                     "enable": False}]
        # Add the avatar (camera).
        commands.extend(TDWUtils.create_avatar())
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

    def __cache_static_data(self, resp: List[bytes]) -> None:
        """
        Cache static data after initializing the scene.
        Sets the initial SceneState.

        :param resp: The response from the build.
        """

        # Clear static data.
        self.__magnets.clear()
        self.objects_static.clear()
        self.segmentation_color_to_id.clear()
        self._next_frame_commands.clear()
        SceneState.FRAME_COUNT = 0

        # Set the default joint angles.
        self.__joint_angles = {Arm.left: [0, 0, 0, 0, 0, 0, 0, 0, 0],
                               Arm.right: [0, 0, 0, 0, 0, 0, 0, 0, 0]}

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
        self._set_state()

    def __absolute_to_relative(self, position: np.array, state: SceneState) -> np.array:
        """
        :param position: The position in absolute world coordinates.
        :param state: The current state.

        :return: The converted position relative to the Magnebot's position and rotation.
        """

        return TDWUtils.rotate_position_around(position=position - self.state.magnebot_transform.position,
                                               angle=-TDWUtils.get_angle_between(v1=Magnebot._FORWARD,
                                                                                 v2=state.magnebot_transform.forward))

    def __get_ik(self, target_position: np.array, arm: Arm) -> List[float]:
        """
        :param target_position: The target position as a numpy array: `[x, y, z]`
        :param arm: The arm of the chain.

        :return: A list of angles in degrees to turn to.
        """

        # Get the IK solution using the current angles.
        frame_target = np.eye(4)
        frame_target[:3, 3] = target_position
        return self.__ik_chains[arm].inverse_kinematics_frame(target=frame_target,
                                                              initial_position=self.__joint_angles[arm],
                                                              no_position=False)

    @staticmethod
    def __get_arm(arm: Arm) -> Chain:
        """
        :param arm: The arm of the chain (determines the x position).

        :return: An IK chain for the arm.
        """

        return Chain(name=arm.name, links=[
            OriginLink(),
            URDFLink(name="shoulder_pitch",
                     translation_vector=[0.225 * -1 if arm == Arm.left else 1, 0.565, 0.075],
                     orientation=[-np.pi / 2, 0, 0],
                     rotation=[-1, 0, 0],
                     bounds=(-1.0472, 3.12414)),
            URDFLink(name="shoulder_yaw",
                     translation_vector=[0, 0, 0],
                     orientation=[0, 0, 0],
                     rotation=[0, 1, 0],
                     bounds=(-1.5708, 1.5708)),
            URDFLink(name="shoulder_roll",
                     translation_vector=[0, 0, 0],
                     orientation=[0, 0, 0],
                     rotation=[0, 0, 1],
                     bounds=(-0.785398, 0.785398)),
            URDFLink(name="elbow_pitch",
                     translation_vector=[0, 0, -0.235],
                     orientation=[0, 0, 0],
                     rotation=[-1, 0, 0],
                     bounds=(0, 2.79253)),
            URDFLink(name="wrist_pitch",
                     translation_vector=[0, 0, -0.15],
                     orientation=[0, 0, 0],
                     rotation=[0, 0, 1],
                     bounds=(-1.5708, 1.5708)),
            URDFLink(name="wrist_yaw",
                     translation_vector=[0, 0, 0],
                     orientation=[0, 0, 0],
                     rotation=[0, 0, 1],
                     bounds=(-1.5708, 1.5708)),
            URDFLink(name="wrist_roll",
                     translation_vector=[0, 0, 0],
                     orientation=[0, 0, 0],
                     rotation=[-1, 0, 0],
                     bounds=(0, 1.5708)),
            URDFLink(name="magnet",
                     translation_vector=[0, 0, -0.0625],
                     orientation=[0, 0, 0],
                     rotation=[0, 0, 0])])

