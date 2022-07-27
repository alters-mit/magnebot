##### Magnebot

# Scene Setup

*For more information regarding TDW scene setup strategies, [read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/scene_setup/overview.md).*

By design, scene setup for a [`Magnebot`](../../api/magnebot.md) can be much more complicated than scene setup for a [`MagnebotController`](../../api/magnebot_controller.md). This is intentional; the `Magnebot` agent is meant to be usable in *any* TDW controller.

## Add Magnebot to a minimal scene

This is a minimal example of how to create a scene and add a `Magnebot` agent:

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot

c = Controller()
m = Magnebot()
c.add_ons.append(m)
c.communicate(TDWUtils.create_empty_room(12, 12))
print(m.dynamic.transform.position)
c.communicate({"$type": "terminate"})
```

This will set the initial position and rotation of the Magnebot:

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot

c = Controller()
m = Magnebot(position={"x": 1, "y": 0, "z": -2},
             rotation={"x": 0, "y": 30, "z": 0})
c.add_ons.append(m)
c.communicate(TDWUtils.create_empty_room(12, 12))
print(m.dynamic.transform.position)
c.communicate({"$type": "terminate"})
```

To replicate `MagnebotController.init_scene()` we need to add a few more things:

- A `load_scene` command to totally re-load the scene (this isn't necessary for a minimal example but it's useful for when you want to reset the scene)
- An [`ObjectManager`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/add_ons/object_manager.md) add-on to cache static object data and manage dynamic object data per-frame.
- A [`StepPhysics`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/add_ons/step_physics.md) add-on to skip *n* frames per communicate call.
- Post-processing commands

This controller adds a Magnebot and an object to a scene:

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.step_physics import StepPhysics
from tdw.add_ons.object_manager import ObjectManager
from magnebot import Magnebot
from magnebot.util import get_default_post_processing_commands

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
```

## Add Magnebot to floorplan scene

You can also add a Magnebot to a floorplan scene by adding a [`Floorplan`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/add_ons/floorplan.md). You can spawn the Magnebot in a given room by reading the spawn positions data file. Note that `floorplan` is first in the `add_ons` array; this is because add-ons are read sequentially. You must initialize the scene before adding the Magnebot.

```python
from json import loads
from tdw.controller import Controller
from tdw.add_ons.step_physics import StepPhysics
from tdw.add_ons.object_manager import ObjectManager
from tdw.add_ons.floorplan import Floorplan
from magnebot import Magnebot
from magnebot.paths import SPAWN_POSITIONS_PATH

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

c.communicate([])

print(magnebot.dynamic.transform.position)
for object_id in objects.transforms:
    print(object_id, objects.transforms[object_id].position)
c.communicate({"$type": "terminate"})
```

[**Images of the floorplans can be found here.**](https://github.com/alters-mit/magnebot/tree/main/doc/images/floorplans) 

[**Images of the floorplan rooms can be found here.**](https://github.com/alters-mit/magnebot/tree/main/doc/images/rooms) 

## Reset a scene

*For more information regarding how to reset a scene, [read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/scene_setup_high_level/reset_scene.md).*

When resetting a scene, be sure to call `magnebot.reset(position, rotation)`. If you're using an object manager, set `object_manager.initialized = False`.

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.object_manager import ObjectManager
from magnebot import Magnebot

class ResetScene(Controller):
    def __init__(self, port: int = 1071, check_version: bool = True, launch_build: bool = True):
        super().__init__(port=port, check_version=check_version, launch_build=launch_build)
        self.position = {"x": 1, "y": 0, "z": -2}
        self.rotation = {"x": 0, "y": 30, "z": 0}
        self.magnebot: Magnebot = Magnebot(position=self.position,
                                           rotation=self.rotation)
        self.object_manager: ObjectManager = ObjectManager()
        self.add_ons.extend([self.magnebot, self.object_manager])
    
    def init_scene(self):
        self.magnebot.reset(position=self.position, rotation=self.rotation)
        self.object_manager.initialized = False
        self.communicate([{"$type": "load_scene",
                           "scene_name": "ProcGenScene"},
                          TDWUtils.create_empty_room(12, 12)])
```

***

**Next: [Output data](output_data.md)**

[Return to the README](../../../README.md)

***

Example controllers:

- [minimal_scene_setup.py](https://github.com/alters-mit/magnebot/blob/main/controllers/examples/magnebot/minimal_scene_setup.py) Create an empty room, add an object, and add a Magnebot.
- [floorplan_scene_setup.py](https://github.com/alters-mit/magnebot/blob/main/controllers/examples/magnebot/floorplan_scene_setup.py) Add a Magnebot to a floorplan scene.
