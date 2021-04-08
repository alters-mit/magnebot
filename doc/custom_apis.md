# Custom APIs

The Magnebot API is designed to be easily extendable for specialized APIs. Generally, we expect that frontend users won't need to write their own specialized APIs, but if they do, here are some helpful notes on the backend programming.

- **[Scene initialization](scene.md)**
- **[Moving and turning](movement.md)**
- **[Arm articulation](arm_articulation.md)**
- [**Example controller**](https://github.com/alters-mit/magnebot/blob/main/controllers/examples/custom_api.py)

## Overview

In general, all actions need to start by calling `self._start_action()` and end with `self._end_action()`. Ideally, they should return an [`ActionStatus`](api/action_status.md):

```python
from magnebot import Magnebot, ActionStatus

class MyMagnebot(Magnebot):
    def my_action(self) -> ActionStatus:
        self._start_action()
        
        # Your code here.
        
        self._end_action()
        return ActionStatus.success


if __name__ == "__main__":
    m = MyMagnebot()
    m.init_scene()
    m.my_action()
```

- `self._start_action()` disables the camera for the duration of the action
- `self._end_action()` re-enables the camera and sets `self.state` (including image data)
- `ActionStatus` is a status code that can help the user determine why an action succeeded or failed

## Sending commands to the build

[Read these documents](https://github.com/threedworld-mit/tdw/tree/master/Documentation/api) to learn more about the low-level TDW API works.

If you want to send commands to the build, call `self.communicate()`:

```python
from magnebot import Magnebot, ActionStatus

class MyMagnebot(Magnebot):
    def my_action(self) -> ActionStatus:
        self._start_action()

        self.communicate({"$type": "do_nothing"})

        self._end_action()
        return ActionStatus.success


if __name__ == "__main__":
    m = MyMagnebot()
    m.init_scene()
    m.my_action()
```

However, you will often want to send commands on the *next* frame for better physics precision. `self._end_action()` calls `self.communicate()` internally, for example.

In the Magnebot API, there is a list called `self._next_frame_commands`. Whenever `self.communicate(commands)` is called, it automatically appends all of the commands in `self._next_frame_commands` to `commands` and then clears `self._next_frame_commands`.

This example is identical to the previous example except that it will call `self.communicate()` once (within `self._end_action()`) instead of twice:

```python
from magnebot import Magnebot, ActionStatus

class MyMagnebot(Magnebot):
    def my_action(self) -> ActionStatus:
        self._start_action()
        
        self._next_frame_commands.append({"$type": "do_nothing"})

        self._end_action()
        return ActionStatus.success
    

if __name__ == "__main__":
    m = MyMagnebot()
    m.init_scene()
    m.my_action()
```

## Creating new `SceneState` objects

Typically, `self.state` reflects the state of the simulation at the *end* of an action (and is assigned within `self._end_action()`). Once you call `self.communicate()`, there's no way to know if `self.state` accurately describes the current simulation state.

You can create your own `SceneState` objects using the response from the build. You will often need to do this to track an intermediate scene state (for example, if you need to get how many degrees each wheel has spun since the action began). Note that unlike `self.state`, these `SceneState` objects won't contain images because the camera is disabled until `self._end_action()` is called:

```python
from magnebot import Magnebot, ActionStatus
from magnebot.scene_state import SceneState

class MyMagnebot(Magnebot):
    def my_action(self) -> ActionStatus:
        self._start_action()
        
        resp = self.communicate({"$type": "do_nothing"})
        state = SceneState(resp=resp)
        print(state.magnebot_transform.position)
        print(state.images)  # An empty dictionary.

        self._end_action()
        return ActionStatus.success


if __name__ == "__main__":
    m = MyMagnebot()
    m.init_scene()
    m.my_action()
```

## Output data

The data within a `SceneState` object is usually sufficient for most actions. Occasionally, you'll need additional [output data from the build](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/output_data.md).

The Magnebot has a utility `get_data()` function which can automatically extract output data of a given type from a byte array. This is often very convenient, but has two caveats:

- It's slightly inefficient (this only matters if there are many output data objects)
- It will only return the first instance of a given output data type. Some output data types such as `Collision` will appear multiple times in `resp`. Some output data types such as `Transforms` appear once and contain multiple objects. This is due to how the output data is actually gathered within the build, what is the most computationally efficient option, etc.

The following example will get [`Raycast` data](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/output_data.md#Raycast). Note that because `self._end_action()` internally calls `self.communicate()`, it also returns the response from the build (`resp`):

```python
from tdw.output_data import Raycast
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus
from magnebot.util import get_data

class MyMagnebot(Magnebot):
    def __init__(self, port: int = 1071):
        super().__init__(port=port)
        self.target_object_id: int = -1
        
    def my_action(self) -> ActionStatus:
        self._start_action()

        self._next_frame_commands.append({"$type": "send_raycast",
                                          "origin": TDWUtils.array_to_vector3(self.state.magnebot_transform.position),
                                          "destination": {"x": 10, "y": 1, "z": 2}})
        resp = self._end_action()
        raycast = get_data(resp=resp, d_type=Raycast)
        # The action is successful if the raycast hit an object.
        if raycast.get_hit() and raycast.get_hit_object():
            # Set the target object from the raycast.
            self.target_object_id = raycast.get_object_id()
            return ActionStatus.success
        else:
            return ActionStatus.failure


if __name__ == "__main__":
    m = MyMagnebot()
    m.init_scene()
    m.my_action()
```