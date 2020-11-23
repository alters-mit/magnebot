import numpy as np
from typing import List, Dict, Type, TypeVar, Optional
from tdw.floorplan_controller import FloorplanController
from tdw.output_data import OutputData, Transforms, Rigidbodies, Bounds, Images, SegmentationColors, Volumes, Raycast, \
    CompositeObjects, CameraMatrices, Environments, Overlap, Version, StaticRobot
from tdw.tdw_utils import TDWUtils
from tdw.object_init_data import AudioInitData
from tdw.py_impact import PyImpact, ObjectInfo
from tdw.release.pypi import PyPi
from magnebot.body_part_static import BodyPartStatic


class Magnebot(FloorplanController):
    T = TypeVar("T", bound=OutputData)
    # Output data types mapped to their IDs.
    _OUTPUT_IDS: Dict[Type[OutputData], str] = {Transforms: "tran",
                                                Rigidbodies: "rigi",
                                                Bounds: "boun",
                                                Images: "imag",
                                                SegmentationColors: "segm",
                                                Volumes: "volu",
                                                Raycast: "rayc",
                                                CompositeObjects: "comp",
                                                CameraMatrices: "cama",
                                                Environments: "envi",
                                                Overlap: "over",
                                                Version: "vers",
                                                StaticRobot: "srob"}
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
        self.__wheels_target: float = 0
        self.__wheels: Dict[str, int] = dict()
        self.static_robot_info: Dict[int, BodyPartStatic] = dict()

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
            version = Magnebot._get_data(resp=resp, d_type=Version)
            build_version = version.get_tdw_version()
            python_version = PyPi.get_installed_tdw_version(truncate=True)
            if build_version != python_version:
                print(f"Your installed version of tdw ({python_version}) doesn't match the version of the build "
                      f"{build_version}. This might cause errors!")

    @staticmethod
    def _get_data(resp: List[bytes], d_type: Type[T]) -> Optional[T]:
        """
        Parse the output data list of byte arrays to get a single type output data object.

        :param resp: The response from the build (a byte array).
        :param d_type: The desired type of output data.

        :return: An object of type `d_type` from `resp`. If there is no object, returns None.
        """

        if d_type not in Magnebot._OUTPUT_IDS:
            raise Exception(f"Output data ID not defined: {d_type}")

        for i in range(len(resp) - 1):
            r_id = OutputData.get_data_type_id(resp[i])
            if r_id == Magnebot._OUTPUT_IDS[d_type]:
                return d_type(resp[i])
        return None

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
        self.__wheels_target: float = 0
        self.__wheels: Dict[str, int] = dict()

        self._add_object("basket_18inx18inx12iin",
                         scale={"x": 0.6, "y": 0.4, "z": 0.6},
                         position={"x": -1.195, "y": 0, "z": 0.641},
                         mass=1)
        self._add_object("jug05",
                         position={"x": 0.215, "y": 0, "z": 3.16})

        resp = self.communicate(self._get_scene_init_commands(scene=scene, layout=layout, room=room))

        # Cache the static robot data.
        static_robot = self._get_data(resp=resp, d_type=StaticRobot)
        for i in range(static_robot.get_num_body_parts()):
            body_part_id = static_robot.get_body_part_id(i)
            self.static_robot_info[body_part_id] = BodyPartStatic(sr=static_robot, index=i)
            # Cache the wheels.
            body_part_name = static_robot.get_body_part_name(i)
            if "wheel" in body_part_name:
                self.__wheels[body_part_name] = body_part_id

    def move_by(self, distance: float) -> None:
        commands = []
        for wheel in ["wheel_left_front", "wheel_left_back", "wheel_right_front", "wheel_right_back"]:
            commands.append({"$type": "set_revolute_target",
                             "target": self.__wheels_target,
                             "joint_id": self.__wheels[wheel]})
        self.communicate(commands)
        for i in range(10):
            self.communicate([])
        self.__wheels_target += 5

    def _get_scene_init_commands(self, scene: str = None, layout: int = None, room: int = -1) -> List[dict]:
        commands = [{"$type": "load_scene",
                     "scene_name": "ProcGenScene"},
                    TDWUtils.create_empty_room(12, 12),
                    {"$type": "add_magnebot"},
                    {"$type": "send_robots",
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

    for q in range(5):
        c.move_by(2)

