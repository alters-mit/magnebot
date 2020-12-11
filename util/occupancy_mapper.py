from typing import List, Dict, Tuple
from pathlib import Path
from json import dumps
from PIL import ImageFont, ImageDraw
import numpy as np
from tdw.floorplan_controller import FloorplanController
from tdw.output_data import OutputData, Raycast, Images, ScreenPosition
from tdw.tdw_utils import TDWUtils
from magnebot.scene_environment import SceneEnvironment
from magnebot.constants import OCCUPANCY_CELL_SIZE
from magnebot.paths import OCCUPANCY_MAPS_DIRECTORY, ROOM_MAPS_DIRECTORY, SPAWN_POSITIONS_PATH
from magnebot.util import get_data


class OccupancyMapper(FloorplanController):
    """
    Create the occupancy maps and images of scenes.
    """

    @staticmethod
    def get_islands(occupancy_map: np.array) -> List[List[Tuple[int, int]]]:
        """
        :param occupancy_map: The occupancy map.

        :return: A list of all islands, i.e. continuous zones of traversability on the occupancy map.
        """

        # Positions that have been reviewed so far.
        traversed: List[Tuple[int, int]] = []
        islands: List[List[Tuple[int, int]]] = list()

        for ox, oy in np.ndindex(occupancy_map.shape):
            p = (ox, oy)
            if p in traversed:
                continue
            island = OccupancyMapper.get_island(occupancy_map=occupancy_map, p=p)
            if len(island) > 0:
                for island_position in island:
                    traversed.append(island_position)
                islands.append(island)
        return islands

    @staticmethod
    def get_island(occupancy_map: np.array, p: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Fill the island (a continuous zone) that position `p` belongs to.

        :param occupancy_map: The occupancy map.
        :param p: The position.

        :return: An island of positions as a list of (x, z) tuples.
        """

        to_check = [p]
        island: List[Tuple[int, int]] = list()
        while len(to_check) > 0:
            # Check the next position.
            p = to_check.pop(0)
            if p[0] < 0 or p[0] >= occupancy_map.shape[0] or p[1] < 0 or p[1] >= occupancy_map.shape[1] or \
                    occupancy_map[p[0]][p[1]] != 0 or p in island:
                continue
            # Mark the position as traversed.
            island.append(p)
            # Check these neighbors.
            px, py = p
            to_check.extend([(px, py + 1),
                             (px + 1, py + 1),
                             (px + 1, py),
                             (px + 1, py - 1),
                             (px, py - 1),
                             (px - 1, py - 1),
                             (px - 1, py),
                             (px - 1, py + 1)])
        return island

    @staticmethod
    def get_occupancy_position(scene_env: SceneEnvironment, ix: int, iy: int) -> Tuple[float, float]:
        """
        Convert an occupancy map position to a worldspace position.

        :param scene_env: The scene environment.

        :param ix: The x coordinate of the occupancy map position.
        :param iy: The y coordinate of the occupancy map position.

        :return: The `(x, z)` position in worldspace corresponding to `(ix, iy`) on the occupancy map.
        """

        return scene_env.x_min + (ix * OCCUPANCY_CELL_SIZE),  scene_env.z_min + (iy * OCCUPANCY_CELL_SIZE)

    def create(self) -> None:
        """
        Create the following:

        - Occupancy maps as numpy arrays.
        - Images of each occupancy map with markers showing which positions are navigable.
        - Images of each scene+layout combination.
        - Images of where the rooms are in a scene.
        - Spawn position data as a json file.
        """

        screen_width: int = 1280
        screen_height: int = 720

        # Set global variables.
        self.communicate([{"$type": "set_img_pass_encoding",
                           "value": False},
                          {"$type": "set_render_quality",
                           "render_quality": 5},
                          {"$type": "set_vignette",
                           "enabled": False},
                          {"$type": "set_screen_size",
                           "width": screen_width,
                           "height": screen_height},
                          {"$type": "set_shadow_strength",
                           "strength": 1.0}])

        scene_bounds: Dict[str, Dict[str, float]] = dict()
        font_size = 28
        font = ImageFont.truetype("fonts/inconsolata/Inconsolata_Expanded-Regular.ttf", font_size)

        floorplan_images_dir = str(Path("../doc/images/floorplans").resolve())
        occupancy_images_dir = str(Path("../doc/images/occupancy_maps").resolve())
        room_images_dir = Path("../doc/images/rooms")
        # Iterate through each scene and layout.
        spawn_positions = dict()
        for scene in ["1a", "1b", "1c", "2a", "2b", "2c", "4a", "4b", "4c", "5a", "5b", "5c"]:
            # Use just the number, i.e. "1" instead of "1a".
            scene_key = scene[0]
            if "a" in scene:
                spawn_positions[scene_key] = dict()
            for layout in [0, 1, 2]:
                occupancy_map = list()
                commands = self.get_scene_init_commands(scene=scene, layout=layout, audio=True)
                # Hide the roof and remove any existing position markers.
                commands.extend([{"$type": "set_floorplan_roof",
                                  "show": False},
                                 {"$type": "remove_position_markers"},
                                 {"$type": "simulate_physics",
                                  "value": True},
                                 {"$type": "send_environments"}])
                commands.extend(TDWUtils.create_avatar(position={"x": 0, "y": 31, "z": 0},
                                                       look_at=TDWUtils.VECTOR3_ZERO))
                commands.extend([{"$type": "set_pass_masks",
                                  "pass_masks": ["_img"]},
                                 {"$type": "send_images"}])
                # Send the commands.
                resp = self.communicate(commands)
                # Save the floorplan image.
                images = get_data(resp=resp, d_type=Images)
                TDWUtils.save_images(images=images, filename=f"{scene}_{layout}", output_directory=floorplan_images_dir,
                                     append_pass=False)

                # If this is a variant of the scene, don't bother creating a new occupancy map.
                if "a" not in scene:
                    continue

                spawn_positions[scene_key][layout] = dict()

                scene_env = SceneEnvironment(resp=resp)
                # Cache the environment data.
                if scene_key not in scene_bounds:
                    scene_bounds[scene_key] = {"x_min": scene_env.x_min,
                                               "x_max": scene_env.x_max,
                                               "z_min": scene_env.z_min,
                                               "z_max": scene_env.z_max}
                # Spherecast to each point.
                x = scene_env.x_min
                while x < scene_env.x_max:
                    z = scene_env.z_min
                    pos_row: List[int] = list()
                    while z < scene_env.z_max:
                        origin = {"x": x, "y": 4, "z": z}
                        destination = {"x": x, "y": -1, "z": z}
                        # Spherecast at the "cell".
                        resp = self.communicate({"$type": "send_spherecast",
                                                 "origin": origin,
                                                 "destination": destination,
                                                 "radius": OCCUPANCY_CELL_SIZE / 2})
                        # Get the y values of each position in the spherecast.
                        ys = []
                        hits = []
                        hit_objs = []
                        for j in range(len(resp) - 1):
                            raycast = Raycast(resp[j])
                            raycast_y = raycast.get_point()[1]
                            is_hit = raycast.get_hit() and (not raycast.get_hit_object() or raycast_y > 0.01)
                            if is_hit:
                                ys.append(raycast_y)
                                hit_objs.append(raycast.get_hit_object())
                            hits.append(is_hit)
                        # This position is outside the environment.
                        if len(ys) == 0 or len(hits) == 0 or len([h for h in hits if h]) == 0 or max(ys) > 2.8:
                            occupied = -1
                        else:
                            # This space is occupied if:
                            # 1. The spherecast hit any objects.
                            # 2. The surface is higher than floor level (such that carpets are ignored).
                            if any(hit_objs) and max(ys) > 0.03:
                                occupied = 1
                            # The position is free.
                            else:
                                occupied = 0
                        pos_row.append(occupied)
                        z += OCCUPANCY_CELL_SIZE
                    occupancy_map.append(pos_row)
                    x += OCCUPANCY_CELL_SIZE
                occupancy_map = np.array(occupancy_map)
                # Save the occupancy map.
                save_filename = f"{scene_key}_{layout}"
                np.save(str(OCCUPANCY_MAPS_DIRECTORY.joinpath(save_filename).resolve()), occupancy_map)

                # Sort the free positions of the occupancy map into continuous "islands".
                # Then, sort that list of lists by length.
                # The longest list is the biggest "island" i.e. the navigable area.
                non_navigable = list(sorted(OccupancyMapper.get_islands(occupancy_map=occupancy_map), key=len))[:-1]
                # Record non-navigable positions.
                for island in non_navigable:
                    for p in island:
                        occupancy_map[p[0]][p[1]] = 2

                # Define the room positions. This is the same for all layouts of the scene.
                if layout == 0:
                    rooms = np.zeros(shape=occupancy_map.shape, dtype=int)
                    for ix, iy in np.ndindex(occupancy_map.shape):
                        # Ignore positions outside of the scene.
                        if occupancy_map[ix, iy] == -1:
                            continue
                        # Get the room that this position is in.
                        for i, env in enumerate(scene_env.rooms):
                            x, z = OccupancyMapper.get_occupancy_position(scene_env=scene_env, ix=ix, iy=iy)
                            if env.is_inside(x, z):
                                rooms[ix, iy] = i
                                break
                    np.save(str(ROOM_MAPS_DIRECTORY.joinpath(str(scene_key)).resolve()), np.array(rooms))

                # Add position markers and create an occupancy image.
                commands = []
                for ix, iy in np.ndindex(occupancy_map.shape):
                    # Only include free positions
                    if occupancy_map[ix][iy] != 0:
                        continue
                    x, z = OccupancyMapper.get_occupancy_position(scene_env=scene_env, ix=ix, iy=iy)
                    commands.append({"$type": "add_position_marker",
                                     "position": {"x": x, "y": 0, "z": z},
                                     "scale": OCCUPANCY_CELL_SIZE,
                                     "color": {"r": 0, "g": 0, "b": 1, "a": 1},
                                     "shape": "cube"})
                commands.append({"$type": "send_images"})
                resp = self.communicate(commands)
                images = get_data(resp=resp, d_type=Images)
                TDWUtils.save_images(images=images, filename=save_filename, output_directory=occupancy_images_dir,
                                     append_pass=False)

                if layout == 0:
                    # Create room images.
                    positions = list()
                    position_ids = list()
                    # Remove the position markers.
                    # Disable physics. We'll use cube primitives for our markers and we don't want them to jostle.
                    commands = [{"$type": "remove_position_markers"},
                                {"$type": "simulate_physics",
                                 "value": False}]
                    for i in range(len(scene_env.rooms)):
                        position = TDWUtils.array_to_vector3(scene_env.rooms[i].center)
                        # Create a cube per room. Set the position and scale to match the room center and bounds.
                        commands.extend([{"$type": "load_primitive_from_resources",
                                          "primitive_type": "Cube",
                                          "id": i,
                                          "position": position},
                                         {"$type": "scale_object",
                                          "id": i,
                                          "scale_factor": {"x": scene_env.rooms[i].bounds[0],
                                                           "y": 4,
                                                           "z": scene_env.rooms[i].bounds[2]}},
                                         {"$type": "set_color",
                                          "color": {"r": 0, "g": 0, "b": 0.75, "a": 1.0},
                                          "id": i}])
                        positions.append(position)
                        position_ids.append(i)
                        i += 1
                    # Convert the center position of each room to screenspace coordinates.
                    commands.extend([{"$type": "send_screen_positions",
                                      "positions": positions,
                                      "position_ids": position_ids},
                                     {"$type": "set_pass_masks",
                                      "pass_masks": ["_img"]},
                                     {"$type": "send_images"}])
                    resp = c.communicate(commands)
                    images = get_data(resp=resp, d_type=Images)
                    screen_positions = dict()
                    for j in range(len(resp) - 1):
                        r_id = OutputData.get_data_type_id(resp[j])
                        # Get the screenspace coordinates of the center of each room.
                        if r_id == "scre":
                            screen_position = ScreenPosition(resp[j])
                            screen_positions[screen_position.get_id()] = screen_position.get_screen()
                    # Convert the image to a PIL image.
                    pil_image = TDWUtils.get_pil_image(images=images, index=0)
                    draw = ImageDraw.Draw(pil_image)
                    # Draw the room ID in the center of each room.
                    for position_id in screen_positions:
                        p = (screen_positions[position_id][0],
                             screen_height - screen_positions[position_id][1] - (font_size / 2))
                        draw.text(p, str(position_id), font=font, anchor="mb")
                    # Save the room image.
                    pil_image.save(str(room_images_dir.joinpath(save_filename + ".jpg")), "JPEG")

                # Get the spawn positions for each room.
                room_id = 0
                for room in scene_env.rooms:
                    # Get the free position on the map closest to the center of the room.
                    min_distance = 1000
                    min_position = None
                    for ix, iy in np.ndindex(occupancy_map.shape):
                        if occupancy_map[ix, iy] == 0:
                            x, z = OccupancyMapper.get_occupancy_position(scene_env=scene_env, ix=ix, iy=iy)
                            pos = np.array([x, 0, z])
                            d = np.linalg.norm(pos - room.center)
                            if d < min_distance:
                                min_distance = d
                                min_position = pos
                    # Add the free position closest to the center as a spawn position.
                    spawn_positions[scene_key][layout][room_id] = TDWUtils.array_to_vector3(min_position)
                    room_id += 1
        # Save the spawn position data.
        SPAWN_POSITIONS_PATH.write_text(dumps(spawn_positions, indent=2, sort_keys=True))
        self.communicate({"$type": "terminate"})


if __name__ == "__main__":
    c = OccupancyMapper(launch_build=False)
    c.create()
