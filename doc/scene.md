# Scene Setup

By default, the Magnebot API has two options for initializing a scene:

- `self.init_scene()` will load an empty test room
- `self.init_floorplan_scene(scene, layout, room)` will load an interior environment and populate with objects

Both actions will add a Magnebot, cache static data, and so on.

## Custom Scene Setup

Most scene setup logic is handled in the backend function `self._init_scene()` (note the extra `_`). This function should always be called in any scene setup function. It can't (and shouldn't) be overridden. `self._init_scene()` has the following parameters:

| Parameter         | Type             | Default | Description                                                  |
| ----------------- | ---------------- | ------- | ------------------------------------------------------------ |
| scene             | List[dict]       |         | A list of commands to initialize the scene.                  |
| post_processing   | List[dict]       | None    | A list of commands to set post-processing values. Can be None. |
| end               | List[dict]       | None    | A list of commands sent at the end of scene initialization (on the same frame). Can be None. |
| magnebot_position | Dict[str, float] | None    | The position of the Magnebot. If None, defaults to `{"x": 0, "y": 0, "z": 0}`. |

### The `scene` parameter

If you're loading a streamed scene, this can be a list that just contains `self.get_add_scene()`, a function that is deliberately not listed in the Magnebot API but is part of the base class Controller API. To learn how to get a list of all available scenes, [read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/librarian/scene_librarian.md).

```python
from magnebot import Magnebot

class MyMagnebot(Magnebot):
    def my_init_scene(self):
        scene = [self.get_add_scene(scene_name="floorplan_1a")]
        self._init_scene(scene=scene)


if __name__ == "__main__":
    m = MyMagnebot()
    m.my_init_scene()
```

You can also create an empty test room:

```python
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot

class MyMagnebot(Magnebot):
    def my_init_scene(self):
        scene = [{"$type": "load_scene", 
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12)]
        self._init_scene(scene=scene)
        
       
if __name__ == "__main__":
    m = MyMagnebot()
    m.my_init_scene()
```

[This is an example in the Magnebot API that adds a nice-looking floor to a test room.](https://github.com/alters-mit/magnebot/blob/main/controllers/promos/reach_high.py) [You can generate much more elaborate scenes in TDW using the same commands.](https://github.com/threedworld-mit/tdw/blob/master/Python/example_controllers/proc_gen_room.py)  Most scene setup recipes that would work in TDW will work in the Magnebot API. The keys differences are that:

- All scene setup commands must be in the same list and sent as the `scene` parameter of `self._init_scene()`
- Add additional avatars with `self.add_camera()`
- Object initialization commands shouldn't be in the same list as scene initialization commands (see below)
- The Magnebot API works best if the floor is level

### The `post_processing` parameter

Add a list of post-processing commands here. You can use default commands via `self._get_post_processing_commands()`:

```python
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot

class MyMagnebot(Magnebot):
    def my_init_scene(self):
        scene = [{"$type": "load_scene",
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12)]
        self._init_scene(scene=scene,
                         post_processing=self._get_post_processing_commands())
        
        
if __name__ == "__main__":
    m = MyMagnebot()
    m.my_init_scene()
```

[This is a list of post-processing commands.](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md#postprocesscommand) You could feasibly set other global values within this list, but be aware that this list is sent prior to adding the Magnebot, camera, and objects to the scene.

If you're using a test scene, you might not want to enable post-processing, in which case you should omit this parameter (it will default to None).

### The `end` parameter

Add miscellaneous commands to the end of the list of scene initialization commands. This is a good way of modifying object data i.e. applying a force to an object (see below for how to add objects). If you don't need to add any extra commands, omit this parameter (it will default to None).

### The `magnebot_position` parameter

Set where in the scene the Magnebot will spawn. If you omit this parameter, it will default to `{"x": 0, "y": 0, "z": 0}`

## Object initialization

The backend `self._init_scene()` function automatically adds objects from the dictionary `self._object_init_commands`. In this dictionary, the key is the ID of the new object and the value is a list of initialization commands.

There are many ways to add objects to TDW, and there are several similarly-named wrapper functions in the Controller class. We recommend you *don't* use those wrappers in the Magnebot API. Instead, use `self._add_object()`. This wrapper function will automatically set an objects mass, friction values, etc. and add its ID and commands to`self._object_init_commands`. It returns an object ID:

```python
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot

class MyMagnebot(Magnebot):
    def __init__(self, port: int = 1071):
        super().__init__(port=port)
        self.target_object_id = -1

    def my_init_scene(self):
        self.target_object_id = self._add_object(model_name="rh10",
                                                 position={"x": 3, "y": 0, "z": -4.5},
                                                 rotation={"x": 0, "y": 34, "z": 0},
                                                 scale={"x": 1, "y": 1, "z": 1},
                                                 library="models_core.json")
        scene = [{"$type": "load_scene",
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12)]
        self._init_scene(scene=scene,
                         post_processing=self._get_post_processing_commands())


if __name__ == "__main__":
    m = MyMagnebot()
    m.my_init_scene()
    m.move_to(m.target_object_id)
```

If you want to manually set the physics values of the object, you can do so via the optional `audio` parameter. (This parameter doesn't actually mean that the simulation will generate audio or use audio data in any way; it just uses a data structure that has a few audio-specific parameters, namely `amp` and `resonance`.)

```python
from tdw.tdw_utils import TDWUtils
from tdw.py_impact import ObjectInfo, AudioMaterial
from magnebot import Magnebot

class MyMagnebot(Magnebot):
    def __init__(self, port: int = 1071):
        super().__init__(port=port)
        self.target_object_id = -1

    def my_init_scene(self):
        audio = ObjectInfo(name="rh10",
                           library="models_core.json",
                           mass=8,
                           bounciness=0.6,
                           resonance=0.65,
                           amp=0.1,
                           material=AudioMaterial.metal)
        self.target_object_id = self._add_object(model_name="rh10",
                                                 position={"x": 3, "y": 0, "z": -4.5},
                                                 rotation={"x": 0, "y": 34, "z": 0},
                                                 scale={"x": 1, "y": 1, "z": 1},
                                                 library="models_core.json",
                                                 audio=audio)
        scene = [{"$type": "load_scene",
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12)]
        self._init_scene(scene=scene)


if __name__ == "__main__":
    m = MyMagnebot()
    m.my_init_scene()
    m.move_to(m.target_object_id)
```

But this is a lot more complicated than it needs to be because `rh10` *does* have default values. And because this scene setup happens to be identical to `self.init_scene()`, you can collapse the above example into a much smaller example that leaves a lot of default parameters as-is and doesn't even define a new action:

```python
from magnebot import Magnebot, ActionStatus

class MyMagnebot(Magnebot):
    def __init__(self, port: int = 1071):
        super().__init__(port=port)
        self.target_object_id = -1

    def init_scene(self) -> ActionStatus:
        self.target_object_id = self._add_object(model_name="rh10",
                                                 position={"x": 3, "y": 0, "z": -4.5},
                                                 rotation={"x": 0, "y": 34, "z": 0})
        return super().init_scene()


if __name__ == "__main__":
    m = MyMagnebot()
    m.my_init_scene()
    m.move_to(m.target_object_id)
```

You can add more [object initialization commands](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md#objectcommand) after calling `self._add_object()` by appending them to the list. For example, if you want to make the object kinematic so that it doesn't respond to physics:

```python
from magnebot import Magnebot, ActionStatus

class MyMagnebot(Magnebot):
    def __init__(self, port: int = 1071):
        super().__init__(port=port)
        self.target_object_id = -1

    def init_scene(self) -> ActionStatus:
        self.target_object_id = self._add_object(model_name="rh10",
                                                 position={"x": 3, "y": 0, "z": -4.5},
                                                 rotation={"x": 0, "y": 34, "z": 0})
        self._object_init_commands[self.target_object_id].append({"$type": "set_kinematic_state",
                                                                  "id": self.target_object_id,
                                                                  "is_kinematic": True,
                                                                  "use_gravity": False})
        return super().init_scene()


if __name__ == "__main__":
    m = MyMagnebot()
    m.my_init_scene()
    m.move_to(m.target_object_id)
```

## Limitations

- **You should only create objects within your scene initialization function.** Once you call `self._init_scene()`, it will clear any previous static data and cache new static data. It will also request output data. If you add objects *afterwards*, they won't appear in `self.objects_static` or `self.state`!
- `self.init_floorplan_scene()` is fairly difficult to modify because the floorplan data is stored in the `tdw` repo, not the `magnebot` repo. We recommend that you don't modify it and instead use the above examples as a template for more complex scenes.