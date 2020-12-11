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

The types `Dict`, `Union`, and `List` are in the [`typing` module](https://docs.python.org/3/library/typing.html).

#### Dict[str, float]

Parameters of type `Dict[str, float]` are Vector3 dictionaries formatted like this:

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

#### Union[Dict[str, float], int]]

Parameters of type `Union[Dict[str, float], int]]` can be either a Vector3 or an integer (an object ID).

#### Arm

All parameters of type `Arm` require you to import the [Arm enum class](arm.md):

```python
from magnebot import Arm

print(Arm.left)
```

***

***

## Class Variables

| Variable | Type | Description |
| --- | --- | --- |
| `FORWARD` | np.array | The global forward directional vector. |
| `CAMERA_RPY_CONSTRAINTS` | List[float] | The camera roll, pitch, yaw constraints in degrees. |
| `THIRD_PERSON_CAMERA_ID ` |  | If there is a third-person camera in the scene, this is its ID (i.e. the avatar ID).
    See: `add_third_person_camera()` |

***

## Fields

- `state` Dynamic data for all of the most recent frame (i.e. the frame after doing an action such as `move_to()`). [Read this](scene_state.md) for a full API.

- `auto_save_images` If True, automatically save images to `images_directory` at the end of every action.

- `images_directory` The output directory for images if `auto_save_images == True`. This is a [`Path` object from `pathlib`](https://docs.python.org/3/library/pathlib.html).

- `camera_rpy` The current (roll, pitch, yaw) angles of the Magnebot's camera in degrees.

This is handled outside of `self.state` because it isn't calculated using output data from the build.

See: `Magnebot.CAMERA_RPY_CONSTRAINTS` and `self.rotate_camera()`

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

**`Magnebot(port, launch_build, screen_width, screen_height, auto_save_images, images_directory, debug)`**

| Parameter | Type | Description |
| --- | --- | --- |
| port |  int  | The socket port. [Read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/getting_started.md#command-line-arguments) for more information. |
| launch_build |  bool  | If True, the build will launch automatically on the default port (1071). If False, you will need to launch the build yourself (for example, from a Docker container). |
| screen_width |  int  | The width of the screen in pixels. |
| screen_height |  int  | The height of the screen in pixels. |
| auto_save_images |  bool  | If True, automatically save images to `images_directory` at the end of every action. |
| images_directory |  str  | The output directory for images if `auto_save_images == True`. |
| debug |  bool  | If True, enable debug mode and output debug messages to the console. |

***

### Scene Setup

_These functions should be sent at the start of the simulation._

#### init_scene

**`self.init_scene(scene, layout, room)`**

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

Images of each scene+layout combination can be found [here](https://github.com/alters-mit/magnebot/tree/master/doc/images/floorplans).

Images of where each room in a scene is can be found [here](https://github.com/alters-mit/magnebot/tree/master/doc/images/rooms).

You can call `init_scene()` more than once to reset the simulation.

Possible [return values](action_status.md):

- `success`
- `failed_to_bend` (Technically this is _possible_, but it shouldn't ever happen.)

| Parameter | Type | Description |
| --- | --- | --- |
| scene |  str | The name of an interior floorplan scene. Each number (1, 2, etc.) has a different shape, different rooms, etc. Each letter (a, b, c) is a cosmetically distinct variant with the same floorplan. |
| layout |  int | The furniture layout of the floorplan. Each number (0, 1, 2) will populate the floorplan with different furniture in different positions. |
| room |  int  | The index of the room that the Magnebot will spawn in the center of. If None, the room will be chosen randomly. |

***

### Movement

_These functions move or turn the Magnebot._

#### turn_by

**`self.turn_by(angle, aligned_at)`**

Turn the Magnebot by an angle.

The Magnebot will turn by small increments to align with the target angle.

When turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

Possible [return values](action_status.md):

- `success`
- `failed_to_turn`


| Parameter | Type | Description |
| --- | --- | --- |
| angle |  float | The target angle in degrees. Positive value = clockwise turn. |
| aligned_at |  float  | If the different between the current angle and the target angle is less than this value, then the action is successful. |

_Returns:_  An `ActionStatus` indicating if the Magnebot turned by the angle and if not, why.

#### turn_to

**`self.turn_to(target, aligned_at)`**

Turn the Magnebot to face a target object or position.

The Magnebot will turn by small increments to align with the target angle.

When turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

Possible [return values](action_status.md):

- `success`
- `failed_to_turn`


| Parameter | Type | Description |
| --- | --- | --- |
| target |  Union[int, Dict[str, float] | Either the ID of an object or a Vector3 position. |
| aligned_at |  float  | If the different between the current angle and the target angle is less than this value, then the action is successful. |

_Returns:_  An `ActionStatus` indicating if the Magnebot turned by the angle and if not, why.

#### move_by

**`self.move_by(distance, arrived_at)`**

Move the Magnebot forward or backward by a given distance.

Possible [return values](action_status.md):

- `success`
- `failed_to_move`


| Parameter | Type | Description |
| --- | --- | --- |
| distance |  float | The target distance. If less than zero, the Magnebot will move backwards. |
| arrived_at |  float  | If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful. |

_Returns:_  An `ActionStatus` indicating if the Magnebot moved by `distance` and if not, why.

#### move_to

**`self.move_to(target, arrived_at, aligned_at)`**

Move the Magnebot to a target object or position.

The Magnebot will first try to turn to face the target by internally calling a `turn_to()` action.

Possible [return values](action_status.md):

- `success`
- `failed_to_move`
- `failed_to_turn`


| Parameter | Type | Description |
| --- | --- | --- |
| target |  Union[int, Dict[str, float] | Either the ID of an object or a Vector3 position. |
| arrived_at |  float  | While moving, if at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful. |
| aligned_at |  float  | While turning, if the different between the current angle and the target angle is less than this value, then the action is successful. |

_Returns:_  An `ActionStatus` indicating if the Magnebot moved to the target and if not, why.

***

### Arm Articulation

_These functions move and bend the joints of the Magnebots's arms._

#### reach_for

**`self.reach_for(target, arm, absolute, arrived_at)`**

Reach for a target position.

The action ends when the Magnebot's magnet reaches arm stops moving. The arm might stop moving if it succeeded at finishing the motion, in which case the action is successful. Or, the arms might stop moving because the motion is impossible, there's an obstacle in the way, if the arm is holding something heavy, and so on.

Possible [return values](action_status.md):

- `success`
- `cannot_reach`
- `failed_to_reach`


| Parameter | Type | Description |
| --- | --- | --- |
| target |  Dict[str, float] | The target position for the magnet at the arm to reach. |
| arm |  Arm | The arm that will reach for the target. |
| absolute |  bool  | If True, `target` is in absolute world coordinates. If `False`, `target` is relative to the position and rotation of the Magnebot. |
| arrived_at |  float  | If the magnet is this distance or less from `target`, then the action is successful. |

_Returns:_  An `ActionStatus` indicating if the magnet at the end of the `arm` is at the `target` and if not, why.

#### grasp

**`self.grasp(target, arm)`**

Try to grasp the target object with the arm. The Magnebot will reach for the nearest position on the object.
If, after bending the arm, the magnet is holding the object, then the action is successful.

Possible [return values](action_status.md):

- `success`
- `cannot_reach`
- `failed_to_grasp`


| Parameter | Type | Description |
| --- | --- | --- |
| target |  int | The ID of the target object. |
| arm |  Arm | The arm of the magnet that will try to grasp the object. |

_Returns:_  An `ActionStatus` indicating if the magnet at the end of the `arm` is holding the `target` and if not, why.

#### drop

**`self.drop(target, arm)`**

Drop an object held by a magnet. This action takes exactly 1 frame; it won't wait for the object to finish falling.

See [`SceneState.held`](scene_state.md) for a dictionary of held objects.

Possible [return values](action_status.md):

- `success`
- `not_holding`


| Parameter | Type | Description |
| --- | --- | --- |
| target |  int | The ID of the object currently held by the magnet. |
| arm |  Arm | The arm of the magnet holding the object. |

_Returns:_  An `ActionStatus` indicating if the magnet at the end of the `arm` dropped the `target`.

#### drop_all

**`self.drop_all()`**

Drop all objects held by either magnet. This action takes exactly 1 frame; it won't wait for the object to finish falling.

Possible [return values](action_status.md):

- `success`
- `not_holding`

_Returns:_  An `ActionStatus` if the Magnebot dropped any objects.

#### reset_arm

**`self.reset_arm(arm, reset_torso)`**

Reset an arm to its neutral position. If the arm is holding any objects, it will continue to do so.

Possible [return values](action_status.md):

- `success`
- `failed_to_bend`


| Parameter | Type | Description |
| --- | --- | --- |
| arm |  Arm | The arm that will be reset. |
| reset_torso |  bool  | If True, rotate and slide the torso to its neutral rotation and height. |

_Returns:_  An `ActionStatus` indicating if the arm reset and if not, why.

#### reset_arms

**`self.reset_arms()`**

Reset both arms and the torso to their neutral positions. If either arm is holding any objects, it will continue to do so.

Possible [return values](action_status.md):

- `success`
- `failed_to_bend`

_Returns:_  An `ActionStatus` indicating if the arms reset and if not, why.

***

### Camera

_These commands rotate the Magnebot's camera._

#### rotate_camera

**`self.rotate_camera(roll, pitch, yaw)`**

Rotate the camera by the (roll, pitch, yaw) axes. This action takes exactly 1 frame.

Each axis of rotation is constrained (see `Magnebot.CAMERA_RPY_CONSTRAINTS`).

| Axis | Minimum | Maximum |
| --- | --- | --- |
| roll | -55 | 55 |
| pitch | -70 | 70 |
| yaw | -85 | 85 |

See `self.camera_rpy` for the current (roll, pitch, yaw) angles of the camera.

```python
from magnebot import Magnebot

m = Magnebot()
m.init_scene(scene="2a", layout=1)
status = m.rotate_camera(roll=-10, pitch=-90, yaw=45)
print(status) # ActionStatus.clamped_camera_rotation
print(m.camera_rpy) # [-10 -70 45]
```

Possible [return values](action_status.md):

- `success`
- `clamped_camera_rotation`


| Parameter | Type | Description |
| --- | --- | --- |
| roll |  float  | The roll angle in degrees. |
| pitch |  float  | The pitch angle in degrees. |
| yaw |  float  | The yaw angle in degrees. |

_Returns:_  An `ActionStatus` indicating if the camera rotated fully or if the rotation was clamped..

#### reset_camera

**`self.reset_camera()`**

Reset the rotation of the Magnebot's camera to its default angles. This action takes exactly 1 frame.

```python
from magnebot import Magnebot

m = Magnebot()
m.init_scene(scene="2a", layout=1)
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

#### add_third_person_camera

**`self.add_third_person_camera(position)`**

Add a third person camera (i.e. a camera not attached to the any object) to the scene.
This camera will output images at the end of every action (see [`SceneState.third_person_images`](scene_state.md)).

The camera will always point at the Magnebot.

_Backend developers:_ For the ID of the camera, see: `Magnebot.THIRD_PERSON_CAMERA_ID`.

Possible [return values](action_status.md):

- `success`



| Parameter | Type | Description |
| --- | --- | --- |
| position |  Dict[str, float] | The position of the camera. The camera will never move from this position but it will rotate to look at the Magnebot. |

_Returns:_  An `ActionStatus` (always `success`).

#### end

**`self.end()`**

End the simulation. Terminate the build process.

***

### Low-level

_These are low-level functions that you are unlikely to ever need to use._

#### communicate

**`self.communicate(commands)`**

Use this function to send low-level TDW API commands and receive low-level output data. See: [`Controller.communicate()`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/controller.md)

You shouldn't ever need to use this function, but you might see it in some of the example controllers because they might require a custom scene setup.


| Parameter | Type | Description |
| --- | --- | --- |
| commands |  Union[dict, List[dict] | Commands to send to the build. See: [Command API](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md). |

_Returns:_  The response from the build as a list of byte arrays. See: [Output Data](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/output_data.md).

***

