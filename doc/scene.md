# Scene Setup

## Option A: Using the `Magnebot` agent

The [`Magnebot` agent](api/magnebot.md) is a standard [TDW add-on](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/add_ons/add_on.md) that can be added to a Controller.

[Read the objects and scenes tutorial](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/objects_and_scenes/overview.md) for a guide to basic scene setup.

In addition to the tutorials recommendations, you should consider adding the following to a Magnebot simulation (though none of this is strictly required):

- Add objects with [`AudioInitData`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/api/object_init_data.md) to initialize the object with default physics values.
- Add an [`ObjectManager`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/api/add_ons/object_manager.md) to organize object output data.
- Add a [`CollisionManager`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/api/add_ons/collision_manager.md) to organize collision data.
- Add a [`SkipFrames`](api/skip_frames.md) to skip a certain number of frames per step; the Magnebot API has been optimized to skip 10 frames per step (in other words, there will be 11 physics frames per `communicate()` call).

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.object_manager import ObjectManager
from tdw.add_ons.collision_manager import CollisionManager
from tdw.object_init_data import AudioInitData
from magnebot import Magnebot, ActionStatus
from magnebot.image_frequency import ImageFrequency
from magnebot.skip_frames import SkipFrames

c = Controller()

# Add the object manager (this is optional).
om = ObjectManager(transforms=True, rigidbodies=False, bounds=False)
# Add the collision manager (this is optional).
co = CollisionManager(enter=True, exit=True, stay=False)
# Skip 10 frames per step (this is optional).
sk = SkipFrames(num_frames=10)
# Add the Magnebot (this is NOT optional).
m = Magnebot(position={"x": 0, "y": 0, "z": 0},
             rotation={"x": 0, "y": 0, "z": 0},
             robot_id=0,
             image_frequency=ImageFrequency.once)
c.add_ons.extend([om, co, sk, m])

# Get commands to add an object.
object_init_data = AudioInitData(name="rh10",
                                 position={"x": 3, "y": 0, "z": -4.5},
                                 rotation={"x": 0, "y": 34, "z": 0},
                                 scale_factor={"x": 1, "y": 1, "z": 1})
object_id, object_commands = object_init_data.get_commands()

commands = [TDWUtils.create_empty_room(12, 12)]
commands.extend(object_commands)
# Make the object kinematic.
commands.append({"$type": "set_kinematic_state",
                 "id": object_id,
                 "is_kinematic": True,
                 "use_gravity": False})

# Send the commands. This will also send commands to add the Magnebot, ObjectManager, CollisionManager, and SkipFrames.
c.communicate(commands)

# Start moving the Magnebot.
m.move_by(2)
while m.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate({"$type": "terminate"})
```

## Option B: Using the `MagnebotController`

### Default scene setup options

By default, the [`MagnebotController`](api/magnebot_controller.md) has two options for initializing a scene:

- `self.init_scene()` will load an empty test room
- `self.init_floorplan_scene(scene, layout, room)` will load an interior environment and populate with objects

Both actions will add a Magnebot, cache static data, and so on.

### Custom scene setup

Most scene setup logic is handled in the backend function `self._init_scene()` (note the extra `_`). This function should always be called in any scene setup function. It can't (and shouldn't) be overridden. `self._init_scene()` has the following parameters:

| Parameter         | Type             | Default | Description                                                  |
| ----------------- | ---------------- | ------- | ------------------------------------------------------------ |
| scene             | List[dict]       |         | A list of commands to initialize the scene. If you're loading a streamed scene, this can be a list that just contains `self.get_add_scene()`, a function that is deliberately not listed in the Magnebot API but is part of the base class Controller API. To learn how to get a list of all available scenes, [read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/librarian/scene_librarian.md).                 |
| post_processing   | List[dict]       | None    | A list of commands to set post-processing values. Can be None. To get the list of default post-processing commands, call `self._get_default_post_processing_commands()`. [This is a list of post-processing commands.](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md#postprocesscommand) |
| end               | List[dict]       | None    | A list of commands sent at the end of scene initialization (on the same frame). Can be None. This is a good way of modifying object data i.e. applying a force to an object (see below for how to add objects). |
| position | Dict[str, float] | None    | The position of the Magnebot. If None, defaults to `{"x": 0, "y": 0, "z": 0}`. |

The backend `self._init_scene()` function automatically adds objects from the dictionary `self._object_init_commands`. In this dictionary, the key is the ID of the new object and the value is a list of initialization commands.

There are many ways to add objects to TDW, and there are several similarly-named wrapper functions in the Controller class. We recommend you *don't* use those wrappers in the Magnebot API. Instead, use `self._add_object()`. This wrapper function will automatically set an objects mass, friction values, etc. and add its ID and commands to`self._object_init_commands`. It returns an object ID.

```python
from tdw.tdw_utils import TDWUtils
from magnebot import MagnebotController

class MyMagnebot(MagnebotController):
    def __init__(self, port: int = 1071):
        super().__init__(port=port)
        self.target_object_id = -1

    def init_scene(self):
        self.target_object_id = self._add_object(model_name="rh10",
                                                 position={"x": 3, "y": 0, "z": -4.5},
                                                 rotation={"x": 0, "y": 34, "z": 0},
                                                 scale={"x": 1, "y": 1, "z": 1},
                                                 library="models_core.json")
        scene = [{"$type": "load_scene",
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12)]
        self._init_scene(scene=scene,
                         post_processing=MagnebotController._get_default_post_processing_commands(),
                         position={"x": 0, "y": 0, "z": 0},
                         end=[{"$type": "set_kinematic_state",
                               "id": self.target_object_id,
                               "is_kinematic": True,
                               "use_gravity": False}])


if __name__ == "__main__":
    m = MyMagnebot()
    m.init_scene()
    m.move_to(m.target_object_id)
    m.end()
```

***

## TDW model libraries

To learn more about TDW's model libraries, [read this.](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/librarian/model_librarian.md)  The model librarian metadata classes are all cached in [`TransformInitData.LIBRARIES`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/object_init_data.md#transforminitdata):

```python
from tdw.object_init_data import TransformInitData
from magnebot import MagnebotController

class MyMagnebot(MagnebotController):
    def __init__(self, port: int = 1071):
        super().__init__(port=port)
        for record in TransformInitData.LIBRARIES["models_core.json"].records:
            print(record.name, record.bounds)
```

To learn more about the `ObjectInfo` class (which stores physics data), [read this.](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/py_impact.md#objectinfo) A subset of TDW's models have default physics values, which are stored in the dictionary `Magnebot._OBJECT_AUDIO`: 

```python
from tdw.object_init_data import TransformInitData
from magnebot import MagnebotController

class MyMagnebot(MagnebotController):
    def __init__(self, port: int = 1071):
        super().__init__(port=port)
        for model_name in MagnebotController._OBJECT_AUDIO:
            record = TransformInitData.LIBRARIES["models_core.json"].get_record(model_name)
            # Some objects in `_OBJECT_AUDIO` don't have their own records, such as pieces of a jigsaw puzzle.
            if record is None:
                continue
            mass = MagnebotController._OBJECT_AUDIO[model_name].mass  # See API documentation for ObjectInfo
            bounds = TransformInitData.LIBRARIES["models_core.json"].get_record(model_name).bounds
            print(model_name, mass, bounds)
```

This is a simple example of how to add a randomly selected small object to the scene:

```python
from tdw.object_init_data import TransformInitData
from magnebot import MagnebotController

class MyMagnebot(MagnebotController):
    def __init__(self, port: int = 1071):
        super().__init__(port=port)
        self.target_object_id = -1
        # Get all models with default physics values with a low mass.
        self.small_models = [o.name for o in MagnebotController._OBJECT_AUDIO.values() if o.mass <= 1 and
                             TransformInitData.LIBRARIES["models_core.json"].get_record(o.name) is not None]

    def init_scene(self) -> None:
        # Choose a random model.
        model_name = self.rng.choice(self.small_models)
        self.target_object_id = self._add_object(model_name=model_name,
                                                 position={"x": 3, "y": 0, "z": -4.5})
        super().init_scene()


if __name__ == "__main__":
    m = MyMagnebot()
    m.init_scene()
    m.move_to(m.target_object_id)
```
