# Magnebot

`from magnebot import Magnebot`

[TDW controller](https://github.com/threedworld-mit/tdw) for Magnebots. This high-level API supports:

- Creating a complex interior environment
- Directional movement
- Turning
- Arm articulation via inverse kinematics (IK)
- Grasping and dropping objects
- Image rendering
- Scene state metadata

Unless otherwise stated, each of these functions is an "action" that the Magnebot can do. Each action advances the simulation by at least 1 physics frame, returns an [`ActionStatus`](action_status.md), and updates the `state` field.

```python
from magnebot import Magnebot

m = Magnebot()
# Initializes the scene.
status = m.init_scene(scene="2a", layout=1)
print(status) # ActionStatus.success

# Prints the current position of the Magnebot.
print(m.state.magnebot_transform.position)
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
| `CAMERA_RPY_CONSTRAINTS` | List[float] | The camera roll, pitch, yaw constraints in degrees. |

***

## Fields

- `state` Dynamic data for all of the most recent frame (i.e. the frame after doing an action such as `move_to()`). [Read this](scene_state.md) for a full API.

- `auto_save_images` If True, automatically save images to `images_directory` at the end of every action.

- `images_directory` The output directory for images if `auto_save_images == True`. This is a [`Path` object from `pathlib`](https://docs.python.org/3/library/pathlib.html).

- `camera_rpy` The current (roll, pitch, yaw) angles of the Magnebot's camera in degrees as a numpy array. This is handled outside of `self.state` because it isn't calculated using output data from the build. See: `Magnebot.CAMERA_RPY_CONSTRAINTS` and `self.rotate_camera()`

- `objects_static` Data for all objects in the scene that that doesn't change between frames, such as object IDs, mass, etc. Key = the ID of the object. [Read the full API here](object_static.md).

```python
from magnebot import Magnebot

m = Magnebot()
m.init_scene(scene="2a", layout=1)

# Print each object ID and segmentation color.     
for object_id in m.objects_static:
    o = m.objects_static[object_id]
    print(object_id, o.segmentation_color)
```

- `segmentation_color_to_id` A dictionary. Key = a hashable representation of the object's segmentation color. Value = The object ID. See `objects_static` for a dictionary mapped to object ID with additional data.

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

- `magnebot_static` Data for the Magnebot that doesn't change between frames. [Read this for a full API](magnebot_static.md)

```python
from magnebot import Magnebot

m = Magnebot()
m.init_scene(scene="2a", layout=1)
print(m.magnebot_static.magnets)
```

- `occupancy_map` A numpy array of the occupancy map. This is None until you call `init_scene()`

Shape = `(1, width, length)` where `width` and `length` are the number of cells in the grid. Each grid cell has a radius of 0.245. To convert from occupancy map `(x, y)` coordinates to worldspace `(x, z)` coordinates, see: `get_occupancy_position()`.

Each element is an integer describing the occupancy at that position.

| Value | Meaning |
| --- | --- |
| -1 | This position is outside of the scene. |
| 0 | Unoccupied and navigable; the Magnebot can go here. |
| 1 | This position is occupied by an object(s) or a wall. |
| 2 | This position is free but not navigable (usually because there are objects in the way. |

```python
from magnebot import Magnebot

m = Magnebot(launch_build=False)
m.init_scene(scene="1a", layout=0)
x = 30
y = 16
print(m.occupancy_map[x][y]) # 0 (free and navigable position)
print(m.get_occupancy_position(x, y)) # (1.1157886505126946, 2.2528389358520506)
```

Images of occupancy maps can be found [here](https://github.com/alters-mit/magnebot/tree/master/doc/images/occupancy_maps). The blue squares are free navigable positions. Images are named `scene_layout.jpg` (there aren't any letters in the scene name because the difference between lettered variants is purely aesthetic and the room maps are identical).

The occupancy map is static, meaning that it won't update when objects are moved.

Note that it is possible for the Magnebot to go to positions that aren't "free". Reasons for this include:

- The Magnebot's base is a rectangle that is longer on the sides than the front and back. The occupancy grid cell size is defined by the longer axis, so it is possible for the Magnebot to move forward and squeeze into a smaller space.
- The Magnebot can push, lift, or otherwise move objects out of its way.

***

## Functions

#### \_\_init\_\_

**`Magnebot()`**

**`Magnebot(port=1071, launch_build=True, screen_width=256, screen_height=256, auto_save_images=False, images_directory="images", debug=False)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| port |  int  | 1071 | The socket port. [Read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/getting_started.md#command-line-arguments) for more information. |
| launch_build |  bool  | True | If True, the build will launch automatically on the default port (1071). If False, you will need to launch the build yourself (for example, from a Docker container). |
| screen_width |  int  | 256 | The width of the screen in pixels. |
| screen_height |  int  | 256 | The height of the screen in pixels. |
| auto_save_images |  bool  | False | If True, automatically save images to `images_directory` at the end of every action. |
| images_directory |  str  | "images" | The output directory for images if `auto_save_images == True`. |
| debug |  bool  | False | If True, enable debug mode. This controller will output messages to the console, including any warnings or errors sent by the build. It will also create 3D plots of arm articulation IK solutions. |

***

### Scene Setup

_These functions should be sent at the start of the simulation._

#### init_scene

**`self.init_scene(scene, layout)`**

**`self.init_scene(scene, layout, room=None)`**

Initialize a scene, populate it with objects, and add the Magnebot. The simulation will advance through frames until the Magnebot's body is in its neutral position.

**Always call this function before any other API calls.**

It might take a few minutes to initialize the scene.

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

Images of each scene+layout combination can be found [here](https://github.com/alters-mit/magnebot/tree/master/doc/images/floorplans). Images are named `scene_layout.jpg`.

Images of where each room in a scene is can be found [here](https://github.com/alters-mit/magnebot/tree/master/doc/images/rooms). Images are named `scene.jpg` (there aren't any letters in the scene name because the difference between lettered variants is purely aesthetic and the room maps are identical).

You can call `init_scene()` more than once to reset the simulation.

Possible [return values](action_status.md):

- `success`
- `failed_to_bend` (Technically this is _possible_, but it shouldn't ever happen.)

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  str |  | The name of an interior floorplan scene. Each number (1, 2, etc.) has a different shape, different rooms, etc. Each letter (a, b, c) is a cosmetically distinct variant with the same floorplan. |
| layout |  int |  | The furniture layout of the floorplan. Each number (0, 1, 2) will populate the floorplan with different furniture in different positions. |
| room |  int  | None | The index of the room that the Magnebot will spawn in the center of. If None, the room will be chosen randomly. |

***

### Movement

_These functions move or turn the Magnebot._

#### turn_by

**`self.turn_by(angle)`**

**`self.turn_by(angle, aligned_at=3)`**

Turn the Magnebot by an angle.

The Magnebot will turn by small increments to align with the target angle.

When turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

Possible [return values](action_status.md):

- `success`
- `failed_to_turn`


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| angle |  float |  | The target angle in degrees. Positive value = clockwise turn. |
| aligned_at |  float  | 3 | If the different between the current angle and the target angle is less than this value, then the action is successful. |

_Returns:_  An `ActionStatus` indicating if the Magnebot turned by the angle and if not, why.

#### turn_to

**`self.turn_to(target)`**

**`self.turn_to(target, aligned_at=3)`**

Turn the Magnebot to face a target object or position.

The Magnebot will turn by small increments to align with the target angle.

When turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

Possible [return values](action_status.md):

- `success`
- `failed_to_turn`


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  Union[int, Dict[str, float] |  | Either the ID of an object or a Vector3 position. |
| aligned_at |  float  | 3 | If the different between the current angle and the target angle is less than this value, then the action is successful. |

_Returns:_  An `ActionStatus` indicating if the Magnebot turned by the angle and if not, why.

#### move_by

**`self.move_by(distance)`**

**`self.move_by(distance, arrived_at=0.3)`**

Move the Magnebot forward or backward by a given distance.

Possible [return values](action_status.md):

- `success`
- `failed_to_move`
- `collision`


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| distance |  float |  | The target distance. If less than zero, the Magnebot will move backwards. |
| arrived_at |  float  | 0.3 | If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful. |

_Returns:_  An `ActionStatus` indicating if the Magnebot moved by `distance` and if not, why.

#### move_to

**`self.move_to(target)`**

**`self.move_to(target, arrived_at=0.3, aligned_at=3)`**

Move the Magnebot to a target object or position.

The Magnebot will first try to turn to face the target by internally calling a `turn_to()` action.

Possible [return values](action_status.md):

- `success`
- `failed_to_move`
- `collision`
- `failed_to_turn`


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  Union[int, Dict[str, float] |  | Either the ID of an object or a Vector3 position. |
| arrived_at |  float  | 0.3 | While moving, if at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful. |
| aligned_at |  float  | 3 | While turning, if the different between the current angle and the target angle is less than this value, then the action is successful. |

_Returns:_  An `ActionStatus` indicating if the Magnebot moved to the target and if not, why.

***

### Arm Articulation

_These functions move and bend the joints of the Magnebots's arms._

#### reach_for

**`self.reach_for(target, arm)`**

**`self.reach_for(target, arm, absolute=True, arrived_at=0.125)`**

Reach for a target position.

The action ends when the Magnebot's magnet reaches arm stops moving. The arm might stop moving if it succeeded at finishing the motion, in which case the action is successful. Or, the arms might stop moving because the motion is impossible, there's an obstacle in the way, if the arm is holding something heavy, and so on.

Possible [return values](action_status.md):

- `success`
- `cannot_reach`
- `failed_to_reach`


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  Dict[str, float] |  | The target position for the magnet at the arm to reach. |
| arm |  Arm |  | The arm that will reach for the target. |
| absolute |  bool  | True | If True, `target` is in absolute world coordinates. If `False`, `target` is relative to the position and rotation of the Magnebot. |
| arrived_at |  float  | 0.125 | If the magnet is this distance or less from `target`, then the action is successful. |

_Returns:_  An `ActionStatus` indicating if the magnet at the end of the `arm` is at the `target` and if not, why.

#### grasp

**`self.grasp(target, arm)`**

Try to grasp the target object with the arm. The Magnebot will reach for the nearest position on the object.
If, after bending the arm, the magnet is holding the object, then the action is successful.

Possible [return values](action_status.md):

- `success`
- `cannot_reach`
- `failed_to_grasp`


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  int |  | The ID of the target object. |
| arm |  Arm |  | The arm of the magnet that will try to grasp the object. |

_Returns:_  An `ActionStatus` indicating if the magnet at the end of the `arm` is holding the `target` and if not, why.

#### drop

**`self.drop(target, arm)`**

**`self.drop(target, arm, wait_for_objects=True)`**

Drop an object held by a magnet.

See [`SceneState.held`](scene_state.md) for a dictionary of held objects.

Possible [return values](action_status.md):

- `success`
- `not_holding`


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  int |  | The ID of the object currently held by the magnet. |
| arm |  Arm |  | The arm of the magnet holding the object. |
| wait_for_objects |  bool  | True | If True, the action will continue until the objects have finished falling. If True, the action will take exactly 1 frame to finish. |

_Returns:_  An `ActionStatus` indicating if the magnet at the end of the `arm` dropped the `target`.

#### reset_arm

**`self.reset_arm(arm)`**

**`self.reset_arm(arm, reset_torso=True)`**

Reset an arm to its neutral position.

Possible [return values](action_status.md):

- `success`
- `failed_to_bend`


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| arm |  Arm |  | The arm that will be reset. |
| reset_torso |  bool  | True | If True, rotate and slide the torso to its neutral rotation and height. |

_Returns:_  An `ActionStatus` indicating if the arm reset and if not, why.

***

### Camera

_These commands rotate the Magnebot's camera or add additional camera to the scene._

#### rotate_camera

**`self.rotate_camera()`**

**`self.rotate_camera(roll=0, pitch=0, yaw=0)`**

Rotate the Magnebot's camera by the (roll, pitch, yaw) axes. This action takes exactly 1 frame.

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


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| roll |  float  | 0 | The roll angle in degrees. |
| pitch |  float  | 0 | The pitch angle in degrees. |
| yaw |  float  | 0 | The yaw angle in degrees. |

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

#### add_camera

**`self.add_camera(position)`**

**`self.add_camera(position, roll=0, pitch=0, yaw=0, look_at=True, follow=False, camera_id="c")`**

Add a third person camera (i.e. a camera not attached to the any object) to the scene. This camera will render concurrently with the camera attached to the Magnebot and will output images at the end of every action (see [`SceneState.third_person_images`](scene_state.md)).

This should only be sent per `init_scene()` call. When `init_scene()` is called to reset the simulation, you'll need to send `add_camera()` again too.

Possible [return values](action_status.md):

- `success`


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| position |  Dict[str, float] |  | The initial position of the camera. If `follow == True`, this is relative to the Magnebot. If `follow == False`, this is in absolute worldspace coordinates. |
| roll |  float  | 0 | The initial roll of the camera in degrees. |
| pitch |  float  | 0 | The initial pitch of the camera in degrees. |
| yaw |  float  | 0 | The initial yaw of the camera in degrees. |
| look_at |  bool  | True | If True, on every frame, the camera will rotate to look at the Magnebot. |
| follow |  bool  | False | If True, on every frame, the camera will follow the Magnebot, maintaining a constant relative position and rotation. |
| camera_id |  str  | "c" | The ID of this camera. |

_Returns:_  An `ActionStatus` (always `success`).

***

### Misc.

_These are utility functions that won't advance the simulation by any frames._

#### get_occupancy_position

**`self.get_occupancy_position(i, j)`**

Converts the position `(i, j)` in the occupancy map to `(x, z)` worldspace coordinates.

```python
from magnebot import Magnebot

m = Magnebot(launch_build=False)
m.init_scene(scene="1a", layout=0)
x = 30
y = 16
print(m.occupancy_map[x][y]) # 0 (free and navigable position)
print(m.get_occupancy_position(x, y)) # (1.1157886505126946, 2.2528389358520506)
```


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| i |  int |  | The i coordinate in the occupancy map. |
| j |  int |  | The j coordinate in the occupancy map. |

_Returns:_  Tuple: (x coordinate; z coordinate) of the corresponding worldspace position.

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


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| commands |  Union[dict, List[dict] |  | Commands to send to the build. See: [Command API](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md). |

_Returns:_  The response from the build as a list of byte arrays. See: [Output Data](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/output_data.md).

***

