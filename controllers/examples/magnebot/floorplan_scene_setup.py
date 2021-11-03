from json import loads
from tdw.controller import Controller
from tdw.add_ons.step_physics import StepPhysics
from tdw.add_ons.object_manager import ObjectManager
from tdw.add_ons.floorplan import Floorplan
from magnebot import Magnebot
from magnebot.paths import SPAWN_POSITIONS_PATH
from magnebot.util import get_default_post_processing_commands


"""
Add a Magnebot to a floorplan scene.
"""

spawn_positions = loads(SPAWN_POSITIONS_PATH.read_text())

# Scene 1a, layout 0, room 2.
scene = "1a"
layout = 0
magnebot_position = spawn_positions["1"]["0"]["2"]

c = Controller()
magnebot = Magnebot(position=magnebot_position)
objects = ObjectManager()
step_physics = StepPhysics(num_frames=10)
floorplan = Floorplan()
floorplan.init_scene(scene=scene, layout=layout)
c.add_ons.extend([floorplan, magnebot, objects, step_physics])

c.communicate(get_default_post_processing_commands())

print(magnebot.dynamic.transform.position)
for object_id in objects.transforms:
    print(object_id, objects.transforms[object_id].position)
c.communicate({"$type": "terminate"})
