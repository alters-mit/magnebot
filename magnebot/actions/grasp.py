from enum import Enum
from json import loads
from typing import List, Dict
import numpy as np
from tdw.tdw_utils import TDWUtils
from tdw.output_data import OutputData, Bounds, Raycast, SegmentationColors, Magnebot
from magnebot.arm import Arm
from magnebot.util import get_data
from magnebot.ik.orientation_mode import OrientationMode
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.action_status import ActionStatus
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.image_frequency import ImageFrequency
from magnebot.actions.ik_motion import IKMotion
from magnebot.paths import CONVEX_SIDES_PATH


class _GraspStatus(Enum):
    getting_bounds = 1,
    spherecasting = 2
    raycasting = 4
    grasping = 8


class Grasp(IKMotion):
    """
    Try to grasp a target object.
    The action ends when either the Magnebot grasps the object, can't grasp it, or fails arm articulation.
    """

    # A list of indices of convex sides per object. See: `_BOUNDS_SIDES`.
    _CONVEX_SIDES: Dict[str, List[int]] = loads(CONVEX_SIDES_PATH.read_text(encoding="utf-8"))
    # The order of bounds sides. The values in `_CONVEX_SIDES` correspond to indices in this list.
    _BOUNDS_SIDES: List[str] = ["left", "right", "front", "back", "top", "bottom"]

    def __init__(self, target: int, arm: Arm, orientation_mode: OrientationMode, target_orientation: TargetOrientation,
                 dynamic: MagnebotDynamic):
        """
        :param target: The ID of the target object.
        :param arm: [The arm used for this action.](../arm.md)
        :param orientation_mode: [The orientation mode.](../ik/orientation_mode.md)
        :param target_orientation: [The target orientation.](../ik/target_orientation.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        """

        super().__init__(arm=arm, orientation_mode=orientation_mode, target_orientation=target_orientation,
                         dynamic=dynamic)
        self._target: int = target
        self._grasp_status: _GraspStatus = _GraspStatus.getting_bounds
        self._target_bounds: Dict[str, np.array] = dict()
        self._target_name: str = ""
        self._target_position: np.array = np.array([0, 0, 0])

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        # This Magnebot is already holding the object.
        if self._target in dynamic.held[Arm.left] or self._target in dynamic.held[Arm.right]:
            self.status = ActionStatus.success
            return []
        # Check if another Magnebot is holding the object.
        for i in range(len(resp) - 1):
            r_id = OutputData.get_data_type_id(resp[i])
            if r_id == "magn":
                magnebot = Magnebot(resp[i])
                if magnebot.get_id() != static.robot_id:
                    if self._target in magnebot.get_held_left() or self._target in magnebot.get_held_right():
                        self.status = ActionStatus.held_by_other
                        return []
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        commands.extend([{"$type": "set_magnet_targets",
                          "arm": self._arm.name,
                          "targets": [self._target],
                          "id": static.robot_id},
                         {"$type": "send_bounds",
                          "frequency": "once"},
                         {"$type": "send_segmentation_colors",
                          "frequency": "once"}])
        return commands

    def get_end_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                         image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_end_commands(resp=resp, static=static, dynamic=dynamic, image_frequency=image_frequency)
        commands.append({"$type": "set_magnet_targets",
                         "arm": self._arm.name,
                         "targets": [],
                         "id": static.robot_id})
        return commands

    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        if self._is_success(resp=resp, static=static, dynamic=dynamic):
            self.status = ActionStatus.success
            return []
        elif self._grasp_status == _GraspStatus.grasping:
            return self._evaluate_arm_articulation(resp=resp, static=static, dynamic=dynamic)
        elif self._grasp_status == _GraspStatus.getting_bounds:
            # Get the segmentation color data and get the object name.
            segmentation_colors = get_data(resp=resp, d_type=SegmentationColors)
            for i in range(segmentation_colors.get_num()):
                if segmentation_colors.get_object_id(i) == self._target:
                    self._target_name = segmentation_colors.get_object_name(i).lower()
                    break
            # Get the bounds data and spherecast to the center.
            bounds = get_data(resp=resp, d_type=Bounds)
            for i in range(bounds.get_num()):
                if bounds.get_id(i) == self._target:
                    self._target_bounds = {"left": bounds.get_left(i),
                                           "right": bounds.get_right(i),
                                           "front": bounds.get_front(i),
                                           "back": bounds.get_back(i),
                                           "top": bounds.get_top(i),
                                           "bottom": bounds.get_bottom(i),
                                           "center": bounds.get_center(i)}
                    self._grasp_status = _GraspStatus.spherecasting
                    return [{"$type": "send_spherecast",
                             "radius": 0.2,
                             "origin": TDWUtils.array_to_vector3(dynamic.joints[static.magnets[self._arm]].position),
                             "destination": TDWUtils.array_to_vector3(bounds.get_center(0)),
                             "id": static.robot_id}]
            raise Exception(f"No bounds data: {resp}")
        elif self._grasp_status == _GraspStatus.spherecasting:
            magnet_position = dynamic.joints[static.magnets[self._arm]].position
            # Get the nearest spherecasted point.
            nearest_distance = np.inf
            nearest_position = np.array([0, 0, 0])
            got_raycast_point = False
            for i in range(len(resp) - 1):
                r_id = OutputData.get_data_type_id(resp[i])
                if r_id == "rayc":
                    raycast = Raycast(resp[i])
                    if raycast.get_raycast_id() == static.robot_id:
                        # Ignore raycasts that didn't hit the target.
                        if not raycast.get_hit() or not raycast.get_hit_object() or raycast.get_object_id() != self._target:
                            continue
                        got_raycast_point = True
                        point = np.array(raycast.get_point())
                        raycast_distance = np.linalg.norm(point - magnet_position)
                        if raycast_distance < nearest_distance:
                            nearest_distance = raycast_distance
                            nearest_position = point
            # We found a good target!
            if got_raycast_point:
                self._target_position = self._absolute_to_relative(position=nearest_position, dynamic=dynamic)
                self._set_start_arm_articulation_commands(static=static, dynamic=dynamic)
                self._grasp_status = _GraspStatus.grasping
                return self._evaluate_arm_articulation(resp=resp, static=static, dynamic=dynamic)
            # Try to get a target from cached bounds data.
            else:
                # If we haven't cached the bounds for this object, just return all of the sides.
                if self._target_name not in Grasp._CONVEX_SIDES:
                    sides = list(self._target_bounds.values())[:-1]
                else:
                    # Get only the convex sides of the object using cached data.
                    sides: List[np.array] = list()
                    for i, side in enumerate(Grasp._BOUNDS_SIDES):
                        if i in Grasp._CONVEX_SIDES[self._target_name]:
                            sides.append(self._target_bounds[side])
                # If there are no valid bounds sides, aim for the center and hope for the best.
                if len(sides) == 0:
                    self._target_position = self._absolute_to_relative(position=self._target_bounds["center"],
                                                                       dynamic=dynamic)
                    self._set_start_arm_articulation_commands(static=static, dynamic=dynamic)
                    self._grasp_status = _GraspStatus.grasping
                    return self._evaluate_arm_articulation(resp=resp, static=static, dynamic=dynamic)
                else:
                    # If the object is higher up than the magnet, remove the lowest side.
                    if self._target_bounds["center"][1] > magnet_position[1] and len(sides) > 1:
                        lowest: int = -1
                        y = np.inf
                        for i in range(len(sides)):
                            if sides[i][1] < y:
                                lowest = i
                                y = sides[i][1]
                        del sides[lowest]
                    # Get the closest side to the magnet.
                    nearest_side: np.array = sides[0]
                    d = np.inf
                    for side in sides:
                        dd = np.linalg.norm(side - magnet_position)
                        if dd < d:
                            nearest_side = side
                            d = dd
                    self._grasp_status = _GraspStatus.raycasting
                    return [{"$type": "send_raycast",
                             "origin": TDWUtils.array_to_vector3(nearest_side),
                             "destination": TDWUtils.array_to_vector3(self._target_bounds["center"]),
                             "id": static.robot_id}]
        elif self._grasp_status == _GraspStatus.raycasting:
            for i in range(len(resp) - 1):
                r_id = OutputData.get_data_type_id(resp[i])
                if r_id == "rayc":
                    raycast = Raycast(resp[i])
                    if raycast.get_raycast_id() == static.robot_id:
                        # If the raycast hit the object, aim for that point.
                        if raycast.get_hit() and raycast.get_hit_object() and raycast.get_object_id() == self._target:
                            self._target_position = self._absolute_to_relative(dynamic=dynamic,
                                                                               position=np.array(raycast.get_point()))
                            self._set_start_arm_articulation_commands(static=static, dynamic=dynamic)
                            self._grasp_status = _GraspStatus.grasping
                            return self._evaluate_arm_articulation(resp=resp, static=static, dynamic=dynamic)
                        else:
                            self._target_position = self._absolute_to_relative(position=self._target_bounds["center"],
                                                                               dynamic=dynamic)
                            self._set_start_arm_articulation_commands(static=static, dynamic=dynamic)
                            self._grasp_status = _GraspStatus.grasping
                            return self._evaluate_arm_articulation(resp=resp, static=static, dynamic=dynamic)
            self._target_position = self._absolute_to_relative(position=self._target_bounds["center"],
                                                               dynamic=dynamic)
            self._set_start_arm_articulation_commands(static=static, dynamic=dynamic)
            self._grasp_status = _GraspStatus.grasping
            return self._evaluate_arm_articulation(resp=resp, static=static, dynamic=dynamic)
        else:
            raise Exception(self._grasp_status)

    def _get_fail_status(self) -> ActionStatus:
        return ActionStatus.failed_to_grasp

    def _is_success(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> bool:
        return self._target in dynamic.held[self._arm]

    def _get_ik_target_position(self) -> np.array:
        return self._target_position
