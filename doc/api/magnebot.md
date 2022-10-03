# Magnebot

`from magnebot import Magnebot`

The Magnebot agent is a high-level robotics-like API for [TDW](https://github.com/threedworld-mit/tdw) This high-level API supports:

- Creating a complex interior environment
- Directional movement
- Turning
- Arm articulation via inverse kinematics (IK)
- Grasping and dropping objects
- Image rendering
- Scene state metadata

The Magnebot has various [actions](actions/action.md). Each action has a start and end, and has a [status](action_status.md) that indicates if it is ongoing, if it succeeded, or if it failed (and if so, why).

***

## Basic usage

You can add a Magnebot to a regular TDW controller:

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot
from magnebot.action_status import ActionStatus

m = Magnebot(robot_id=0, position={"x": 0.5, "y": 0, "z": -1})
c = Controller()
c.add_ons.append(m)
c.communicate(TDWUtils.create_empty_room(12, 12))
m.move_by(1)
while m.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate({"$type": "terminate"})
```

It is possible to create a multi-agent Magnebot simulation simply by adding more Magnebot agents:

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot
from magnebot.action_status import ActionStatus

m0 = Magnebot(robot_id=0, position={"x": 0.5, "y": 0, "z": -1})
m1 = Magnebot(robot_id=1, position={"x": -0.5, "y": 0, "z": 1})
c = Controller()
c.add_ons.extend([m0, m1])
c.communicate(TDWUtils.create_empty_room(12, 12))
m0.move_by(1)
m1.move_by(-2)
while m0.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate({"$type": "terminate"})
```

For a simplified single-agent API, see [`MagnebotController`](magnebot_controller.md):

```python
from magnebot import MagnebotController

m = MagnebotController()
m.init_scene()
m.move_by(2)
m.end()
```

***

## Skipped frames

The `Magnebot` and `MagnebotController` were originally the same code--the controller was a hard-coded single-agent simulation.

The Magnebot has been designed so that a certain number of physics frames will be skipped per frame that actually returns data back to the controller. The `MagnebotController` does this automatically but you can easily add this to your simulation with a [`StepPhysics`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/add_ons/step_physics.md) object:

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.step_physics import StepPhysics
from magnebot.magnebot import Magnebot

m = Magnebot()
s = StepPhysics(10)
c = Controller()
c.add_ons.extend([m, s])
c.communicate(TDWUtils.create_empty_room(12, 12))
print(m.dynamic.transform.position)
c.communicate({"$type": "terminate"})
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

#### Union[int, Dict[str, float], np.ndarray]

Parameters of type `Union[int, Dict[str, float], np.ndarray]` can be either a Vector3, an [x, y, z] numpy array, or an integer (an object ID).

#### Arm

All parameters of type `Arm` require you to import the [Arm enum class](arm.md):

```python
from magnebot import Arm

print(Arm.left)
```

***

***

## Fields

- `static` [Cached static data for the Magnebot](magnebot_static.md) such as the IDs and segmentation colors of each joint:

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot.magnebot import Magnebot

m = Magnebot()
c = Controller()
c.add_ons.append(m)
c.communicate(TDWUtils.create_empty_room(12, 12))
for arm_joint in m.static.arm_joints:
    joint_id = m.static.arm_joints[arm_joint]
    segmentation_color = m.static.joints[joint_id].segmentation_color
    print(arm_joint, joint_id, segmentation_color)
c.communicate({"$type": "terminate"})
```

- `dynamic` [Per-frame dynamic data for the Magnebot](magnebot_dynamic.md) such as its position and images:

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot.magnebot import Magnebot

m = Magnebot()
c = Controller()
c.add_ons.append(m)
c.communicate(TDWUtils.create_empty_room(12, 12))
print(m.dynamic.transform.position)
c.communicate({"$type": "terminate"})
```

- `action` The Magnebot's current [action](actions/action.md). Can be None (no ongoing action).

- `image_frequency` This sets [how often images are captured](image_frequency.md).

- `collision_detection` [The collision detection rules.](collision_detection.md) This determines whether the Magnebot will immediately stop moving or turning when it collides with something.

- `camera_rpy` The current (roll, pitch, yaw) angles of the Magnebot's camera in degrees as a numpy array. This is handled outside of `self.state` because it isn't calculated using output data from the build. See: `Magnebot.CAMERA_RPY_CONSTRAINTS` and `self.rotate_camera()`

***

## Functions

#### \_\_init\_\_

**`Magnebot()`**

**`Magnebot(robot_id=0, position=None, rotation=None, image_frequency=ImageFrequency.once, parent_camera_to_torso=True, visual_camera_mesh=False, check_version=True)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| robot_id |  int  | 0 | The ID of the robot. |
| position |  Dict[str, float] | None | The position of the robot. If None, defaults to `{"x": 0, "y": 0, "z": 0}`. |
| rotation |  Dict[str, float] | None | The rotation of the robot in Euler angles (degrees). If None, defaults to `{"x": 0, "y": 0, "z": 0}`. |
| image_frequency |  ImageFrequency  | ImageFrequency.once | [The frequency of image capture.](image_frequency.md) |
| parent_camera_to_torso |  bool  | True | If True, the camera will be parented to the Magnebot's torso. If False, the camera will be parented to the Magnebot's column. |
| visual_camera_mesh |  bool  | False | If True, the camera will receive a visual mesh. The mesh won't have colliders and won't respond to physics. If False, the camera won't have a visual mesh. |
| check_version |  bool  | True | If True, check whether an update to the Magnebot API or TDW API is available. |

***

### Movement

These functions move or turn the Magnebot. [Read this for more information about movement and collision detection.](../manual/magnebot/movement.md)

#### turn_by

**`self.turn_by(angle)`**

**`self.turn_by(angle, aligned_at=1)`**

Turn the Magnebot by an angle.

While turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| angle |  float |  | The target angle in degrees. Positive value = clockwise turn. |
| aligned_at |  float  | 1 | If the difference between the current angle and the target angle is less than this value, then the action is successful. |

#### turn_to

**`self.turn_to(target)`**

**`self.turn_to(target, aligned_at=1)`**

Turn the Magnebot to face a target object or position.

While turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  Union[int, Dict[str, float] |  | The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array. |
| aligned_at |  float  | 1 | If the difference between the current angle and the target angle is less than this value, then the action is successful. |

#### move_by

**`self.move_by(distance)`**

**`self.move_by(distance, arrived_at=0.1)`**

Move the Magnebot forward or backward by a given distance.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| distance |  float |  | The target distance. If less than zero, the Magnebot will move backwards. |
| arrived_at |  float  | 0.1 | If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful. |

#### move_to

**`self.move_to(target)`**

**`self.move_to(target, arrived_at=0.1, aligned_at=1, arrived_offset=0)`**

Move to a target object or position. This combines turn_to() followed by move_by().

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  Union[int, Dict[str, float] |  | The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array. |
| arrived_at |  float  | 0.1 | If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful. |
| aligned_at |  float  | 1 | If the difference between the current angle and the target angle is less than this value, then the action is successful. |
| arrived_offset |  float  | 0 | Offset the arrival position by this value. This can be useful if the Magnebot needs to move to an object but shouldn't try to move to the object's centroid. This is distinct from `arrived_at` because it won't affect the Magnebot's braking solution. |

#### stop

**`self.stop()`**

Stop the Magnebot's wheels at their current positions.

#### reset_position

**`self.reset_position()`**

Reset the Magnebot so that it isn't tipping over.
This will rotate the Magnebot to the default rotation (so that it isn't tipped over) and move the Magnebot to the nearest empty space on the floor.
It will also drop any held objects.

This will be interpreted by the physics engine as a _very_ sudden and fast movement.
This action should only be called if the Magnebot is a position that will prevent the simulation from continuing (for example, if the Magnebot fell over).

***

### Arm Articulation

These functions move and bend the joints of the Magnebots's arms.

During an arm articulation action, the Magnebot is always "immovable", meaning that its wheels are locked and it isn't possible for its root object to move or rotate.

For more information regarding how arm articulation works, [read this](../manual/magnebot/arm_articulation.md).

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
| orientation_mode |  OrientationMode  | OrientationMode.auto | [The orientation mode.](ik/orientation_mode.md) |
| target_orientation |  TargetOrientation  | TargetOrientation.auto | [The target orientation.](ik/target_orientation.md) |

#### grasp

**`self.grasp(target, arm)`**

**`self.grasp(target, arm, orientation_mode=OrientationMode.auto, target_orientation=TargetOrientation.auto)`**

Try to grasp a target object.
The action ends when either the Magnebot grasps the object, can't grasp it, or fails arm articulation.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  int |  | The ID of the target object. |
| arm |  Arm |  | [The arm that will reach for and grasp the target.](arm.md) |
| orientation_mode |  OrientationMode  | OrientationMode.auto | [The orientation mode.](ik/orientation_mode.md) |
| target_orientation |  TargetOrientation  | TargetOrientation.auto | [The target orientation.](ik/target_orientation.md) |

#### drop

**`self.drop(target, arm)`**

**`self.drop(target, arm, wait_for_object=True)`**

Drop an object held by a magnet.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  int |  | The ID of the object currently held by the magnet. |
| arm |  Arm |  | [The arm of the magnet holding the object.](arm.md) |
| wait_for_object |  bool  | True | If True, the action will continue until the object has finished falling. If False, the action advances the simulation by exactly 1 frame. |

#### reset_arm

**`self.reset_arm(arm)`**

Reset an arm to its neutral position.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| arm |  Arm |  | [The arm to reset.](arm.md) |

***

### Torso

These functions adjust the Magnebot's torso..

During a torso action, the Magnebot is always "immovable", meaning that its wheels are locked and it isn't possible for its root object to move or rotate.

#### slide_torso

**`self.slide_torso(height)`**

Slide the Magnebot's torso up or down.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| height |  float |  | The height of the torso. Must be between `magnebot.constants.TORSO_MIN_Y` and `magnebot.constants.TORSO_MAX_Y`. |

***

### Camera

These functions rotate the Magnebot's camera. They advance the simulation by exactly 1 frame.

#### rotate_camera

**`self.rotate_camera()`**

**`self.rotate_camera(roll=0, pitch=0, yaw=0)`**

Rotate the Magnebot's camera by the (roll, pitch, yaw) axes.

Each axis of rotation is constrained by the following limits:

| Axis | Minimum | Maximum |
| --- | --- | --- |
| roll | -55 | 55 |
| pitch | -70 | 70 |
| yaw | -85 | 85 |

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| roll |  float  | 0 | The roll angle in degrees. |
| pitch |  float  | 0 | The pitch angle in degrees. |
| yaw |  float  | 0 | The yaw angle in degrees. |

#### move_camera

**`self.move_camera(position)`**

**`self.move_camera(position, coordinate_space=CameraCoordinateSpace.relative_to_camera)`**

Move the Magnebot's camera.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| position |  Union[Dict[str, float] |  | The position of the camera. |
| coordinate_space |  CameraCoordinateSpace  | CameraCoordinateSpace.relative_to_camera | The [`CameraCoordinateSpace`](camera_coordinate_space.md), which is used to define what `position` means. |

#### reset_camera_rotation

**`self.reset_camera_rotation()`**

Reset the rotation of the Magnebot's camera to its default angles.

#### reset_camera_position

**`self.reset_camera_position()`**

Reset the Magnebot's camera to its initial position.

***

### RobotBase

These functions are inherited from the `RobotBase` parent class.

#### get_initialization_commands

**`self.get_initialization_commands()`**

This function gets called exactly once per add-on by the controller; don't call this function yourself!

_Returns:_  A list of commands that will initialize this add-on.

#### on_send

**`self.on_send(resp)`**

This is called after commands are sent to the build and a response is received.

This function is called automatically by the controller; you don't need to call it yourself.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| resp |  List[bytes] |  | The response from the build. |

#### reset

**`self.reset()`**

***

