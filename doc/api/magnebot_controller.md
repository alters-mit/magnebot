# MagnebotController

`from magnebot import MagnebotController`

This is a simplified API for single-agent [Magnebot](magnebot.md) simulations.

```python
from magnebot import MagnebotController

m = MagnebotController()
m.init_scene()
m.move_by(2)
m.end()
```

Differences between the `MagnebotController` and `Magnebot` agent:

- The `MagnebotController` *is a [controller](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/controller.md)* and will send its own commands.
- In the `MagnebotController`, the agent's action will begin and end automatically. In the above example, `m.move_by(2)` will continuously advance the simulation until the Magnebot has moved 2 meters or stopped unexpectedly (i.e. due to a collision).
- The `MagnebotController`, [physics frames are skipped per output data frame](skip_frames.md); see `skip_frames` in the constructor.
- Images are always returned at the end of every action. In the above example, [`m.dynamic.images`](magnebot_dynamic.md) will be updated at the end of `m.move_by(2)`.
- The `MagnebotController` includes two functions that can initialize a scene optimized for the Magnebot.
- The `MagnebotController` adds an [`ObjectManager`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/add_ons/object_manager.md) and [`CollisionManager`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/add_ons/collision_manager.md).

***

## Fields

- `occupancy_map` A numpy array of an occupancy map. This is set after calling `self.init_floorplan_scene()`.

Shape = (1, width, length) where width and length are the number of cells in the grid. Each grid cell has a radius of 0.49. To convert from occupancy map (x, y) coordinates to worldspace (x, z) coordinates, see: `self.get_occupancy_position(i, j)`.
Each element is an integer describing the occupancy at that position.

| Value | Meaning |
| --- | --- |
| -1 | This position is outside of the scene. |
| 0 | Unoccupied and navigable; the Magnebot can go here. |
| 1 | This position is occupied by an object(s) or a wall. |
| 2 | This position is free but not navigable (usually because there are objects in the way. |

```python
from magnebot import MagnebotController

m = MagnebotController()
m.init_floorplan_scene(scene="1a", layout=0, room=0)
x = 30
y = 16
print(m.occupancy_map[x][y]) # 0 (free and navigable position)
print(m.get_occupancy_position(x, y)) # (1.1157886505126946, 2.2528389358520506)
m.end()
```

Images of occupancy maps can be found [here](https://github.com/alters-mit/magnebot/tree/master/doc/images/occupancy_maps). The blue squares are free navigable positions. Images are named `[scene]_[layout].jpg` For example, the occupancy map image for scene "2a" layout 0 is: `2_0.jpg`.

The occupancy map is static, meaning that it won't update when objects are moved.

Note that it is possible for the Magnebot to go to positions that aren't "free". The Magnebot's base is a rectangle that is longer on the sides than the front and back. The occupancy grid cell size is defined by the longer axis, so it is possible for the Magnebot to move forward and squeeze into a smaller space. The Magnebot can also push, lift, or otherwise move objects out of its way.

- `rng` A random number generator.

- `magnebot` [The Magnebot agent.](magnebot.md). Call this to access static or dynamic data:

```python
from magnebot import MagnebotController

m = MagnebotController()
m.init_scene()
print(m.magnebot.dynamic.transform.position)
m.end()
```

- `objects` [An `ObjectManager`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/add_ons/object_manager.md) for tracking static and dynamic object data:

```python
from magnebot import MagnebotController

m = MagnebotController()
m.init_floorplan_scene(scene="1a", layout=0, room=0)
for object_id in m.objects.objects_static:
    name = m.objects.objects_static[object_id].name
    segmentation_color = m.objects.objects_static[object_id].segmentation_color
    print(object_id, name, segmentation_color)
for object_id in m.objects.transforms:
    position = m.objects.transforms[object_id].position
    print(object_id, position)
m.end()
```

- `collisions` [A `CollisionManager`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/add_ons/collision_manager.md) for collisions from the previous frame:

```python
from magnebot import MagnebotController

m = MagnebotController()
m.init_floorplan_scene(scene="1a", layout=0, room=0)
for object_id in m.collisions.env_collisions:
    print(object_id)
m.end()
```

***

## Functions

#### \_\_init\_\_

**`MagnebotController()`**

**`MagnebotController(port=1071, launch_build=True, screen_width=256, screen_height=256, random_seed=None, skip_frames=10, check_pypi_version=True)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| port |  int  | 1071 | The port number. |
| launch_build |  bool  | True | If True, automatically launch the build. If one doesn't exist, download and extract the correct version. Set this to False to use your own build, or (if you are a backend developer) to use Unity Editor. |
| screen_width |  int  | 256 | The width of the screen in pixels. |
| screen_height |  int  | 256 | The height of the screen in pixels. |
| random_seed |  int  | None | The seed used for random numbers. If None, this is chosen randomly. In the Magnebot API this is used only when randomly selecting a start position for the Magnebot (see the `room` parameter of `init_floorplan_scene()`). The same random seed is used in higher-level APIs such as the Transport Challenge. |
| skip_frames |  int  | 10 | The build will return output data this many physics frames per simulation frame (communicate() call). This will greatly speed up the simulation, but eventually there will be a noticeable loss in physics accuracy. If you want to render every frame, set this to 0. |
| check_pypi_version |  bool  | True | If True, compare the locally installed version of TDW and Magnebot to the most recent versions on PyPi. |

***

### Scene Setup

These functions should be sent at the start of the simulation.

#### init_scene

**`self.init_scene()`**

Initialize the Magnebot in an empty test room.

```python
from magnebot import MagnebotController

m = MagnebotController()
m.init_scene()

# Your code here.

m.end()
```

#### init_floorplan_scene

**`self.init_floorplan_scene(scene, layout)`**

**`self.init_floorplan_scene(scene, layout, room=None)`**

Initialize a scene, populate it with objects, and add the Magnebot.

It might take a few minutes to initialize the scene. You can call `init_scene()` more than once to reset the simulation; subsequent resets at runtime should be extremely fast.

Set the `scene` and `layout` parameters in `init_scene()` to load an interior scene with furniture and props. Set the `room` to spawn the avatar in the center of a specific room.

```python
from magnebot import MagnebotController

m = MagnebotController()
m.init_floorplan_scene(scene="2b", layout=0, room=1)

# Your code here.

m.end()
```

Valid scenes, layouts, and rooms:

| `scene` | `layout` | `room` |
| --- | --- | --- |
| 1a, 1b, 1c | 0, 1, 2 | 0, 1, 2, 3, 4, 5, 6 |
| 2a, 2b, 2c | 0, 1, 2 | 0, 1, 2, 3, 4, 5, 6, 7, 8 |
| 4a, 4b, 4c | 0, 1, 2 | 0, 1, 2, 3, 4, 5, 6, 7 |
| 5a, 5b, 5c | 0, 1, 2 | 0, 1, 2, 3 |

Images of each scene+layout combination can be found [here](https://github.com/alters-mit/magnebot/tree/master/doc/images/floorplans). Images are named `[scene]_[layout].jpg` For example, the image for scene "2a" layout 0 is: `2a_0.jpg`.

Images of where each room in a scene is can be found [here](https://github.com/alters-mit/magnebot/tree/master/doc/images/rooms). Images are named `[scene].jpg` For example, the image for scene "2a" layout 0 is: `2.jpg`.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  str |  | The name of an interior floorplan scene. Each number (1, 2, etc.) has a different shape, different rooms, etc. Each letter (a, b, c) is a cosmetically distinct variant with the same floorplan. |
| layout |  int |  | The furniture layout of the floorplan. Each number (0, 1, 2) will populate the floorplan with different furniture in different positions. |
| room |  int  | None | The index of the room that the Magnebot will spawn in the center of. If None, the room will be chosen randomly. |

_Returns:_  An `ActionStatus` (always success).

***

### Movement

These functions move or turn the Magnebot. [Read this for more information about movement and collision detection.](../movement.md)

#### turn_by

**`self.turn_by(angle)`**

**`self.turn_by(angle, aligned_at=1)`**

Turn the Magnebot by an angle.

While turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| angle |  float |  | The target angle in degrees. Positive value = clockwise turn. |
| aligned_at |  float  | 1 | If the difference between the current angle and the target angle is less than this value, then the action is successful. |

_Returns:_  An `ActionStatus` indicating whether the Magnebot succeeded in turning and if not, why.

#### turn_to

**`self.turn_to(target)`**

**`self.turn_to(target, aligned_at=1)`**

Turn the Magnebot to face a target object or position.

While turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  Union[int, Dict[str, float] |  | The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array. |
| aligned_at |  float  | 1 | If the difference between the current angle and the target angle is less than this value, then the action is successful. |

_Returns:_  An `ActionStatus` indicating whether the Magnebot succeeded in turning and if not, why.

#### move_by

**`self.move_by(distance)`**

**`self.move_by(distance, arrived_at=0.1)`**

Move the Magnebot forward or backward by a given distance.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| distance |  float |  | The target distance. If less than zero, the Magnebot will move backwards. |
| arrived_at |  float  | 0.1 | If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful. |

_Returns:_  An `ActionStatus` indicating whether the Magnebot succeeded in moving and if not, why.

#### move_to

**`self.move_to(target)`**

**`self.move_to(target, arrived_at=0.1, aligned_at=1)`**

Move to a target object or position. This combines turn_to() followed by move_by().


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  Union[int, Dict[str, float] |  | The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array. |
| arrived_at |  float  | 0.1 | If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful. |
| aligned_at |  float  | 1 | If the difference between the current angle and the target angle is less than this value, then the action is successful. |

_Returns:_  An `ActionStatus` indicating whether the Magnebot succeeded in moving and if not, why.

#### reset_position

**`self.reset_position()`**

Reset the Magnebot so that it isn't tipping over.
This will rotate the Magnebot to the default rotation (so that it isn't tipped over) and move the Magnebot to the nearest empty space on the floor.
It will also drop any held objects.

This will be interpreted by the physics engine as a _very_ sudden and fast movement.
This action should only be called if the Magnebot is a position that will prevent the simulation from continuing (for example, if the Magnebot fell over).

_Returns:_  An `ActionStatus` indicating whether the Magnebot reset its position and if not, why.

***

### Arm Articulation

These functions move and bend the joints of the Magnebots's arms.

During an arm articulation action, the Magnebot is always "immovable", meaning that its wheels are locked and it isn't possible for its root object to move or rotate.

For more information regarding how arm articulation works, [read this](../arm_articulation.md).

#### reach_for

**`self.reach_for(target, arm)`**

**`self.reach_for(target, arm, absolute=True, arrived_at=0.125, orientation_mode=OrientationMode.auto, target_orientation=TargetOrientation.auto)`**

Reach for a target position. The action ends when the magnet is at or near the target position, or if it fails to reach the target.
The Magnebot may try to reach for the target multiple times, trying different IK orientations each time, or no times, if it knows the action will fail.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  Union[Dict[str, float] |  | The target position. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array. |
| arm |  Arm |  | [The arm that will reach for the target.](arm.md) |
| absolute |  bool  | True | If True, `target` is in absolute world coordinates. If `False`, `target` is relative to the position and rotation of the Magnebot. |
| arrived_at |  float  | 0.125 | If the magnet is this distance or less from `target`, then the action is successful. |
| orientation_mode |  OrientationMode  | OrientationMode.auto | [The orientation mode.](../arm_articulation.md) |
| target_orientation |  TargetOrientation  | TargetOrientation.auto | [The target orientation.](../arm_articulation.md) |

_Returns:_  An `ActionStatus` indicating whether the Magnebot's magnet reached the target position and if not, why.

#### grasp

**`self.grasp(target, arm)`**

**`self.grasp(target, arm, orientation_mode=OrientationMode.auto, target_orientation=TargetOrientation.auto)`**

Try to grasp a target object.
The action ends when either the Magnebot grasps the object, can't grasp it, or fails arm articulation.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  int |  | The ID of the target object. |
| arm |  Arm |  | [The arm that will reach for and grasp the target.](arm.md) |
| orientation_mode |  OrientationMode  | OrientationMode.auto | [The orientation mode.](../arm_articulation.md) |
| target_orientation |  TargetOrientation  | TargetOrientation.auto | [The target orientation.](../arm_articulation.md) |

_Returns:_  An `ActionStatus` indicating whether the Magnebot succeeded in grasping the object and if not, why.

#### drop

**`self.drop(target, arm)`**

**`self.drop(target, arm, wait_for_object=True)`**

Drop an object held by a magnet.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  int |  | The ID of the object currently held by the magnet. |
| arm |  Arm |  | [The arm of the magnet holding the object.](arm.md) |
| wait_for_object |  bool  | True | If True, the action will continue until the object has finished falling. If False, the action advances the simulation by exactly 1 frame. |

_Returns:_  An `ActionStatus` indicating whether the Magnebot succeeded in dropping the object and if not, why.

#### reset_arm

**`self.reset_arm(arm)`**

Reset the Magnebot so that it isn't tipping over.
This will rotate the Magnebot to the default rotation (so that it isn't tipped over) and move the Magnebot to the nearest empty space on the floor.
It will also drop any held objects.

This will be interpreted by the physics engine as a _very_ sudden and fast movement.
This action should only be called if the Magnebot is a position that will prevent the simulation from continuing (for example, if the Magnebot fell over).


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| arm |  Arm |  | [The arm to reset.](arm.md) |

_Returns:_  An `ActionStatus` indicating whether the Magnebot reset its arm and if not, why.

***

### Camera

These commands rotate the Magnebot's camera or add additional camera to the scene. They advance the simulation by exactly 1 frame.

#### rotate_camera

**`self.rotate_camera(roll, pitch, yaw)`**

Rotate the Magnebot's camera by the (roll, pitch, yaw) axes.

Each axis of rotation is constrained by the following limits:

| Axis | Minimum | Maximum |
| --- | --- | --- |
| roll | -55 | 55 |
| pitch | -70 | 70 |
| yaw | -85 | 85 |


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| roll |  float |  | The roll angle in degrees. |
| pitch |  float |  | The pitch angle in degrees. |
| yaw |  float |  | The yaw angle in degrees. |

_Returns:_  An `ActionStatus` indicating whether the Magnebot rotated its camera freely or if the rotation was clamped at a limit.

#### reset_camera

**`self.reset_camera()`**

Reset the rotation of the Magnebot's camera to its default angles.

_Returns:_  An `ActionStatus` (always success).

***

### Misc.

These are utility functions that won't advance the simulation by any frames.

#### get_visible_objects

**`self.get_visible_objects()`**

Get all objects visible to the Magnebot.

_Returns:_  A list of IDs of visible objects.

#### end

**`self.end()`**

End the simulation. Terminate the build process.

#### get_occupancy_position

**`self.get_occupancy_position(i, j)`**

Converts the position `(i, j)` in the occupancy map to `(x, z)` worldspace coordinates.

This only works if you've loaded an occupancy map via `self.init_floorplan_scene()`.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| i |  int |  | The i coordinate in the occupancy map. |
| j |  int |  | The j coordinate in the occupancy map. |

_Returns:_  Tuple: (x coordinate; z coordinate) of the corresponding worldspace position.

***

### Low-level

These are low-level functions that you are unlikely to ever need to use.

##### communicate

**`self.communicate(commands)`**

Send commands and receive output data in response.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| commands |  Union[dict, List[dict] |  | A list of JSON commands. |

_Returns:_  The output data from the build.

##### get_add_object

**`self.get_add_object(model_name, object_id)`**

**`self.get_add_object(model_name, position={"x" 0, rotation={"x" 0, library="", object_id)`**

Returns a valid add_object command.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| model_name |  str |  | The name of the model. |
| position |  | {"x" 0 | The position of the model. |
| rotation |  | {"x" 0 | The starting rotation of the model, in Euler angles. |
| library |  str  | "" | The path to the records file. If left empty, the default library will be selected. See `ModelLibrarian.get_library_filenames()` and `ModelLibrarian.get_default_library()`. |
| object_id |  int |  | The ID of the new object. |

_Returns:_  An add_object command that the controller can then send.

##### get_add_material

**`self.get_add_material(material_name)`**

**`self.get_add_material(material_name, library="")`**

Returns a valid add_material command.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| material_name |  str |  | The name of the material. |
| library |  str  | "" | The path to the records file. If left empty, the default library will be selected. See `MaterialLibrarian.get_library_filenames()` and `MaterialLibrarian.get_default_library()`. |

_Returns:_  An add_material command that the controller can then send.

##### get_add_scene

**`self.get_add_scene(scene_name)`**

**`self.get_add_scene(scene_name, library="")`**

Returns a valid add_scene command.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene_name |  str |  | The name of the scene. |
| library |  str  | "" | The path to the records file. If left empty, the default library will be selected. See `SceneLibrarian.get_library_filenames()` and `SceneLibrarian.get_default_library()`. |

_Returns:_  An add_scene command that the controller can then send.

##### get_add_hdri_skybox

**`self.get_add_hdri_skybox(skybox_name)`**

**`self.get_add_hdri_skybox(skybox_name, library="")`**

Returns a valid add_hdri_skybox command.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| skybox_name |  str |  | The name of the skybox. |
| library |  str  | "" | The path to the records file. If left empty, the default library will be selected. See `HDRISkyboxLibrarian.get_library_filenames()` and `HDRISkyboxLibrarian.get_default_library()`. |

_Returns:_  An add_hdri_skybox command that the controller can then send.

##### get_add_humanoid

**`self.get_add_humanoid(humanoid_name, object_id)`**

**`self.get_add_humanoid(humanoid_name, position={"x" 0, rotation={"x" 0, library="", object_id)`**

Returns a valid add_humanoid command.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| humanoid_name |  str |  | The name of the humanoid. |
| position |  | {"x" 0 | The position of the humanoid. |
| rotation |  | {"x" 0 | The starting rotation of the humanoid, in Euler angles. |
| library |  str  | "" | The path to the records file. If left empty, the default library will be selected. See `HumanoidLibrarian.get_library_filenames()` and `HumanoidLibrarian.get_default_library()`. |
| object_id |  int |  | The ID of the new object. |

_Returns:_  An add_humanoid command that the controller can then send.

##### get_add_humanoid_animation

**`self.get_add_humanoid_animation(humanoid_animation_name)`**

**`self.get_add_humanoid_animation(humanoid_animation_name, library="")`**

Returns a valid add_humanoid_animation command and the record (which you will need to play an animation).


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| humanoid_animation_name |  str |  | The name of the animation. |
| library |  | "" | The path to the records file. If left empty, the default library will be selected. See `HumanoidAnimationLibrarian.get_library_filenames()` and `HumanoidAnimationLibrarian.get_default_library()`. |

_Returns:_  An add_humanoid_animation command that the controller can then send.

##### get_add_robot

**`self.get_add_robot(name, robot_id)`**

**`self.get_add_robot(name, robot_id, position=None, rotation=None, library="")`**

Returns a valid add_robot command.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| name |  str |  | The name of the robot. |
| robot_id |  int |  | A unique ID for the robot. |
| position |  Dict[str, float] | None | The initial position of the robot. If None, the position will be (0, 0, 0). |
| rotation |  Dict[str, float] | None | The initial rotation of the robot in Euler angles. |
| library |  str  | "" | The path to the records file. If left empty, the default library will be selected. See `RobotLibrarian.get_library_filenames()` and `RobotLibrarian.get_default_library()`. |

_Returns:_  An `add_robot` command that the controller can then send.

##### get_version

**`self.get_version()`**

Send a send_version command to the build.

_Returns:_  The TDW version and the Unity Engine version.

##### get_unique_id

**`Controller(object).get_unique_id()`**

_This is a static function._

Generate a unique integer. Useful when creating objects.

_Returns:_  The new unique ID.

##### get_frame

**`Controller(object).get_frame(frame)`**

_This is a static function._

Converts the frame byte array to an integer.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| frame |  bytes |  | The frame as bytes. |

_Returns:_  The frame as an integer.

##### launch_build

**`Controller(object).launch_build()`**

**`Controller(object).launch_build(port=1071)`**

_This is a static function._

Launch the build. If a build doesn't exist at the expected location, download one to that location.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| port |  int  | 1071 | The socket port. |



