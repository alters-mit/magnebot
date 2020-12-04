# Magnebot

`from magnebot import Magnebot`

[TDW controller](https://github.com/threedworld-mit/tdw) for Magnebots.

```python
from magnebot import Magnebot

m = Magnebot()
# Initializes the scene.
m.init_scene(scene="2a", layout=1)
```

***

## Parameter types

#### Dict[str, float]

All parameters of type `Dict[str, float]` are Vector3 dictionaries formatted like this:

```json
{"x": -0.2, "y": 0.21, "z": 0.385}
```

`y` is the up direction.

To convert from or to a numpy array:

```python
from tdw.tdw_utils import TDWUtils

target = {"x": 1, "y": 0, "z": 0}
target = TDWUtils.vector3_to_array(target)
print(target) # [1 0 0]
target = TDWUtils.array_to_vector3(target)
print(target) # {'x': 1.0, 'y': 0.0, 'z': 0.0}
```

A parameter of type `Union[Dict[str, float], int]]` can be either a Vector3 or an integer (an object ID).

The types `Dict`, `Union`, and `List` are in the [`typing` module](https://docs.python.org/3/library/typing.html).

#### Arm

All parameters of type `Arm` require you to import the [Arm enum class](arm.md):

```python
from magnebot import Arm

print(Arm.left)
```

***

***

## Fields

- `state` Dynamic data for all of the most recent frame (i.e. the frame after doing an action such as `move_to()`). [Read this](scene_state.md) for a full API.

- `camera_rpy` The current (roll, pitch, yaw) angles of the Magnebot's camera in degrees.

This is handled outside of `self.state` because it isn't calculated using output data from the build.

See: `Magnebot.CAMERA_RPY_CONSTRAINTS` and `Magnebot.rotate_camera()`

- `segmentation_color_to_id` A dictionary. Key = a hashable representation of the object's segmentation color. Value = The object ID. See `static_object_info` for a dictionary mapped to object ID with additional data.

```python
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot

m = Magnebot()
m.init_scene(scene="2a", layout=1)

for hashable_color in m.segmentation_color_to_id:
    object_id = m.segmentation_color_to_id[hashable_color]
    # Convert the hashable color back to an [r, g, b] array.
    color = TDWUtils.hashable_to_color(hashable_color)
```

- `magnebot_static` Static data for the Magnebot that doesn't change between frames. [Read this for a full API](magnebot_static.md)

```python
from magnebot import Magnebot

m = Magnebot()
m.init_scene(scene="2a", layout=1)
print(m.magnebot_static.magnets)
```

***

## Functions

#### \_\_init\_\_

**`def __init__(self, port: int = 1071, launch_build: bool = True, screen_width: int = 256, screen_height: int = 256, debug: bool = False)`**

| Parameter | Description |
| --- | --- |
| port | The socket port. [Read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/getting_started.md#command-line-arguments) for more information. |
| launch_build | If True, the build will launch automatically on the default port (1071). If False, you will need to launch the build yourself (for example, from a Docker container). |
| screen_width | The width of the screen in pixels. |
| screen_height | The height of the screen in pixels. |
| debug | If True, enable debug mode and output debug messages to the console. |

***

### Scene Setup

_These functions should be sent at the start of the simulation._

#### init_scene

**`def init_scene(self, scene: str, layout: int, room: int = -1) -> ActionStatus`**

Initialize a scene, populate it with objects, and add the Magnebot. The simulation will advance through frames until the Magnebot's body is in its neutral position.

**Always call this function before any other API calls.**

Set the `scene` and `layout` parameters in `init_scene()` to load an interior scene with furniture and props. Set the `room` to spawn the avatar in the center of a room.

```python
from magnebot import Magnebot

m = Magnebot()
m.init_scene(scene="2b", layout=0, room=1)

# Your code here.
```

Valid scenes, layouts, and rooms:

| `scene` | `layout` | `room` |
| --- | --- | --- |
| 1a, 1b, 1c | 0, 1, 2 | 0, 1, 2, 3, 4, 5, 6 |
| 2a, 2b, 2c | 0, 1, 2 | 0, 1, 2, 3, 4, 5, 6, 7, 8 |
| 4a, 4b, 4c | 0, 1, 2 | 0, 1, 2, 3, 4, 5, 6, 7 |
| 5a, 5b, 5c | 0, 1, 2 | 0, 1, 2, 3 |

Images of each scene+layout combination can be found [here](https://github.com/alters-mit/magnebot/tree/master/Documentation/images/floorplans).

You can safely call `init_scene()` more than once to reset the simulation.

Possible [return values](action_status.md):

- `success`
- `failed_to_bend` (Technically this is _possible_, but it shouldn't ever happen.)

| Parameter | Description |
| --- | --- |
| scene | The name of an interior floorplan scene. Each number (1, 2, etc.) has a different shape, different rooms, etc. Each letter (a, b, c) is a cosmetically distinct variant with the same floorplan. |
| layout | The furniture layout of the floorplan. Each number (0, 1, 2) will populate the floorplan with different furniture in different positions. |
| room | The index of the room that the Magnebot will spawn in the center of. If `room == -1` the room will be chosen randomly. |

#### init_test_scene

**`def init_test_scene(self) -> ActionStatus`**

Initialize an empty test room with a Magnebot. The simulation will advance through frames until the Magnebot's body is in its neutral position.

This function can be called instead of `init_scene()` for testing purposes. If so, it must be called before any other API calls.

```python
from magnebot import Magnebot

m = Magnebot()
m.init_test_scene()

# Your code here.
```

You can safely call `init_test_scene()` more than once to reset the simulation.

Possible [return values](action_status.md):

- `success`
- `failed_to_bend` (Technically this is _possible_, but it shouldn't ever happen.)

***

### Movement

_These functions move or turn the Magnebot._

#### turn_by

**`def turn_by(self, angle: float, aligned_at: float = 3) -> ActionStatus`**

Turn the Magnebot by an angle.

The Magnebot will turn by small increments to align with the target angle.

When turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

Possible [return values](action_status.md):

- `success`
- `failed_to_turn`


| Parameter | Description |
| --- | --- |
| angle | The target angle in degrees. Positive value = clockwise turn. |
| aligned_at | If the different between the current angle and the target angle is less than this value, then the action is successful. |

_Returns:_  An `ActionStatus` indicating if the Magnebot turned by the angle and if not, why.

#### turn_to

**`def turn_to(self, target: Union[int, Dict[str, float]], aligned_at: float = 3) -> ActionStatus`**

Turn the Magnebot to face a target object or position.

The Magnebot will turn by small increments to align with the target angle.

When turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

Possible [return values](action_status.md):

- `success`
- `failed_to_turn`


| Parameter | Description |
| --- | --- |
| target | Either the ID of an object or a Vector3 position. |
| aligned_at | If the different between the current angle and the target angle is less than this value, then the action is successful. |

_Returns:_  An `ActionStatus` indicating if the Magnebot turned by the angle and if not, why.

#### move_by

**`def move_by(self, distance: float, arrived_at: float = 0.1) -> ActionStatus`**

Move the Magnebot forward or backward by a given distance.

Possible [return values](action_status.md):

- `success`
- `failed_to_move`


| Parameter | Description |
| --- | --- |
| distance | The target distance. If less than zero, the Magnebot will move backwards. |
| arrived_at | If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful. |

_Returns:_  An `ActionStatus` indicating if the Magnebot moved by `distance` and if not, why.

#### move_to

**`def move_to(self, target: Union[int, Dict[str, float]], arrived_at: float = 0.1, aligned_at: float = 3) -> ActionStatus`**

Move the Magnebot to a target object or position.

The Magnebot will first try to turn to face the target by internally calling a `turn_to()` action.

Possible [return values](action_status.md):

- `success`
- `failed_to_move`
- `failed_to_turn`


| Parameter | Description |
| --- | --- |
| target | Either the ID of an object or a Vector3 position. |
| arrived_at | While moving, if at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful. |
| aligned_at | While turning, if the different between the current angle and the target angle is less than this value, then the action is successful. |

_Returns:_  An `ActionStatus` indicating if the Magnebot moved to the target and if not, why.

***

### Arm Articulation

_These functions move and bend the joints of the Magnebots's arms._

#### reach_for

**`def reach_for(self, target: Dict[str, float], arm: Arm, absolute: bool = False, arrived_at: float = 0.125) -> ActionStatus`**

Reach for a target position.

The action ends when the Magnebot's magnet reaches arm stops moving. The arm might stop moving if it succeeded at finishing the motion, in which case the action is successful. Or, the arms might stop moving because the motion is impossible, there's an obstacle in the way, if the arm is holding something heavy, and so on.

Possible [return values](action_status.md):

- `success`
- `cannot_reach`
- `failed_to_reach`


| Parameter | Description |
| --- | --- |
| target | The target position for the magnet at the arm to reach. |
| arm | The arm that will reach for the target. |
| absolute | If True, `target` is in absolute world coordinates. If `False`, `target` is relative to the position and rotation of the Magnebot. |
| arrived_at | If the magnet is this distance or less from `target`, then the action is successful. |

_Returns:_  An `ActionStatus` indicating if the magnet at the end of the `arm` is at the `target` and if not, why.

#### grasp

**`def grasp(self, target: int, arm: Arm) -> ActionStatus`**

Try to grasp the target object with the arm. The Magnebot will reach for the nearest position on the object.
If, after bending the arm, the magnet is holding the object, then the action is successful.

Possible [return values](action_status.md):

- `success`
- `cannot_reach`
- `failed_to_grasp`


| Parameter | Description |
| --- | --- |
| target | The ID of the target object. |
| arm | The arm of the magnet that will try to grasp the object. |

_Returns:_  An `ActionStatus` indicating if the magnet at the end of the `arm` is holding the `target` and if not, why.

#### drop

**`def drop(self, target: int, arm: Arm) -> ActionStatus`**

Drop an object held by a magnet. This action takes exactly 1 frame; it won't wait for the object to finish falling.

See [`SceneState.held`](scene_state.md) for a dictionary of held objects.

Possible [return values](action_status.md):

- `success`
- `not_holding`


| Parameter | Description |
| --- | --- |
| target | The ID of the object currently held by the magnet. |
| arm | The arm of the magnet holding the object. |

_Returns:_  An `ActionStatus` indicating if the magnet at the end of the `arm` dropped the `target`.

#### drop_all

**`def drop_all(self) -> ActionStatus`**

Drop all objects held by either magnet. This action takes exactly 1 frame; it won't wait for the object to finish falling.

Possible [return values](action_status.md):

- `success`
- `not_holding`

_Returns:_  An `ActionStatus` if the Magnebot dropped any objects.

#### reset_arm

**`def reset_arm(self, arm: Arm, reset_torso: bool = True) -> ActionStatus`**

Reset an arm to its neutral position. If the arm is holding any objects, it will continue to do so.

Possible [return values](action_status.md):

- `success`
- `failed_to_bend`


| Parameter | Description |
| --- | --- |
| arm | The arm that will be reset. |
| reset_torso | If True, rotate and slide the torso to its neutral rotation and height. |

_Returns:_  An `ActionStatus` indicating if the arm reset and if not, why.

#### reset_arms

**`def reset_arms(self) -> ActionStatus`**

Reset both arms and the torso to their neutral positions. If either arm is holding any objects, it will continue to do so.

Possible [return values](action_status.md):

- `success`
- `failed_to_bend`

_Returns:_  An `ActionStatus` indicating if the arms reset and if not, why.

***

### Camera

_These commands rotate the Magnebot's camera._

#### rotate_camera

**`def rotate_camera(self, roll: float = 0, pitch: float = 0, yaw: float = 0) -> ActionStatus`**

Rotate the camera by the (roll, pitch, yaw) axes. This action takes exactly 1 frame.

Each axis of rotation is constrained (see `Magnebot.CAMERA_RPY_CONSTRAINTS`).

| Axis | Minimum | Maximum |
| --- | --- | --- |
| roll | -55 | 55 |
| pitch | -70 | 70 |
| yaw | -85 | 85 |

See `Magnebot.camera_rpy` for the current (roll, pitch, yaw) angles of the camera.

```python
from magnebot import Magnebot

m = Magnebot()
m.init_test_scene()
status = m.rotate_camera(roll=-10, pitch=-90, yaw=45)
print(status) # ActionStatus.clamped_camera_rotation
print(m.camera_rpy) # [-10 -70 45]
```

Possible [return values](action_status.md):

- `success`
- `clamped_camera_rotation`


| Parameter | Description |
| --- | --- |
| roll | The roll angle in degrees. |
| pitch | The pitch angle in degrees. |
| yaw | The yaw angle in degrees. |

_Returns:_  An `ActionStatus` indicating if the camera rotated fully or if the rotation was clamped..

#### reset_camera

**`def reset_camera(self) -> ActionStatus`**

Reset the rotation of the Magnebot's camera to its default angles. This action takes exactly 1 frame.

```python
from magnebot import Magnebot

m = Magnebot()
m.init_test_scene()
m.rotate_camera(roll=-10, pitch=-90, yaw=45)
m.reset_camera()
print(m.camera_rpy) # [0 0 0]
```

Possible [return values](action_status.md):

- `success`

_Returns:_  An `ActionStatus` (always `success`).

***

### Misc.

_These are utility functions that won't advance the simulation by any frames._

#### end

**`def end(self) -> None`**

End the simulation. Terminate the build process.

***

### Low-level

_These are low-level functions that you are unlikely to ever need to use._

#### communicate

**`def communicate(self, commands: Union[dict, List[dict]]) -> List[bytes]`**

Use this function to send low-level TDW API commands and receive low-level output data. See: [`Controller.communicate()`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/controller.md)

You shouldn't ever need to use this function, but you might see it in some of the example controllers because they might require a custom scene setup.


| Parameter | Description |
| --- | --- |
| commands | Commands to send to the build. See: [Command API](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md). |

_Returns:_  The response from the build as a list of byte arrays. See: [Output Data](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/output_data.md).

***

