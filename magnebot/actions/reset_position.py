from enum import Enum
from typing import List, Dict
import numpy as np
from tdw.output_data import Transforms
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.occupancy_map import OccupancyMap
from magnebot.action_status import ActionStatus
from magnebot.util import get_data
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.image_frequency import ImageFrequency
from magnebot.actions.action import Action
from magnebot.constants import OCCUPANCY_CELL_SIZE


class _ResetPositionStatus(Enum):
    waiting_for_objects = 1
    initializing_occupancy_map = 2
    generating_occupancy_map = 4
    getting_position = 8


class ResetPosition(Action):
    """
    Reset the Magnebot so that it isn't tipping over.
    This will rotate the Magnebot to the default rotation (so that it isn't tipped over) and move the Magnebot to the nearest empty space on the floor.
    It will also drop any held objects.

    This will be interpreted by the physics engine as a _very_ sudden and fast movement.
    This action should only be called if the Magnebot is a position that will prevent the simulation from continuing (for example, if the Magnebot fell over).
    """

    _CELL_SIZE = OCCUPANCY_CELL_SIZE * 2

    def __init__(self):
        """
        (no parameterS)
        """

        super().__init__()

        # Objects that were formerly held by the Magnebot. We need to wait for this to finish moving.
        # Key = Object ID. Value = Position.
        self._formerly_held_objects: Dict[int, np.array] = dict()
        # Wait a few frames before checking on the object.
        self._initial_frames: int = 0
        self._drop_frames: int = 0
        # Use an occupancy map to reset the position.
        self._occupancy_map: OccupancyMap = OccupancyMap(cell_size=ResetPosition._CELL_SIZE)
        self._reset_position_status: _ResetPositionStatus = _ResetPositionStatus.waiting_for_objects

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        has_tipped, tipping = self._is_tipping(dynamic=dynamic)
        if not has_tipped and not tipping:
            self.status = ActionStatus.cannot_reset_position
            return []
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        # Drop all held objects.
        held_objects: List[int] = list()
        for arm in dynamic.held:
            for object_id in dynamic.held[arm]:
                o_id = int(object_id)
                commands.append({"$type": "detach_from_magnet",
                                 "id": static.robot_id,
                                 "arm": arm.name,
                                 "object_id": o_id})
                held_objects.append(o_id)
        # Stop the wheels.
        for wheel in static.wheels:
            commands.append({"$type": "set_revolute_target",
                             "id": static.robot_id,
                             "target": float(dynamic.joints[static.wheels[wheel]].angles[0]),
                             "joint_id": static.wheels[wheel]})
        # Make the Magnebot movable.
        commands.append({"$type": "set_immovable",
                         "id": static.robot_id,
                         "immovable": False})
        if len(held_objects) > 0:
            # Get the positions of each object.
            transforms = get_data(resp=resp, d_type=Transforms)
            for i in range(transforms.get_num()):
                o_id = transforms.get_id(i)
                if o_id in held_objects:
                    self._formerly_held_objects[o_id] = np.array(transforms.get_position(i))
        else:
            self._reset_position_status = _ResetPositionStatus.initializing_occupancy_map
        return commands

    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        if self._reset_position_status == _ResetPositionStatus.waiting_for_objects:
            # Wait a few frames.
            if self._initial_frames < 5:
                self._initial_frames += 1
                return []
            # Continue to wait for the objects to fall.
            else:
                # Stop a possible infinite wait.
                if self._drop_frames >= 200:
                    self._reset_position_status = _ResetPositionStatus.initializing_occupancy_map
                # Continue to wait for the objects to fall.
                else:
                    self._drop_frames += 1
                    transforms = get_data(resp=resp, d_type=Transforms)
                    moving = False
                    # Get the updated positions of the objects and compare them to the current position.
                    for i in range(transforms.get_num()):
                        o_id = transforms.get_id(i)
                        if o_id in self._formerly_held_objects:
                            p1 = np.array(transforms.get_position(i))
                            d = np.linalg.norm(self._formerly_held_objects[o_id] - p1)
                            self._formerly_held_objects[o_id] = np.array([p1[0], p1[1], p1[2]])
                            # Stop if the object somehow fell below the floor or if the object isn't moving.
                            if self._formerly_held_objects[o_id][1] > -1 and d > 0.01:
                                moving = True
                                break
                    if moving:
                        return []
                    else:
                        self._reset_position_status = _ResetPositionStatus.initializing_occupancy_map
        # Initialize the occupancy map.
        if self._reset_position_status == _ResetPositionStatus.initializing_occupancy_map:
            self._occupancy_map.initialized = True
            self._reset_position_status = _ResetPositionStatus.generating_occupancy_map
            return self._occupancy_map.get_initialization_commands()
        # Generate the occupancy map but ignore this Magnebot.
        elif self._reset_position_status == _ResetPositionStatus.generating_occupancy_map:
            # This will set the scene bounds.
            self._occupancy_map.on_send(resp=resp)
            # Return commands to generate the occupancy map.
            self._occupancy_map.generate(ignore_objects=static.body_parts)
            self._reset_position_status = _ResetPositionStatus.getting_position
            return self._occupancy_map.commands
        # Get a position to reset to.
        elif self._reset_position_status == _ResetPositionStatus.getting_position:
            # This will set the occupancy map.
            self._occupancy_map.on_send(resp=resp)
            # Get the nearest position.
            position = dynamic.transform.position
            position[1] = 0
            closest = np.array([0, 0, 0])
            closest_distance = np.inf
            # Get the nearest unoccupied position.
            for ix, iy in np.ndindex(self._occupancy_map.occupancy_map.shape):
                # Ignore non-free positions or positions at the edges of the scene.
                if self._occupancy_map.occupancy_map[ix][iy] != 0:
                    continue
                x = self._occupancy_map.scene_bounds.x_min + (ix * ResetPosition._CELL_SIZE)
                z = self._occupancy_map.scene_bounds.z_min + (iy * ResetPosition._CELL_SIZE)
                p = np.array([x, 0, z])
                d = np.linalg.norm(position - p)
                if d < closest_distance:
                    closest_distance = d
                    closest = p
            self.status = ActionStatus.success
            # Teleport the robot and make it immovable.
            return [{"$type": "teleport_robot",
                     "id": static.robot_id,
                     "position": TDWUtils.array_to_vector3(closest)},
                    {"$type": "set_immovable",
                     "id": static.robot_id,
                     "immovable": True}]
        else:
            raise Exception(f"Not defined: {self._reset_position_status}")
