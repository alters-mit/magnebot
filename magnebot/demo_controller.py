import numpy as np
from typing import Dict, List, Union
from pathlib import Path
from bresenham import bresenham
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

    def __init__(self, port: int = 1071, launch_build: bool = True, screen_width: int = 256, screen_height: int = 256,
                 debug: bool = False, images_directory: str = "images"):
        super().__init__(port=port, launch_build=launch_build, screen_width=screen_width, screen_height=screen_height,
                         auto_save_images=False, debug=debug, images_directory=images_directory)

        self._image_directories: Dict[str, Path] = dict()
        self._create_images_directory(avatar_id="a")

        self._image_count = 0

    def add_camera(self, position: Dict[str, float], rotation: Dict[str, float] = None,
                   look_at: bool = True, follow: bool = False, camera_id: str = "c") -> ActionStatus:
        """
        See: [`Magnebot.add_camera()`](magnebot_controller.md#add_camera).

        Adds some instructions to render images per-frame.
        """

        self._create_images_directory(avatar_id=camera_id)
        status = super().add_camera(position=position, rotation=rotation, look_at=look_at, follow=follow,
                                    camera_id=camera_id)
        # Always save images.
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
        # Save all images.
        for i in range(len(resp) - 1):
            r_id = OutputData.get_data_type_id(resp[i])
            if r_id == "imag":
                images = Images(resp[i])
                TDWUtils.save_images(filename=TDWUtils.zero_padding(self._image_count, 8),
                                     output_directory=self._image_directories[images.get_avatar_id()],
                                     images=images)
        self._image_count += 1
        return resp

    def navigate(self, target: Dict[str, float]) -> ActionStatus:
        """
        Navigate to the target position by following a path of waypoints.

        The path is generated using Unity's NavMesh. Then, each corner of the path is snapped to the occupancy map. Then, the Magnebot goes to each position using a `move_to()` action.

        This isn't in the main `Magnebot` API because it's actually quite naive and won't work in many cases! For example:

        - It doesn't account for objects moving in the scene after scene initialization.
        - The waypoints are always centerpoints of occupancy map positions.
        - Because waypoints are rather naively snapped to occupancy map positions, it is possible for this action to report that there is no path when there actually is one.

        But for the purposes of generating a demo of the Magnebot API, this action is good enough!

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_move`
        - `failed_to_turn`
        - `no_path`

        :param target: The target destination.

        :return: An `ActionStatus` indicating if the Magnebot arrived at the destination and if not, why.
        """

        self._start_action()
        # Set the path origin to the current position of the Magnebot.
        origin = TDWUtils.array_to_vector3(self.state.magnebot_transform.position)

        # Get a path to the target using the Unity NavMesh.
        resp = self.communicate([{"$type": "send_nav_mesh_path",
                                  "origin": origin,
                                  "destination": target}])
        nav_mesh_path = get_data(resp=resp, d_type=NavMeshPath).get_path()
        path: List[Dict[str, float]] = list()
        occupancy_path: List[np.array] = list()
        # For every node on the path, constrain it to the nearest position on the occupancy map.
        # This prevents the Magnebot from hugging corners that it will get caught on.
        for i, node in enumerate(nav_mesh_path):
            # Get the position of the origin on the occupancy map.
            min_distance = np.inf
            waypoint = None
            for ix, iy in np.ndindex(self.occupancy_map.shape):
                if self.occupancy_map[ix][iy] != 0:
                    continue
                # Draw a line from the position to the target.
                # If there are any obstacles in the way, ignore this position.
                if nav_mesh_path[i - 1] is not None and len(occupancy_path) > 0:
                    ignore = False
                    # Draw a line from the previous waypoint to this waypoint.
                    for line_node in bresenham(occupancy_path[i - 1][0], occupancy_path[i - 1][1], ix, iy):
                        if self.occupancy_map[line_node[0]][line_node[1]] != 0:
                            ignore = True
                            break
                    if ignore:
                        continue
                # Get the distance to this position. If it is the closest to `position`, mark it as such.
                x, z = self.get_occupancy_position(ix, iy)
                p = np.array([x, 0, z])
                d = np.linalg.norm(p - node)
                if d < min_distance:
                    min_distance = d
                    waypoint = np.array([ix, iy])
            # If we couldn't find a valid waypoint near the NavMesh position, end the action.
            if waypoint is None:
                self._end_action()
                return ActionStatus.no_path
            # Record the waypoint occupancy map position. We'll use this to draw a Bresenham line.
            occupancy_path.append(waypoint)
            # Convert the occupancy map position to a worldspace position.
            x, z = self.get_occupancy_position(waypoint[0], waypoint[1])
            if i > 0:
                path.append({"x": x, "y": 0, "z": z})
        # If there isn't a path, we're probably already at the destination.
        if len(path) == 0:
            self._end_action()
            return ActionStatus.success
        # Go to each waypoint.
        for waypoint in path:
            status = self.move_to(target=waypoint)
            if status != ActionStatus.success:
                return status
        return ActionStatus.success

    def _get_scene_init_commands(self, magnebot_position: Dict[str, float]) -> List[dict]:
        commands = super()._get_scene_init_commands(magnebot_position=magnebot_position)
        # Hide the roof.
        commands.append({"$type": "set_floorplan_roof",
                         "show": False})
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
