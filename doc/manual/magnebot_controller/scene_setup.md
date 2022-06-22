##### MagnebotController

# Scene Setup

By default, the [`MagnebotController`](../../api/magnebot_controller.md) has two options for initializing a scene:

- `self.init_scene()` will load an empty 12x12 meter test room:

```python
from magnebot import MagnebotController

c = MagnebotController()
c.init_scene()
print(c.magnebot.dynamic.transform.position)
c.end()
```

- `self.init_floorplan_scene(scene, layout, room)` will load an interior environment and populate with objects. 

```python
from magnebot import MagnebotController

c = MagnebotController()
c.init_floorplan_scene(scene="1a", layout=0, room=0)
print(c.magnebot.dynamic.transform.position)
c.end()
```

Both actions will add a Magnebot, cache static data, and so on.

[**Images of the floorplans can be found here.**](https://github.com/alters-mit/magnebot/tree/main/doc/images/floorplans) 

[**Images of the floorplan rooms can be found here.**](https://github.com/alters-mit/magnebot/tree/main/doc/images/rooms) 

## Custom Scene Setup

Most scene setup logic is handled in the backend function `self._init_scene()` (note the extra `_`). This function should always be called in any scene setup function. It can't (and shouldn't) be overridden. `self._init_scene()` has the following parameters:

| Parameter         | Type             | Default | Description                                                  |
| ----------------- | ---------------- | ------- | ------------------------------------------------------------ |
| scene             | List[dict]       |         | A list of commands to initialize the scene.                  |
| post_processing   | List[dict]       | None    | A list of commands to set post-processing values. Can be None. |
| end               | List[dict]       | None    | A list of commands sent at the end of scene initialization (on the same frame). Can be None. |
| magnebot_position | Dict[str, float] | None    | The position of the Magnebot. If None, defaults to `{"x": 0, "y": 0, "z": 0}`. |

### The `scene` parameter

*For more information regarding TDW scenes in general, [read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/core_concepts/scenes.md).*

*For more information regarding TDW scene setup concepts, [read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/scene_setup/overview.md).*

If you're loading a streamed scene, this can be a list that just contains `self.get_add_scene()`, a function that is deliberately not listed in the Magnebot API but is  part of the base class Controller API:

```python
from magnebot import MagnebotController

class MyController(MagnebotController):
    def init_scene(self):
        scene = [self.get_add_scene(scene_name="floorplan_1a")]
        self._init_scene(scene=scene)


if __name__ == "__main__":
    c = MyController()
    c.init_scene()
```

You can also create an empty test room:

```python
from tdw.tdw_utils import TDWUtils
from magnebot import MagnebotController

class MyController(MagnebotController):
    def init_scene(self):
        scene = [{"$type": "load_scene", 
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12)]
        self._init_scene(scene=scene)


if __name__ == "__main__":
    c = MyController()
    c.init_scene()
```

Most scene setup recipes that would work in TDW will work in the Magnebot API. The keys differences are that:

- All scene setup commands must be in the same list and sent as the `scene` parameter of `self._init_scene()`
- Object initialization commands shouldn't be in the same list as scene initialization commands (see below)
- The Magnebot API works best if the floor is level

### The `post_processing` parameter

Add a list of post-processing commands here. You can use default commands via `magnebot.util.get_default_post_processing_commands()`:

```python
from tdw.tdw_utils import TDWUtils
from magnebot import MagnebotController
from magnebot.util import get_default_post_processing_commands

class MyMagnebot(MagnebotController):
    def init_scene(self):
        scene = [{"$type": "load_scene",
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12)]
        self._init_scene(scene=scene,
                         post_processing=get_default_post_processing_commands())


if __name__ == "__main__":
    c = MyMagnebot()
    c.init_scene()
```

If you're using a test scene, you might not want to enable  post-processing, in which case you should omit this parameter (it will  default to None).

### The `objects` parameter

*For more information regarding TDW objects, [read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/core_concepts/objects.md).*

*For more information regarding TDW object physics values, [read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/physx/physics_objects.md).*

This is a list of commands for object initialization. You can add objects at any time to the scene but the output data will initialize correctly if all objects are added in this list of commands.

This example creates a simple 12x12 meter test scene and adds a rocking horse object:

```python
from tdw.tdw_utils import TDWUtils
from magnebot import MagnebotController


class MyController(MagnebotController):
    def init_scene(self):
        scene = [{"$type": "load_scene",
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12)]
        objects = []
        objects.extend(self.get_add_physics_object(model_name="rh10",
                                                   position={"x": 0.04, "y": 0, "z": 1.081},
                                                   object_id=self.get_unique_id()))
        self._init_scene(scene=scene, objects=objects)


if __name__ == "__main__":
    c = MyController()
    c.init_scene()
```

### The `end` parameter

Add miscellaneous commands to the end of the list of scene  initialization commands. This is a good way of modifying object data  i.e. applying a force to an object (see below for how to add objects).  If you don't need to add any extra commands, omit this parameter (it  will default to None).

### The `position` and `rotation` parameters

These set the starting position and rotation of the Magnebot. Their default values are `{"x": 0, "y": 0, "z": 0}`.

```python
from tdw.tdw_utils import TDWUtils
from magnebot import MagnebotController

class MyController(MagnebotController):
    def init_scene(self):
        scene = [{"$type": "load_scene",
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12)]
        self._init_scene(scene=scene,
                         position={"x": 1, "y": 0, "z": -3},
                         rotation={"x": 0, "y": 46, "z": 0})


if __name__ == "__main__":
    c = MyController()
    c.init_scene()
```

***

**Next: [Output data](output_data.md)**

[Return to the README](../../../README.md)

***

Example controllers:

- [custom_scene_setup.py](https://github.com/alters-mit/magnebot/blob/main/controllers/examples/magnebot_controller/custom_scene_setup.py) Define a custom scene setup.
