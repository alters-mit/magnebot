from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.step_physics import StepPhysics
from tdw.add_ons.object_manager import ObjectManager
from magnebot import Magnebot
from magnebot.util import get_default_post_processing_commands


"""
Create an empty room, add an object, and add a Magnebot.
"""

c = Controller()
magnebot = Magnebot()
objects = ObjectManager()
step_physics = StepPhysics(num_frames=10)
c.add_ons.extend([magnebot, objects, step_physics])

commands = [{"$type": "load_scene",
             "scene_name": "ProcGenScene"},
            TDWUtils.create_empty_room(12, 12)]
commands.extend(c.get_add_physics_object(model_name="rh10",
                                         position={"x": -2, "y": 0, "z": -1.5},
                                         object_id=c.get_unique_id()))
commands.extend(get_default_post_processing_commands())
c.communicate(commands)
print(magnebot.dynamic.transform.position)
for object_id in objects.transforms:
    print(object_id, objects.transforms[object_id].position)
c.communicate({"$type": "terminate"})
