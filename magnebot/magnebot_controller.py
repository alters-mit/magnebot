import numpy as np
from typing import List, Dict, Optional, Union, Tuple
from tdw.floorplan_controller import FloorplanController
from tdw.output_data import Version, StaticRobot
from tdw.tdw_utils import TDWUtils
from tdw.object_init_data import AudioInitData
from tdw.py_impact import PyImpact, ObjectInfo
from tdw.release.pypi import PyPi
from magnebot.util import get_data
from magnebot.body_part_static import BodyPartStatic
from magnebot.scene_state import SceneState
from magnebot.action_status import ActionStatus


class Magnebot(FloorplanController):
    class __Wheel:
        def __init__(self, object_id: int, angle: float):
            self.object_id = object_id
            self.angle = angle

    # Global forward directional vector.
    _FORWARD = np.array([0, 0, 1])

    # Load default audio values for objects.
    __OBJECT_AUDIO = PyImpact.get_object_info()

    def __init__(self, port: int = 1071, launch_build: bool = True, id_pass: bool = True,
                 screen_width: int = 256, screen_height: int = 256, debug: bool = False):
        super().__init__(port=port, launch_build=launch_build)

        self._id_pass = id_pass
        self._debug = debug

        # Create an empty occupancy map.
        self.occupancy_map: Optional[np.array] = None
        self._scene_bounds: Optional[dict] = None
        self.__wheels: Dict[str, Magnebot.__Wheel] = dict()
        self.static_robot_info: Dict[int, BodyPartStatic] = dict()
        self.state: Optional[SceneState] = None

        # Commands to initialize objects.
        self._object_init_commands: Dict[int, List[dict]] = dict()

        # Cache static data.
        # self.static_object_info: Dict[int, StaticObjectInfo] = dict()
        # self.static_avatar_info: Dict[int, BodyPartStatic] = dict()

        # self.frame: Optional[FrameData] = None

        self.segmentation_color_to_id: Dict[int, int] = dict()

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

    def _add_object(self, model_name: str, position: Dict[str, float] = None,
                    rotation: Dict[str, float] = None, library: str = "models_core.json",
                    scale: Dict[str, float] = None, audio: ObjectInfo = None,
                    mass: float = None) -> None:
        """
        Add an object to the scene.

        :param model_name: The name of the model.
        :param position: The position of the model.
        :param rotation: The starting rotation of the model. Can be Euler angles or a quaternion.
        :param library: The path to the records file. If left empty, the default library will be selected.
                        See `ModelLibrarian.get_library_filenames()` and `ModelLibrarian.get_default_library()`.
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

    def init_scene(self, scene: str = None, layout: int = None, room: int = -1) -> None:
        self.__wheels: Dict[str, Magnebot.__Wheel] = dict()

        resp = self.communicate(self._get_scene_init_commands(scene=scene, layout=layout, room=room))
        # Cache the static robot data.
        static_robot = get_data(resp=resp, d_type=StaticRobot)
        for i in range(static_robot.get_num_joints()):
            body_part_id = static_robot.get_joint_id(i)
            self.static_robot_info[body_part_id] = BodyPartStatic(sr=static_robot, index=i)
            # Cache the wheels.
            body_part_name = static_robot.get_joint_name(i)
            if "wheel" in body_part_name:
                self.__wheels[body_part_name] = Magnebot.__Wheel(object_id=body_part_id, angle=0)
        self._set_state()

    def turn_by(self, angle: float, speed: float = 15, aligned_at: float = 3) -> ActionStatus:
        """
        Turn the Magnebot by an angle.
        The Magnebot will turn by small increments to align with the target angle.

        Possible [return values](action_status.md):

        - `success`
        - `too_many_attempts`
        - `unaligned`

        :param angle: The target angle in degrees. Positive value = clockwise turn.
        :param aligned_at: If the different between the current angle and the target angle is less than this value,
                            then the action is successful.
        :param speed: The wheels will turn this many degrees per attempt to turn.

        :return: An `ActionStatus` indicating if the Magnebot turned by the angle and if not, why.
        """

        def _get_angle_1() -> float:
            """
            :return: The current angle.
            """

            a = TDWUtils.get_angle_between(wheel_state.robot.forward, f0)
            if angle_0 < 0:
                a *= -1
            elif a > 180:
                a = 360 - a
            return a

        # The initial forward vector.
        f0 = self.state.robot.forward
        # The approximately number of iterations required, given the distance and speed.
        num_attempts = int(np.abs(angle) + 1) * speed * 50
        attempts = 0
        angle_0 = angle
        while attempts < num_attempts:
            attempts += 1
            # Set the direction of the wheels for the turn and send commands.
            commands = []
            for wheel in self.__wheels:
                if "left" in wheel:
                    self.__wheels[wheel].angle += speed if angle > 0 else -speed
                else:
                    self.__wheels[wheel].angle -= speed if angle > 0 else -speed
                commands.append({"$type": "set_revolute_target",
                                 "target": self.__wheels[wheel].angle,
                                 "joint_id": self.__wheels[wheel].object_id})
            resp = self.communicate(commands)

            # Wait until the wheels are done turning.
            wheels_done = False
            wheel_state = SceneState(resp=resp)
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

        Possible [return values](action_status.md):

        - `success`
        - `too_many_attempts`
        - `unaligned`

        :param target: Either the ID of an object or a Vector3 position.
        :param aligned_at: If the different between the current angle and the target angle is less than this value,
                            then the action is successful.
        :param speed: The wheels will turn this many degrees per attempt to turn.

        :return: An `ActionStatus` indicating if the Magnebot turned by the angle and if not, why.
        """

        if isinstance(target, int):
            target = self.state.objects[target].position
        elif isinstance(target, dict):
            target = TDWUtils.vector3_to_array(target)
        else:
            raise Exception(f"Invalid target: {target}")

        angle = TDWUtils.get_angle(forward=self.state.robot.forward, origin=self.state.robot.position,
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
        :param arrived_at: If at any point during the action the difference between the target distance and distance
                           traversed is less than this, then the action is successful.

        :return: An `ActionStatus` indicating if the Magnebot moved by `distance` and if not, why.
        """

        # The initial position of the robot.
        p0 = self.state.robot.position

        # Go until we've traversed the distance.
        d = 0
        # The approximately number of iterations required, given the distance and speed.
        num_attempts = int(np.abs(distance) + 1) * speed * 50
        attempts = 0
        while d < np.abs(distance) and attempts < num_attempts:
            # Move forward a bit and see if we've arrived.
            commands = []
            for wheel in ["wheel_left_front", "wheel_left_back", "wheel_right_front", "wheel_right_back"]:
                self.__wheels[wheel].angle += speed if distance > 0 else -speed
                commands.append({"$type": "set_revolute_target",
                                 "target": self.__wheels[wheel].angle,
                                 "joint_id": self.__wheels[wheel].object_id})
            resp = self.communicate(commands)
            # Wait for the wheels to stop turning.
            wheel_state = SceneState(resp=resp)
            wheels_turning = True
            while wheels_turning:
                wheels_turning, wheel_state = self._wheels_are_done(state_0=wheel_state)
                resp = self.communicate([])
            # Check if we're at the destination.
            p1 = SceneState(resp=resp).robot.position
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
        :param arrived_at: While moving, if at any point during the action the difference between the target distance
                           and distance traversed is less than this, then the action is successful.
        :param turn_speed: The Magnebot's wheels will rotate by this many degrees per iteration when turning.
        :param aligned_at: While turning, if the different between the current angle and the target angle is less than
                           this value, then the action is successful.
        :param move_on_turn_fail: If True, the Magnebot will move forward even if the internal `turn_to()` action
                                  didn't return `success`.

        :return: An `ActionStatus` indicating if the Magnebot moved to the target and if not, why.
        """

        # Turn to face the target.
        status = self.turn_to(target=target, speed=turn_speed, aligned_at=aligned_at)
        # Move to the target unless the turn failed (and if we care about the turn failing).
        if status == ActionStatus.success or move_on_turn_fail:
            if isinstance(target, int):
                target = self.state.objects[target].position
            elif isinstance(target, dict):
                target = TDWUtils.vector3_to_array(target)
            else:
                raise Exception(f"Invalid target: {target}")

            return self.move_by(distance=np.linalg.norm(self.state.robot.position - target), speed=move_speed,
                                arrived_at=arrived_at)
        else:
            self._set_state()
            return status

    def end(self) -> None:
        """
        End the simulation. Terminate the build process.
        """

        self.communicate({"$type": "terminate"})

    def _set_state(self):
        self.state = SceneState(resp=self.communicate([]))

    def _wheels_are_done(self, state_0: SceneState) -> Tuple[bool, SceneState]:
        """
        Advances one frame and then determines if the wheels are still turning.

        :param state_0: The scene state from the previous frame.

        :return: True if none of the wheels are tunring.
        """

        resp = self.communicate([])
        state_1 = SceneState(resp=resp)
        for wheel in self.__wheels:
            w_id = self.__wheels[wheel].object_id
            if np.linalg.norm(state_0.robot_joints[w_id].angles[0] - state_1.robot_joints[w_id].angles[0]) > 0.001:
                return False, state_1
        return True, state_1

    def _get_scene_init_commands(self, scene: str = None, layout: int = None, room: int = -1) -> List[dict]:
        commands = [{"$type": "load_scene",
                     "scene_name": "ProcGenScene"},
                    TDWUtils.create_empty_room(12, 12),
                    {"$type": "add_magnebot"},
                    {"$type": "send_robots",
                     "frequency": "always"},
                    {"$type": "send_transforms",
                     "frequency": "always"},
                    {"$type": "send_static_robots",
                     "frequency": "once"}]
        # Add the objects.
        for object_id in self._object_init_commands:
            commands.extend(self._object_init_commands[object_id])
        return commands
