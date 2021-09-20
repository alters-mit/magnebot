import numpy as np
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.step_physics import StepPhysics
from tdw.add_ons.object_manager import ObjectManager
from tdw.add_ons.collision_manager import CollisionManager
from magnebot import Magnebot, ActionStatus


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
m1.collision_detection.previous_was_same = False
m1.move_to(object_ids[0])
while m1.action.status == ActionStatus.ongoing:
    c.communicate([])
print(m0.action.status)
print(m1.action.status)
c.communicate({"$type": "terminate"})
