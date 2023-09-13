# Changelog

## 2.2.7

- Fixed: Magnebot can't be used with Python 3.10 or newer.
  - (Backend) Added `ikpy/chain.py` with compatible numpy code.
- Fixed some example controllers and documentation code snippets.

## 2.2.6

- Required version of TDW is now >=1.11.22.0
- Fixed: Crash when running custom action example controllers because parameter `set_torso` is missing.
- Fixed: `reach_high.py` example controller doesn't work due to obsolete commands.

## 2.2.5

- Fixed: Crash when calling `magnebot.reset()`.
- Required version of TDW is now >=1.11.6.0

## 2.2.4

- Updated occupancy map API in the `ResetPosition` action.
- Required version of TDW is now >=1.11.4.0

## 2.2.3

- In `Magnebot`, added optional parameter `set_torso` to `drop()`, `grasp()`, `reach_for()`, and `reset_arm()`. The default value is True. If False, the torso won't be set at the *end* of the action.
- In `Magnebot`, added optional parameter `set_torso` to `move_by()`, `move_to()`, `turn_by()`, and `turn_to()`. The default value is True. If False the torso won't slide to its default position at the *start* of the action.
- `magnebot.slide_torso()` no longer sets the torso position at the end of the action.
- Updated documentation to explain the `set_torso` parameter:
  - `manual/magnebot/arm_articulation.md`
  - `manual/magnebot/grasp.md`
  - `manual/magnebot/movement.md`
- Required version of TDW is now >=1.11.3.0

## 2.2.2

- Added optional parameter `visual_camera_mesh_scale` to the Magnebot constructor.
- Required version of TDW is now >=1.11.0.0

## 2.2.1

- Fixed: `controllers/examples/magnebot/multi_magnebot.py` doesn't work.
- Fixed: `util.get_data()` references `Robot` output data, which is obsolete.

## 2.2.0

- Added a new action: `MoveCamera(position, coordinate_space)`, which can be called via `magnebot.move_camera(position, coordinate_space)` or `magnebot_controller.move_camera(position, coordinate_space)`.
- Added a new action: `LookAt(target)`, which can be called via `magnebot.look_at(target)` or `magnebot_controller.look_at(target)`.
- The `reset_camera()` action now resets the camera's position.
- Added optional parameters `position` and `rotation` to `reset_camera()` to handle situations where the user wants to reset on the position or rotation.
- Added new parameter `parent_camera_to_torso` to the `Magnebot` constructor. If True, the camera will be parented to the Magnebot's torso. If False, the camera will be parented to the Magnebot's column. Default = True.
- Added new parameter `visual_camera_mesh` to the `Magnebot` constructor. If True, the camera will receive a visual mesh. The mesh won't have colliders and won't respond to physics. If False, the camera won't have a visual mesh. Default = False.
- Renamed parameter `_position` in `SlideTorso` to `position`.
- Added test controller: `visual_camera.py`
- Added example controllers: `magnebot/look_at.py` and `magnebot_controller/look_at.py`
- Renamed `manual/magnebot/rotate_camera.md` to `manul/magnebot/camera.md` and added documentation for camera movement and visualization.
- Renamed `manual/magnebot_controller/rotate_camera.md` to `manul/magnebot_controller/camera.md` and added documentation for camera movement.
- Required version of TDW is now >=1.10.8.0

## 2.1.0

- Added a new action: `SlideTorso(height)`, which can be called via `magnebot.slide_torso(height)` or `magnebot_controller.slide_torso(height)`.

## 2.0.7

- Fixed required version of TDW in setup.py (>=1.10.6.0)

## 2.0.6

- Required version of TDW is now >=1.10.6.0

## 2.0.5

- Required version of TDW is now >=1.10.5.0
- Added some code to ensure that robot joint IDs are explicitly set so that log files work correctly.

## 2.0.4

- Required version of TDW is now >=1.10.2.0
- Fixed import statements and other errors for `Action` API documents
- Added inherited fields to `MagnebotDynamic` API document
- Fixed broken links in various documents due to the TDW v1.10 release
- (Backend) Added field `robot_index` to `MagnebotStatic` (inherited from `RobotStatic`)
- (Backend) Removed constructor parameters from `MagnebotDynamic`: `robot_id`, `body_parts`, `previous`
- (Backend) Added constructor parameters to `MagnebotDynamic`: `static` (`MagnebotStatic` object)
- (Backend) Updated doc_gen.py for the latest version of PyMDDoc

## 2.0.3

- Required version of TDW is now >=1.10.0.0
- Removed `CompositeObjects` from output data types that can be used by `util.get_data(resp, d_type)` because `CompositeObjects` has been removed as of TDW v1.10.0

## 2.0.2

- Required version of TDW is now >=1.9.9.2
- Updated example controllers to set `scale_mass=False` (see changelog of TDW v1.9.9)

## 2.0.1

- Fixed: `'NoneType' object has no attribute 'transform'` in minimal `Magnebot` example because the add-on isn't appended to `c.add_ons`

## 2.0.0

**This is a MAJOR uprdate to the Magnebot API. Please read this changelog carefully.**

To update:

- `pip3 install tdw -U`
- `pip3 install magnebot -U`
- [Download the latest release of the TDW build](https://github.com/threedworld-mit/tdw/releases/latest/)

### Changes to the Magnebot agent

**The Magnebot agent is now handled as a separate [`Magnebot`](api/magnebot.md) class.** [Read this for more information.](manual/magnebot/overview.md) This *greatly* expands the usefulness of the Magnebot API:

- The Magnebot API can now be added to *any* TDW controller
- The Magnebot API now supports multi-agent simulations (including non-Magnebot agents)
- The Magnebot agent's actions can be interrupted mid-motion
- Joint drive force limits have been adjusted (see below).

### Changes to the controller

#### 1. Renamed `Magnebot` to `MagnebotController`

In Magnebot 1.3.2:

```python
from magnebot import Magnebot

c = Magnebot(launch_build=True)
c.init_scene()
```

In Magnebot 2.0.0:

```python
from magnebot import MagnebotController

c = MagnebotController(launch_build=True)
c.init_scene()
```

#### 2. By default, the build launches automatically

This aligns the behavior in `MagnebotController` with the behavior in `Controller`. [Read this for more information.](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/core_concepts/launch_build.md)

Magnebot 1.3.2:

```python
from magnebot import Magnebot

c = Magnebot()
c.init_scene()
```

Magnebot 2.0.0:

```python
from magnebot import MagnebotController

c = MagnebotController(launch_build=False)
c.init_scene()
```

#### 3. Other changes to the controller constructor

- Removed `auto_save_images`
- Removed `debug`
- Removed `images_directory`
- Removed `img_is_png`

#### 4. Reorganized output data

| Magnebot 1.3.2                  | Magnebot 2.0.0                                               |
| ------------------------------- | ------------------------------------------------------------ |
| `self.state.magnebot_transform` | `self.magnebot.dynamic.transform`                            |
| `self.state.joint_positions`    | `self.magnebot.dynamic.joints`<br>See: `joints[joint_id].position` |
| `self.state.joint_angles`       | `self.magnebot.dynamic.joints`<br>See: `joints[joint[id]].angles` |
| `self.state.held`               | `self.magnebot.dynamic.held`                                 |
| `self.state.object_transforms`  | `self.objects.transforms`                                    |
| `self.state.projection_matrix`  | `self.magnebot.dynamic.projection_matrix`                    |
| `self.state.camera_matrix`      | `self.magnebot.dynamic.camera_materix`                       |
| `self.state.images`             | `self.magnebot.dynamic.images`                               |
| `self.third_person_images`      | *Removed (see below)*                                        |
|                                 | `self.magnebot.top`                                          |
| `self.colliding_objects`        | `self.magnebot.dynamic.collisions_with_objects`              |
| `self.colliding_with_wall`      | `self.magnebot.dynamic.collisions_with_environment` *A dictionary instead of a boolean* |
|                                 | `self.magnebot.dynamic.collisions_with_self`                 |
| `self.objects_static`           | `self.objects.objects_static`                                |
| `self.magnebot_static`          | `self.magnebot.static`                                       |

##### Static object data

Moved `ObjectStatic` from `magnebot.object_static.ObjectStatic` to [`tdw.object_data.object_static.ObjectStatic`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/object_data/object_static.md).

| Magnebot 1.3.2       | Magnebot 2.2.0       |
| -------------------- | -------------------- |
| `name`               | `name`               |
| `object_id`          | `object_id`          |
| `mass`               | `mass`               |
| `segmentation_color` | `segmentation_color` |
| `size`               | `size`               |
|                      | `category`           |
|                      | `kinematic`          |
|                      | `dynamic_friction`   |
|                      | `static_friction`    |
|                      | `bounciness`         |

##### Static Magnebot data

[`MagnebotStatic`](api/magnebot_static.md) is now a subclass of [`RobotStatic`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/robot_data/robot_static.md).

| Magnebot 1.3.2 | Magnebot 2.2.0                                       |
| -------------- | ---------------------------------------------------- |
| `joints`       | `joints` (See **Static joint data** below)           |
| `body_parts`   | `body_parts`                                         |
| `arm_joints`   | `arm_joints`                                         |
| `wheels`       | `wheels`                                             |
| `magnets`      | `magnets`                                            |
| `root`         | *Removed*                                            |
|                | `robot_id` *The ID of the Magnebot*                  |
|                | `joint_ids_by_name` *A dictionary of joint names*    |
|                | `non_moving` *A dictionary of non-moving body parts* |
|                | `immovable` *This is always False*                   |
|                | `avatar_id` *The ID of the Magnebot's camera*        |

##### Static joint data

Moved `JointStatic` from `magnebot.joint_static.JointStatic` to [`tdw.robot_data.joint_static.JointStatic`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/robot_data/joint_static.md).

| Magnebot 1.3.2       | Magnebot 2.0.0                                               |
| -------------------- | ------------------------------------------------------------ |
| `id`                 | `joint_id`                                                   |
| `mass`               | `mass`                                                       |
| `segmentation_color` | `segmentation_color`                                         |
| `name`               | `name`                                                       |
| `drives`             | `drives`                                                     |
| `joint_type`         | `joint_type` *Now a [`JointType`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/robot_data/joint_type.md) value instead of a string* |
|                      | `immovable`                                                  |
|                      | `root`                                                       |
|                      | `parent_id`                                                  |

##### Image data functions

| Magnebot 1.3.2                  | Magnebot 2.0.0                             |
| ------------------------------- | ------------------------------------------ |
| `self.state.get_pil_images()`   | `self.magnebot.dynamic.get_pil_images()`   |
| `self.state.get_depth_values()` | `self.magnebot.dynamic.get_depth_values()` |
| `self.state.get_point_cloud()`  | `self.magnebot.dynamic.get_point_cloud()`  |

Magnebot 1.3.2:

```python
from magnebot import Magnebot

c = Magnebot()
c.init_floorplan_scene(scene="1a", layout=0, room=0)
print("Objects")
for object_id in c.objects_static:
    print(object_id,
          c.objects_static[object_id].mass,
          c.state.object_transforms[object_id].position)
print("Magnebot")
print(c.state.magnebot_transform.position)
for arm_joint in c.magnebot_static.static.arm_joints:
    joint_id = c.magnebot_static.arm_joints[arm_joint]
    print(arm_joint, c.state.joint_angles[joint_id])
point_cloud = c.state.get_point_cloud()
print(point_cloud)
c.end()
```

Magnebot 2.0.0:

```python
from magnebot import MagnebotController

c = MagnebotController()
c.init_floorplan_scene(scene="1a", layout=0, room=0)
print("Objects")
for object_id in c.objects.objects_static:
    print(object_id, 
          c.objects.objects_static[object_id].mass,
          c.objects.transforms[object_id].position)
print("Magnebot")
print(c.magnebot.dynamic.transform.position)
for arm_joint in c.magnebot.static.arm_joints:
    joint_id = c.magnebot.static.arm_joints[arm_joint]
    print(arm_joint, c.magnebot.dynamic.joints[joint_id].angles)
point_cloud = c.magnebot.dynamic.get_point_cloud()
print(point_cloud)
c.end()
```

#### 5. Reorganized collision detection

Previously, collision detection output data was held in `self.colliding_object` and `self.colliding_walls`, while collision detection rules were set within the action functions. This has all been removed and reorganized. Now, collision data is stored in `self.magnebot.dynamic` and collision detection rules are stored in `self.magnebot.collision_detection`.

Magnebot 1.3.2:

```python
from magnebot import Magnebot, ActionStatus
from magnebot.collision_detection import CollisionDetection

c = Magnebot()
c.init_scene()
status = c.move_by(8)
assert status == ActionStatus.collision
c.move_by(-2, stop_on_collision=CollisionDetection(objects=True, walls=False, previous_was_same=True))
status = c.move_by(-2)
assert status == ActionStatus.success
c.end()
```

Magnebot 2.0.0:

```python
from magnebot import MagnebotController, ActionStatus

c = MagnebotController()
c.init_scene()
status = c.move_by(8)
assert status == ActionStatus.collision
c.magnebot.collision_detection.walls = False
status = c.move_by(-2)
assert status == ActionStatus.success
c.end()
```

#### 6. Other changes to fields

- Removed `self.auto_save_images`
- Removed `self.images_directory`
- Removed `self.camera_rpy`
- Added `self.rng` Random number generator (previously was a hidden field `self._rng`)
- Added `self.magnebot` The Magnebot agent (see above)
- Added `self.objects` The [`ObjectManager`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/add_ons/object_manager.md).

#### 7. Removed `self.add_third_person_camera()`

[Read this for more information.](manual/magnebot_controller/third_person_camera.md)

#### 8. Other changes to backend classes

- Removed `magnebot.collision_action.CollisionAction`
- Added [`magnebot.image_frequency.ImageFrequency`](api/image_frequency.md)
- Added `Action` classes (see below).
- Moved `Drive` from `magnebot.drive.Drive` to `tdw.robot_data.drive.Drive`
- Moved `Transform` from `magnebot.transform.Transform` to `tdw.object_data.transform.Transform`

### Changes to the Magnebot's actions

**There shouldn't be any significant difference in the Magnebot's behavior since the 1.3.2 release.**

Due to the entire API being refactored, there may be minor changes in Magnebot behavior. If you find any bugs or significant differences from Magnebot v1, let us know.

The `Magnebot` agent has an additional `stop()` action that isn't implemented in `MagnebotController`.

Actions are defined using [`Action`](api/actions/action.md) objects rather than functions. [Read this for more information.](manual/actions/overview.md)

### Changes to the documentation

Documentation has been split into "manual" and "API" sections. The "manual" section has documentation for `MagnebotController`, `Magnebot`, and `Action`.

### Changes to the example controllers

There are many more example controllers. Some examples were removed and some have been revised. There are example controllers for `MagnebotController`, `Magnebot` (single-agent), and `Magnebot` (multi-agent).

### Known issues

TDW 1.9.0 has been upgraded to Unity 2020.3.24. [As of Unity 2020.3.21](https://unity3d.com/unity/whats-new/2020.3.21), joint force limits use different measurement units. Unfortunately, the Unity documentation doesn't specify *what* the measurement units are. The force limits of the Magnebot's wheels, shoulders, elbows,  column, and wrists have been multiplied by 100 and the force limit of the torso prismatic joint has been multiplied by 1000; the resulting behavior seems to be nearly the same as previous behavior.

***

## 1.3.2

- Fixed: Crash when trying to add multiple third person cameras with `add_camera()` because the avatar ID is always `"c"`.

## 1.3.1

- Fixed: `AttributeError` when calling `init_scene()` because the wrong version of `ikpy` is installed. Now, `magnebot` will always install `ikpy` 3.1.
- Set required version of `tdw` to `>=1.8.25`

## 1.3.0

**This release introduces significant changes. Please read this changelog carefully.**

- **Major improvements to the precision and determinism of the Magnebot's move and turn actions.** 
  - The Magnebot uses special TDW commands to check its move or turn status during skipped frames (for example, whether it has reached a target distance over the course of a skipped frame). As the Magnebot approaches a turn distance or angle, its wheels will start to brake. This behavior only occurs in turn actions if `aligned_at <= 1` and in move actions if `arrived_at < 0.2`. The friction and force limits of the wheels will be reset the next time the Magnebot moves or turns.
  - **The overall possible precision of a Magnebot action is much lower**. The Magnebot can turn within approximately 0.2 degrees of a target angle (previously, the minimum was approximately 3 degrees). The Magnebot can move within approximately 0.01 meters of a target distance previously, the minimum was approximately 0.3 meters).
  - Because the Magnebot can check its position and rotation more frequently, **the overall physics determinism of the simulation is much better**. There is still some variance either between machines or operating systems--we're still not sure what the pattern is and why it occurs.
- Set the default value of `arrived_at` in the `move_by()` and `move_to()` actions to 0.1 (was 0.3).
- Set the default value of `aligned_at` in the `turn_by()`, `turn_to()`, and `move_to()` actions to 1 (was 3).
- Added optional parameter `target_position` to the `turn_by()` action. This is used internally and shouldn't be set by the user.
- `Magnebot` now checks whether the expected version of TDW is installed.
- Added benchmark controller: `precision.py` Test how precision in move and turn actions (`arrived_at` and `aligned_at` parameters) affects the speed of the action.
- Added benchmark controller: `movement_variance.py` Test how varied the movements of the Magnebot are between one machine and a "canonical" set of positions.

## 1.2.2

- (Backend): Removed `SceneEnvironment` (the Magnebot API now uses TDW's `SceneBounds` instead)

## 1.2.1

- **Fixed: `pip3 install magnebot` doesn't work.** This was due to `magnebot` requiring a fork of `ikpy` that isn't on PyPi. Now, `magnebot` requires the PyPi version and a modified version of the relevant script (`link.py`) is included in `magnebot/ikpy/link.py`.

## 1.2.0

**This release introduces significant changes. Please read this changelog carefully.** Below is a brief summary:

- `grasp()` and `reach_for()` are much faster and accurate. For more information, [read this.](https://github.com/alters-mit/magnebot/blob/1.2.0/doc/arm_articulation.md)
- Scene initialization has been split into `init_scene()` and `init_floorplan_scene()` and custom scene setup overall has been simplified. For more information, [read this.](https://github.com/alters-mit/magnebot/blob/1.2.0/doc/scene.md)
- Movement actions such as `move_by()` and `turn_to()` have the option of fine-tuning collision detection rules. For more information, [read this.](https://github.com/alters-mit/magnebot/blob/1.2.0/doc/movement.md)

**To upgrade to Magnebot 1.2.0, you must do the following:** 

- If you installed from PyPi: 
  1. `pip3 uninstall ikpy`
  2. `pip3 uninstall magnebot`
  3. `pip3 install magnebot`
- If you installed from the source code of this repo:
  1. `pip3 uninstall ikpy`
  2. `pip3 uninstall magnebot`
  3. `cd path/to/magnebot`
  4. `pip3 install -e .`

***

- **Rewrote documentation for custom APIs:**
  - Rewrote `custom_apis.md`
  - Added: `doc/arm_articulation.md` (arm actions and IK)
    - Added images of the IK orientation solutions: `doc/images/ik/`
  - Added: `doc/movement.md` (move and turn actions)
  - Added: `doc/scene.md` (scene setup actions)
- **`self.init_scene()` now loads an empty test scene.** To load a floorplan scene, call `self.init_floorplan_scene()`
  - Removed `TestController` because it no longer does anything that `Magnebot` doesn't
  - **Simplified custom scene setup.** It should be much easier now for users to define their own scenes. Replaced `self._get_scene_init_commands()` with `self._init_scene()` and `self._get_post_processing_commands()`.
  - (Backend): `Magnebot` is now a subclass of `Controller` instead of `FloorplanController`
  - (Backend): `self._scene_bounds` is set via output data returned during `self._init_scene()` rather than via pre-cached data. Deleted the pre-cached scene bounds data.
    - Added: `SceneEnvironment.get_bounds()`
- **Improved collision detection.** The `stop_on_collision ` parameter in the `turn_by()`, `turn_to()`, `move_by()`, and `move_to()`, actions can either be a boolean or a `CollisionDetection` object, which can be used to fine-tune collision detection logic.
- Removed `ActionStatus.ongoing` because it's never used and replaced it with `ActionStatus.failure` (generic failure code)
- Added optional parameters `target_orientation` and `orientation_mode` to `reach_for()` and `grasp()`.
  - Added new enum classes: `TargetOrientation` and `OrientationMode`
  - (Backend): Added new class: `Orientation` (a wrapper class of pairings of `TargetOrientation` and `OrientationMode`)
- **Fixed: IK actions are slow and inaccurate due to not using orientation parameters correctly.** *Greatly* improved the speed and accuracy of `reach_for()` and `grasp()` (hereafter referred to as "IK actions"). By default, the IK actions automatically try to set a target orientation and orientation. To do this, they compare the target position against an array of pre-calculated positions and orientation parameters, and select the nearest. If the IK actions try to bend to a target and fail, they will try adjacent orientation parameters before giving up (this is a bit slow but results in increased accuracy).
  - Fixed: `reach_for()` doesn't always end in the middle of an arm motion if the magnet arrives at the target position.
  - (Backend): Added: `self._get_ik_orientations()`,
  - (Backend): Moved all code shared between the IK actions to `self._do_ik()`.
  - (Backend): Adjusted `self.__get_ik_chain()` to include the torso.
  - (Backend): Added pre-calculated data in `data/magnebot/ik/`
- **Fixed: Torso movement is slow and inaccurate.** Previously in the IK actions, the torso prismatic joint was handled iteratively in increments of 0.1 meters. Per iteration, an arm articulation action checked for a solution. Now, using a fork of the underlying `ikpy` module, prismatic joints are correctly supported, resulting in faster and more accurate IK actions.
- **Fixed: `grasp()` often targets bad or non-existent positions on the object's surface**
  - (Backend): Moved all of the code to get a grasp target to the `grasp()` function
  - (Backend): The `grasp()` action will spherecast to the surface of the object. If there are any hits, it will target the nearest hit. Otherwise, it will get a list of sides of the object's bounds, and remove any sides that are known to be concave (see below). Then the controller will raycast from the side nearest to the magnet to the center of the object. Use the hit if there  was one otherwise use the object's center and hope for the best.
  - (Backend): Added cached data of all convex faces of each model in the TDW full model library: `data/objects/convex.json`
- Fixed: IK actions will sometimes try to reach for impossible positions. Now, they will immediately fail if there isn't a known solution at those coordinates or the position is beyond the reach of the arm.
- Fixed: Magnebot sometimes spins in circles during a turn action
- Adjusted all example, promo, and test controllers to use the improved IK system and scene setup code
- Added: `ObjectStatic.CONVEX_SIDES` A dictionary of model names and which sides of the bounds are known to be convex.
- Added: `ObjectStatic.BOUNDS_SIDES` The order of bounds sides. The values in `CONVEX_SIDES` correspond to indices in this list.
- (Backend): Added: `util/ik_solution.py`
- (Backend): Added: `controllers/tests/benchmark/ik.py` IK action tests and benchmarks.
- (Backend): Added: `controllers/tests/convex.py` Test the `grasp()` action with strangely-shaped objects.
- (Backend): Added: `util/convex.py` For every object in the full model library, determine which sides of the bounds are convex.
- (Backend): Added `overrides` as a required module

## 1.1.2

- Fixed: When checking for the most recent version of `magnebot`, the controller recommends to the currently-installed version rather than the latest version on PyPi
- (Backend): Added `self._y_position_to_torso_position()` Converts a y worldspace coordinate to a torso joint position
- (Backend): Added class variables `_TORSO_Y_MIN`, `_TORSO_Y_MAX`, and `_COLUMN_Y`
- (Backend): `self._end_action()` returns the build output data list of byte arrays

## 1.1.1

- Fixed: `scene_environment.py` imports from the `sticky_mitten_avatar` project instead of `magnebot`

## 1.1.0

- Requires: TDW 1.8.4
  - (Fixed in TDW): `rotate_camera()` and the `pitch`, `yaw`, `roll` parameters of `add_camera()` rotate around a local axis instead of a world axis
- **Fixed: Build frequently crashes to desktop.** This was due to the simulation frequently entering impossible physics states. The following changes have been made to prevent this:
  - By default, `turn_by()` and `turn_to()` will stop on a collision, using the exact same logic as `move_by()` and `move_to()` (previously, turn actions ignored collisions)
  - Added optional parameter `stop_on_collision` to `move_by()`, `move_to()`, `turn_by()` and `turn_to()` Set this to False to ignore collision detection during the action
  - If the previous action was a move or turn and it ended in a collision and the next action in the same direction, it will immediately fail. For example, if `turn_by(-45)` ended in a collision, `turn_by(-70)` will immediately fail (but `move_by(-1)` might succeed).
    - (Backend) This is handled via `self._previous_collision`, which is set to a value of a new `CollisionAction` enum class
    - (Backend) `move_by()` and `turn_by()` have an internal function `__set_collision_action()` to set whether there was a collision and if so, what type (`none`, `move_positive`, etc.)
  - Collision detection is far more accurate, especially for walls
  - Sequential moves and turns would try to reset the torso and column positions, which is only necessary after an arm articulation action. This might've caused physics crashes because the Magnebot is briefly immovable (and regardless was unnecessarily slow). Now, if the current action is a move or turn and the previous action was also a move or a turn, the Magnebot doesn't waste time trying to reset the torso and column
    - (Backend) `_end_action()` now has an optional parameter `previous_action_was_move` which should be always True if called from a move or turn action and always be False for any other action (default is False).
- Fixed: Rare near-infinite loop that can occur in move or turn actions due to the wheels turning very slowly for a very long time
- Fixed: TypeError in `get_visible_objects()` if there are too many colors in the image
- Added field: `colliding_with_wall` If True, the Magnebot is currently colliding with a wall.
- Added example controller: `simple_navigation.py`
- (Backend): Added some functions to make collision detection more customizable: `_is_stoppable_collision()`, `_includes_magnebot_joint_and_object()`, and `_is_high_mass()`
- (Backend): Added `tqdm` as a required module
- Made this changelog more readable

## 1.0.9

- Added optional parameter `check_pypi_version` to the constructor

## 1.0.8

- Fixed: Avatars created via `add_camera()` don't use subpixel antialiasing

## 1.0.7

- Fixed: The `pitch` and `yaw` parameters of `add_camera()` are flipped (`pitch` will yaw, and `yaw` will pitch)

## 1.0.6

- Fixed: Magnebot sometimes spins in circles if the target angle is close to -180 degrees

## 1.0.5

- Fixed: `KeyError` in `ObjectStatic` constructor if the object's category isn't in `categories.json`. As a fallback, the constructor will try to get the category from a record in `models_core.json`. 

## 1.0.4

- Fixed: `init_scene()` doesn't clear the data from the previous simulation

## 1.0.3

- Fixed: If `turn_by()` or `turn_to()` is called and the Magnebot is already aligned with the target, the function returns `failed_to_turn` (should return `success`)

## 1.0.2

- Backend:
  - Added field `room_id` in the `Room` class
  - Renamed field `x_min` to `x_0` in the `Room` class

## 1.0.1

- Fixed: pip module is missing the `data/` folder.

## 1.0.0

- **Created a pip module.**

### Documentation

- Updated the gif in the README.
- Updated installation instructions in the README.
- Added a section in `custom_apis.md` about arm articulation actions.

## 0.5.0

### `Magnebot`

- Set default `skip_frames` value to 10 (was 20).
- Improved the speed of `turn_by()` and `turn_to()` by using different turn constants for different ranges of angles.
- Fixed: Controllers take a very long time to load on certain Linux machines.
- Backend:
  - Renamed `_stop_arms()` to `_stop_joints()` and added optional `joint_ids` parameter.
  - Added: `TurnConstants`. Used  to set constants for turn actions.

### `SceneState`

- Replaced `body_part_transforms` with `joint_positions`. These are numpy arrays of `[x, y, z]` positions instead of `Transform` objects. It only includes joints (not non-moving body parts). As a result, the simulation is slightly faster.

### `MagnebotStatic`

- `body_parts` is now a dictionary where the key is an object ID and the value is a segmentation color (was a list of object IDs)

### `JointStatic`

- Added field: `joint_type` 

### Example controllers

- `custom_api.py`: Improved the `push()`.

### Test controllers

- `turn_constants.py` runs tests for multiple angles.
- Added: `magnebot_color_segmentation.py` Tests color segmentation for Magnebot body parts.
- Fixed: `pick_up.py` and `pick_up_heavy.py` don't work.

### Documentation

- Updated benchmark.

## 0.4.3

### `Magnebot`

- If `self.auto_save_images == True`, the script will print the output directory to the console.
- Fixed: objects are created multiple times in subsequent `init_scene()` calls.
- Fixed: If `init_scene()` is called while the Magnebot is tipping over, the controller thinks that the Magnebot is still tipping over in the new scene.

### Example controllers

- Added: `custom_api.py` Example of a custom scene and a custom action.

### Documentation

- Added a table of example controllers to the README.

## 0.4.2

### `DemoController`

- Removed `DemoController` because it isn't being used and includes obsolete code.

### Promo controllers

- Renamed the directory `demos/` to `promos/` so that it's clearer that these aren't example use-cases.

### Documentation

- Various minor edits throughout the API documentation.

## 0.4.1

### `Magnebot`

- Removed: `segmentation_color_to_object_id` (see `get_visible_objects()`)
- Improved arm articulation speed when moving the torso up and down.
- Backend:
  - Removed code to adjust Magnebot drive parameters because the default drive parameters have been adjusted in the build.
  - Added optional parameter `joint_ids` to `_do_arm_motion()` to specify which joints to listen to. This can speed up certain arm articulations.

### Test controllers

- Removed: `wheel_constants.py`
- Moved `turn_constants.py` to `tests/`

## 0.4.0

### `Magnebot`

- **Major speed improvements.** The simulation now skips frames between `communicate()` calls.
  - Added optional parameters `skip_frames` to the constructor to set the number of frames to skip.
- Fixed: `self.camera_rpy` isn't set in the constructor.
- Fixed: The IK solver uses the wrong height.
- Fixed: Error in the build when scene is reset because it tries to destroy a non-existent robot.
- Fixed: Wheel constants aren't optimized.
- Fixed: `turn_by()` and `turn_to()` can greatly overshoot target rotation if they accidentally turn more than 180 degrees or if the turn angle is less than -180 degrees.
- Fixed: `move_by()` and `move_to()` stop and fail if there's a new collision between a body part of the Magnebot (such as the wheels) the floor.
- Backend:
  - Moved the code that resets the simulation state to from `_cache_static_data()` to `_clear_data()`

### `JointStatic`

- Added field `drives`. Stores drive data.

### Test controllers

- `turn_constants.py` checks for how far the Magnebot drifted while turning.
- Added benchmark controllers: `benchmark/benchmark.py` and `benchmark/benchmark_floorplan.py`

### Documentation

- Moved API documents from `doc/` to `doc/api/`
- Added: `benchmark.md`

## 0.3.4

### `magnebot` module

#### `Magnebot`

- Increased average turn speed by 170.2%. Previous average speed of `turn_by(45)` was 2.437 seconds. New average speed of `turn_by(45)` is 0.895 seconds.
- Increased average turn speed by 124.0%. Previous average speed of `move_by(1)` was 1.469 seconds. New average turn speed of `move_by(1)` is 0.656 seconds.
- Default value of `img_is_png` is `False` (was `True`)
- Fixed: TclError when trying to show a plot image of an IK solution in debug mode on a remote server.

### Test controllers

- Added `turn_by()` benchmark to `benchmark.py`
- Added:  `turn_constants.py` Finds the optimal combination of wheel turn constants.
- Added: `wheel_drives.py` Finds the optimal wheel damping and stiffness values.

## 0.3.3

### `magnebot` module

#### `Magnebot`

- In the `reach_for()` action, if the target object is higher up than the default height of the torso, the torso will slide upwards first, and then the rest of the arm articulation action will occur.

## 0.3.2

### `magnebot` module

#### `Magnebot`

- In the `grasp()` action, if the target object is higher up than the default height of the torso, the torso will slide upwards first, and then the rest of the arm articulation action will occur.
- Fixed: AttributeError if `launch_build=True`
- Fixed: IK actions such as `grasp()` and `reach_for()` are calculated from an incorrect torso height.
- Fixed: If an IK action such as `grasp()` or `reach_for()` targets a position above the torso, the torso often slides below the target.
- Backend: 
  - Added `_trigger_events` to record trigger collisions, which will be used in extensions of this API (the Transport Challenge uses it to check if an object is in a container)
  - Added `_get_bounds_sides()` which is used for getting valid sides for a `grasp()` action.
  - Added optional parameters `orientation_mode` and `target_orientation` to `_start_ik()`.
  - Fixed: the `fixed_torso_prismatic` parameter of `_start_ik()` affects IK calculations. It is now only used when actually generating TDW commands.

### Documentation

- Fixed some typos and added some clarifications.
- Moved the scene intialization section of `custom_apis.md` to the top of the document.

### Demo controllers

- Improved the sequence of actions in `reach_high.py`

### Test controllers

- Improved the usefulness of `grasp.py`

## 0.3.1

### `magnebot` module

#### `Magnebot`

- Added optional parameter `img_is_png` to the constructor
- Added field: `colliding_objects` A list of objects that the Magnebot is colliding with at the end of the most recent action.

#### `MagnebotStatic`

- Added field: `body_parts`  The object IDs of every part of the Magnebot. Includes everything in `self.joints` as well as non-moving parts.

#### `ObjectStatic`

- Fixed: Some kinematic objects are not recorded as being kinematic.

### Example controllers

- Simplified some of the code and added more code comments

### Test controllers

- Added: `benchmark.py`
- Added: `grasp.py`

## 0.3.0

- Added a license
- Updated install instructions in the README
- Made the repo public

## 0.2.4

### `magnebot` module

#### `Magnebot`

- The `launch_build` parameter in the constructor defaults to `False` (was `True`)
- Improved image antialiasing quality
- Fixed: When choosing a random room in which to spawn the Magnebot, the `random_seed` isn't used

#### `SceneState`

- Fixed: Depth maps aren't saved correctly.

#### Backend

- Added function `check_version()` to `util.py`

### Documentation

- Updated install instructions in the README
- Moved troubleshooting section of the README to `doc/troubleshooting.md`

## 0.2.3

### `magnebot` module

#### `Magnebot`

- Added optional parameter `random_seed` to constructor.
- `init_scene()` always returns `ActionStatus.success`.
- `move_by()` stops if the Magnebot collides with a heavy object.
- The Magnebot will reset the rotation of its column before moving or turning.
- Fixed: The position of an object at the end of the IK chain is sometimes incorrect.

### Documentation

- Improved the README. Added an API hierarchy diagram.
- Moved changelog to `doc/`
- Added: `custom_apis.md`

## 0.2.2

### `magnebot` module

#### `Magnebot`

- `move_by()` and `move_to()` stop when there is a collision with the environment but not with an object.
- `move_by()`, `move_to()`, `turn_by()`, and `turn_to()` stop when the Magnebot is starting to tip over, at which point they'll try to correct the tipping.
- Added: `reset_position()`

### Test Controllers

- Removed: `tip.py`
- Added: `pick_up_heavy.py`

## 0.2.1

### `magnebot` module

#### `Magnebot`

- Added: `get_visible_objects()`

### Example controllers

- Added: `pick_up.py`

### Test controllers

- Added: `spawn.py`

## 0.2.0

### `magnebot` module

- Updated floorplan images, spawn positions, occupancy maps, etc. to reflect the changes to the floorplan layouts in the `tdw` module.
- Removed: `DemoController.navigate()`
- Backend:
  - Removed: `constants.RUGS`
  
#### `Magnebot`

- `grasp()` will end as soon as the magnet grasps the object, rather than when the arm stops moving.
- `reach_for()` will end as soon as the magnet is at the target position or when the arms stop moving.
- Backend:
  - No longer listens to `exit` collision events.
  - Added optional parameters `object_id` and `do_prismatic_first` to `_start_ik()`. `object_id` will extend the IK chain to include an object.
  - If an object is part of the IK chain, its center (via `send_bounds`) will be used instead of its position and its rotation will be ignored.
  - Removed `_start_ik_orientation()` because it isn't needed right now and doesn't work very well.
  - Added optional parameter `conditional` to `_do_arm_motion()` to allow a boolean function interrupt the arm motion.
  - Added: `_is_grasping()`
  - Added: `_magnet_is_at_target()`
  - `drop()` doesn't apply a force to dropped objects (no longer needed).
  - `SceneState` reshapes and saves depth images correctly.
  
#### `SceneState`

- Added: `get_point_cloud()`

### Demo controllers

- Removed: `carry.py`

## 0.1.3

### `magnebot` module

- `move_to()` and `move_by()` ignore collisions with very small objects.
- `grasp()` targets the nearest side of the object instead of its center.
- Removed: `reset_arms()`
- Removed: `drop_all()`
- Removed class variable `FORWARD` (see `tdw.tdw_utils.QuaternionUtils.FORWARD`)
- Backend:
  - Renamed `__OBJECT_AUDIO` to `_OBJECT_AUDIO` so that subclasses can access it.
  - Added optional parameter `fixed_torso_prismatic` to `_start_ik()` to force a prismatic value for the torso.
  - Added optional parameter `allow_column` to `_start_ik()` to allow column rotation.
  - Added: `_start_ik_orientation()` Set an IK orientation target.
  - Added: `_get_initial_angles()`. Get the current angles of the arm such that they can be used in an IK solver.
  - Renamed `__get_reset_arm_commands()` to `_get_reset_arm_commands()` so that subclasses can access it.
  - Added optional parameter `object_id` to `__get_ik_chain()` to set an object as an end effector.
  - Added optional parameter `allow_column` to `__get_ik_chain()`.
  - Added: `_append_drop_commands()`.
  - Added: `_wait_until_objects_stop()`. Wait until all objects in the list stop moving.

### Documentation

- Added: `reach_high.gif`

### Example controllers

- Improved `social.image.py`

### Test controllers

- Moved `reach_high.py` from `tests/` to `demos/`

## 0.1.2

- Added: `social.jpg`

### `magnebot` module

- Removed `int_pair.py` (moved to the `tdw` repo).

#### `Magnebot`

- `move_by()` and `move_to()` will stop directional movement if the Magnebot collides with the environment or any scene objects.
- Fixed: In `move_by()` and `move_to()`, the Magnebot goes the wrong way when making more than one attempt if `distance < 0`. 

### Demos

- Added: `social_image.py` Generate the social image.

### Tests

- Added: `tip.py` Tests logic preventing the Magnebot from tipping over.

## 0.1.1

### `magnebot` module

- Added: `DemoController` Generate demo videos of the Magnebot API.

#### `Magnebot`

- In debug mode, output log messages from the build.
- Improved the IK system:
  - Choose a strategy for raising/lowering the torso depending on the height of the target.
  - Move the torso up/down before starting the rest of the arm movement.
  - Fixed: `_do_arm_motion()` only checks whether the angle along the first degree of freedom has changed per joint instead of all degrees of freedom.
  - Fixed: `_absolute_to_relative()` is often inaccurate.
  - Fixed: Torso y values are usually incorrect. Added `data/objects/torso_y.csv` which has cached y values mapped to prismatic drive values.
- Set the default value of `arrived_at` in `move_to()` to 0.3 (was 0.1).
- Set the default value of `absolute` in `reach_for()` to True (was False).
- Replaced parameter `rotation` in `add_camera()` with: `roll`, `pitch`, `yaw`.
- Added optional parameter `camera_id` to `add_camera()` and removed `Magnebot.THIRD_PERSON_CAMERA_ID`.
- If the parameter `follow` in `add_camera()` is True, the camera will follow the avatar instead of being parented to it.
- Fixed: `turn_by()` and `turn_to()` take too long to end (they now check the overall delta in the Magnebot's rotation instead of whether the wheels are spinning.)
- Fixed: `move_by()` and `move_to()` take too long to end (they now check the overall delta in the Magnebot's position instead of whether the wheels are spinning.)
- Fixed: `move_by()` and `move_to()` often overshoot the target.
- Fixed: JSON serialization exception when calling `drop_all()` because `object_id` is of type int32.


### Demos

- Added: `carry.py` The Magnebot picks up two objects and moves them to another room.

### Tests

- Added: `reach_high.py` Pick up an object on a shelf.

### Documentation

- Removed redundant room images.
- Added types and default values to all parameters when applicable.
- Various improvements to API documentation.