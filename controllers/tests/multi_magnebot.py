from enum import Enum
from typing import List, Dict
import numpy as np
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.step_physics import StepPhysics
from tdw.add_ons.object_manager import ObjectManager
from tdw.add_ons.collision_manager import CollisionManager
from tdw.output_data import OutputData, Robot
from magnebot import Magnebot, ActionStatus, ImageFrequency, Arm


RNG = np.random.RandomState(0)


class MetaState(Enum):
    navigation = 1
    arm_articulation = 2
    avoidance = 4


class NavigationState(Enum):
    idle = 1
    moving_to_target = 2
    grasping_target_object = 8
    resetting_arm = 16
    moving_to_center = 32


class AvoidanceState(Enum):
    none = 1
    turning = 2
    moving = 4


class Navigator(Magnebot):
    def __init__(self, target_object: int, robot_id: int = 0, position: Dict[str, float] = None, rotation: Dict[str, float] = None,
                 image_frequency: ImageFrequency = ImageFrequency.once):
        super().__init__(robot_id=robot_id, position=position, rotation=rotation,
                         image_frequency=image_frequency)
        self.target_object: int = target_object
        self.navigation_state: NavigationState = NavigationState.idle
        self.avoidance_state: AvoidanceState = AvoidanceState.none

    def on_send(self, resp: List[bytes]) -> None:
        super().on_send(resp=resp)

        # Get the position of the other Magnebot.
        other_magnebot_position: np.array = np.array([0, 0, 0])
        for i in range(len(resp) - 1):
            r_id = OutputData.get_data_type_id(resp[i])
            if r_id == "robo":
                robot = Robot(resp[i])
                if robot.get_id() != self.static.robot_id:
                    other_magnebot_position = np.array(robot.get_position())
                    break

        # If the other Magnebot is too close, stop moving and try to avoid it.
        if np.linalg.norm(self.dynamic.transform.position - other_magnebot_position) < 0.6 and not self.dynamic.immovable:
            if RNG.random() < 0.5:
                self.turn_by(60)
            else:
                self.turn_by(-60)
            self.avoidance_state = AvoidanceState.turning
            return
        # Continue to turn to avoid the other Magnebot.
        elif self.avoidance_state == AvoidanceState.turning:
            # Done turning. Start backing away.
            if self.dynamic.status != ActionStatus.ongoing:
                # Find a direction of movement that moves this Magnebot further away from the other Magnebot.
                positive_vector = self.dynamic.transform.position + self.dynamic.transform.forward
                negative_vector = self.dynamic.transform.position - self.dynamic.transform.forward
                if np.linalg.norm(positive_vector - other_magnebot_position) < np.linalg.norm(
                        negative_vector - other_magnebot_position):
                    distance = -1.5
                else:
                    distance = 1.5
                # Start to move to avoid the other Magnebot.
                self.move_by(distance)
                self.avoidance_state = AvoidanceState.moving
            else:
                return
        # Continue to move to avoid the other Magnebot.
        elif self.avoidance_state == AvoidanceState.moving:
            # Resume basic navigation.
            if self.dynamic.status != ActionStatus.ongoing:
                self.avoidance_state = AvoidanceState.none
                if self.navigation_state == NavigationState.moving_to_target:
                    self.move_to(target=self.target_object)
                elif self.navigation_state == NavigationState.moving_to_center:
                    self.move_to(target=np.array([0, 0, 0]))
            else:
                return

        # Start to move to the object.
        if self.navigation_state == NavigationState.idle:
            self.navigation_state = NavigationState.moving_to_target
            self.move_to(target=self.target_object)
        elif self.navigation_state == NavigationState.moving_to_target:
            # Start to grasp the target object.
            if self.action.status == ActionStatus.success:
                self.grasp(target=self.target_object, arm=Arm.left)
                self.navigation_state = NavigationState.grasping_target_object
            # Try to move again.
            elif self.action.status != ActionStatus.ongoing:
                self.move_to(target=self.target_object)
        elif self.navigation_state == NavigationState.grasping_target_object:
            # We're holding the target. Reset the arm.
            if self.dynamic.status == ActionStatus.success:
                self.navigation_state = NavigationState.resetting_arm
                self.reset_arm(arm=Arm.left)
            # If we failed to grasp the object, try moving to the object again.
            elif self.dynamic.status != ActionStatus.ongoing:
                self.navigation_state = NavigationState.moving_to_target
                self.move_to(target=self.target_object)
        elif self.navigation_state == NavigationState.resetting_arm:
            # If we reset the arm, return home.
            if self.dynamic.status != ActionStatus.ongoing:
                self.navigation_state = NavigationState.moving_to_center
                self.move_to(target=np.array([0, 0, 0]))


c = Controller(check_version=False, launch_build=False)

commands = [TDWUtils.create_empty_room(12, 12)]
# Add ten objects to the scene in a ring.
num_objects = 10
d_theta = 360 / num_objects
theta = d_theta / 2
pos = np.array([3.5, 0, 0])
origin = np.array([0, 0, 0])
object_ids = list()
for j in range(num_objects):
    object_id = Controller.get_unique_id()
    object_ids.append(object_id)
    object_position = TDWUtils.rotate_position_around(origin=origin, position=pos, angle=theta)
    commands.extend(Controller.get_add_physics_object(model_name="jug05",
                                                      object_id=object_id,
                                                      position=TDWUtils.array_to_vector3(object_position)))
    theta += d_theta
m0 = Magnebot(position={"x": 0, "y": 0, "z": -1.5},
              robot_id=0)
m1 = Magnebot(position={"x": 0, "y": 0, "z": 1},
              rotation={"x": 0, "y": 180, "z": 0},
              robot_id=1)
step_physics = StepPhysics(num_frames=10)
objects = ObjectManager(transforms=True, rigidbodies=False, bounds=False)
collisions = CollisionManager(objects=True, environment=True, enter=True, exit=True)
c.add_ons.extend([m0, m1, step_physics, objects, collisions])
c.communicate(commands)
m0.move_by(3)
m1.turn_by(-123)

# m0 collides with m1.
while m0.action.status == ActionStatus.ongoing:
    c.communicate([])
# m0 backs up.
m0.collision_detection.objects = False
m0.move_by(-2)
while m0.action.status == ActionStatus.ongoing:
    c.communicate([])
print(m0.action.status)
print(m1.action.status)
c.communicate({"$type": "terminate"})
