import numpy as np
from typing import Dict, List, Union
from pathlib import Path
from tdw.output_data import NavMeshPath
from tdw.tdw_utils import TDWUtils
from tdw.output_data import OutputData, Images
from magnebot.magnebot_controller import Magnebot
from magnebot.action_status import ActionStatus
from magnebot.util import get_data


class DemoController(Magnebot):
    """
    `DemoController` is used to generate demo videos of the Magnebot API. It is a superclass of [`Magnebot`](magnebot_controller.md) that adds the following functionality:

    - Instead of saving images at the end of every action, they are saved every frame.
    - The roof is removed from the scene.
    - There is a `navigate()` action.

    Most users shouldn't use this controller for the following reasons:

    - Saving every image per frame is _very_ slow.
    - `navigate()` isn't sufficiently reliable (see notes below).
    """

    def __init__(self, port: int = 1071, launch_build: bool = True, screen_width: int = 1024, screen_height: int = 1024,
                 debug: bool = False, images_directory: str = "images", image_pass_only: bool = False):
        super().__init__(port=port, launch_build=launch_build, screen_width=screen_width, screen_height=screen_height,
                         auto_save_images=False, debug=debug, images_directory=images_directory)

        self._image_directories: Dict[str, Path] = dict()
        self._create_images_directory(avatar_id="a")
        self.image_pass_only = image_pass_only

        self._image_count = 0

    def add_camera(self, position: Dict[str, float], roll: float = 0, pitch: float = 0, yaw: float = 0,
                   look_at: bool = True, follow: bool = False, camera_id: str = "c") -> ActionStatus:
        """
        See: [`Magnebot.add_camera()`](magnebot_controller.md#add_camera).

        Adds some instructions to render images per-frame.
        """

        self._create_images_directory(avatar_id=camera_id)
        status = super().add_camera(position=position, roll=roll, pitch=pitch, yaw=yaw, look_at=look_at, follow=follow,
                                    camera_id=camera_id)
        # Always save images.
        if not self._debug:
            self._per_frame_commands.extend([{"$type": "enable_image_sensor",
                                              "enable": True},
                                             {"$type": "send_images"}])
        return status

    def communicate(self, commands: Union[dict, List[dict]]) -> List[bytes]:
        """
        See [`Magnebot.communicate()`](magnebot_controller.md#communicate).

        Images are saved per-frame.
        """

        resp = super().communicate(commands=commands)
        if not self._debug:
            # Save all images.
            got_images = False
            for i in range(len(resp) - 1):
                r_id = OutputData.get_data_type_id(resp[i])
                if r_id == "imag":
                    got_images = True
                    images = Images(resp[i])
                    TDWUtils.save_images(filename=TDWUtils.zero_padding(self._image_count, 8),
                                         output_directory=self._image_directories[images.get_avatar_id()],
                                         images=images)
            if got_images:
                self._image_count += 1
        return resp

    def _get_scene_init_commands(self, magnebot_position: Dict[str, float] = None) -> List[dict]:
        commands = super()._get_scene_init_commands(magnebot_position=magnebot_position)
        # Hide the roof.
        commands.append({"$type": "set_floorplan_roof",
                         "show": False})
        if self.image_pass_only:
            commands.append({"$type": "set_pass_masks",
                             "pass_masks": ["_img"]})
        # Create NavMesh obstacles from all non-kinematic objects.
        obstacle_commands: List[dict] = list()
        for cmd in commands:
            if cmd["$type"] == "set_kinematic_state" and not cmd["is_kinematic"]:
                obstacle_commands.append({"$type": "make_nav_mesh_obstacle",
                                          "id": cmd["id"],
                                          "carve_type": "stationary"})
        commands.extend(obstacle_commands)
        return commands

    def _create_images_directory(self, avatar_id: str) -> None:
        """
        :param avatar_id: The ID of the avatar.

        :return: An images directory for the avatar.
        """

        # Build the images directory.
        a_dir = self.images_directory.joinpath(avatar_id)
        if not a_dir.exists():
            a_dir.mkdir(parents=True)
        self._image_directories[avatar_id] = a_dir
