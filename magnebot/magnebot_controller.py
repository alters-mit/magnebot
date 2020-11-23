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
    # Global forward directional vector.
    _FORWARD = np.array([0, 0, 1])

    # Load default audio values for objects.
    __OBJECT_AUDIO = PyImpact.get_object_info()

    def __init__(self, port: int = 1071, launch_build: bool = True, id_pass: bool = True,
                 screen_width: int = 256, screen_height: int = 256):
        super().__init__(port=port, launch_build=launch_build)

        self._id_pass = id_pass

        # Create an empty occupancy map.
        self.occupancy_map: Optional[np.array] = None
        self._scene_bounds: Optional[dict] = None
        self.__wheels_targets: Dict[str, float] = dict()
        self.__wheels: Dict[str, int] = dict()
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
        self.__wheels_targets: Dict[str, float] = dict()
        self.__wheels: Dict[str, int] = dict()

        self._add_object("basket_18inx18inx12iin",
                         scale={"x": 0.6, "y": 0.4, "z": 0.6},
                         position={"x": -1.195, "y": 0, "z": 0.641},
                         mass=1)
        self._add_object("jug05",
                         position={"x": 0.215, "y": 0, "z": 3.16})

        resp = self.communicate(self._get_scene_init_commands(scene=scene, layout=layout, room=room))
        # Cache the static robot data.
        static_robot = get_data(resp=resp, d_type=StaticRobot)
        for i in range(static_robot.get_num_body_parts()):
            body_part_id = static_robot.get_body_part_id(i)
            self.static_robot_info[body_part_id] = BodyPartStatic(sr=static_robot, index=i)
            # Cache the wheels.
            body_part_name = static_robot.get_body_part_name(i)
            if "wheel" in body_part_name:
                self.__wheels[body_part_name] = body_part_id
                self.__wheels_targets[body_part_name] = 0
        self._set_state()

    def move_by(self, distance: float, speed: float = 5, not_turning_at: float = 0.05, overshot_at: float = 0.1,
                num_attempts: int = 50) -> ActionStatus:
        # The initial position of the robot.
        p0 = self.state.robot.position

        # Go until we've traversed the distance.
        d = 0
        attempts = 0
        while d < distance and attempts < num_attempts:
            commands = []
            for wheel in ["wheel_left_front", "wheel_left_back", "wheel_right_front", "wheel_right_back"]:
                self.__wheels_targets[wheel] += speed
                commands.append({"$type": "set_revolute_target",
                                 "target": self.__wheels_targets[wheel],
                                 "joint_id": self.__wheels[wheel]})
            resp = self.communicate(commands)
            while self._wheels_are_turning(resp=resp, not_turning_at=not_turning_at):
                resp = self.communicate([])
            p1 = SceneState(resp=resp).robot.position
            d = np.linalg.norm(p1 - p0)
            attempts += 1
        self._set_state()
        if np.abs(distance - d) > overshot_at:
            return ActionStatus.overshot_move
        elif attempts >= num_attempts:
            return ActionStatus.too_many_attempts
        else:
            return ActionStatus.success

    def turn_by(self, angle: float, speed: float = 5, not_turning_at: float = 0.05,
                num_attempts: int = 50) -> ActionStatus:
        f0 = self.state.robot.forward
        attempts = 0
        while attempts < num_attempts:
            commands = []
            for wheel in self.__wheels:
                if angle > 1:
                    if "left" in wheel:
                        wheel_direction = 1
                    else:
                        wheel_direction = -1
                else:
                    if "left" in wheel:
                        wheel_direction = -1
                    else:
                        wheel_direction = 1
                self.__wheels_targets[wheel] += speed * wheel_direction
                commands.append({"$type": "set_revolute_target",
                                 "target": self.__wheels_targets[wheel],
                                 "joint_id": self.__wheels[wheel]})
            resp = self.communicate(commands)
            while self._wheels_are_turning(resp=resp, not_turning_at=not_turning_at):
                resp = self.communicate([])
            state = SceneState(resp=resp)
            angle_1 = TDWUtils.get_angle_between(f0, state.robot.forward)
            if angle_1 >= angle:
                self._set_state()
                return ActionStatus.success
            attempts += 1
        self._set_state()
        return ActionStatus.too_many_attempts

    def turn_to(self, target: Union[int, Dict[str, float]], speed: float = 5, not_turning_at: float = 0.05,
                num_attempts: int = 50) -> ActionStatus:
        if isinstance(target, int):
            target = self.state.objects[target].position
        elif isinstance(target, dict):
            target = TDWUtils.vector3_to_array(target)
        else:
            raise Exception(f"Invalid target: {target}")
        angle = TDWUtils.get_angle(forward=self.state.robot.forward, origin=self.state.robot.position,
                                   position=target)
        return self.turn_by(angle=angle, speed=speed, not_turning_at=not_turning_at, num_attempts=num_attempts)

    def _set_state(self):
        self.state = SceneState(resp=self.communicate([]))

    def _wheels_are_turning(self, resp: List[bytes], not_turning_at: float) -> bool:
        """
        :param resp: The response from the build.
        :param not_turning_at: If the angular velocity of any wheel is over this, the wheels are still turning.

        :return: True if any of the robot's wheels are still turning.
        """

        state = SceneState(resp=resp)
        for wheel in self.__wheels:
            if np.linalg.norm(state.robot_body_parts[self.__wheels[wheel]].angular_velocity) > not_turning_at:
                print(np.linalg.norm(state.robot_body_parts[self.__wheels[wheel]].angular_velocity), not_turning_at)
                return True
        return False

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


if __name__ == "__main__":
    c = Magnebot(launch_build=False)
    c.init_scene()
    print(c.move_by(2))
