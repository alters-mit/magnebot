# Changelog

## 1.2.0

**This release introduces significant changes improvements to the arm articulation system. Please read this changelog carefully.** The overall effect is that `grasp()` and `reach_for()` are far faster and more accurate but they behave somewhat differently.

**To upgrade to Magnebot 1.2.0, you must first uninstall and then reinstall the pip module**: 

- If you installed from PyPi: `pip3 uninstall magnebot` then `pip3 install magnebot`
- If you're using the source code in a clone of this repo: `pip3 uninstall magnebot` then `pip3 install -e .`

**For more information regarding the improvements to arm articulation, [read this.](arm_articulation.md)**

***

- **Fixed: IK actions are slow and inaccurate due to not using orientation parameters correctly.** *Greatly* improved the speed and accuracy of `reach_for()` and `grasp()` (hereafter referred to as "IK actions"). By default, the IK actions automatically try to set a target orientation and orientation. To do this, they compare the target position against an array of pre-calculated positions and orientation parameters, and select the nearest. If the IK actions try to bend to a target and fail, they will try adjacent orientation parameters before giving up (this is a bit slow but results in increased accuracy).
  - Fixed: `reach_for()` doesn't always end in the middle of an arm motion if the magnet arrives at the target position.
  - (Backend): Added: `self._get_ik_orientations()`,
  - (Backend): Moved all code shared between the IK actions to `self._do_ik()`.
  - (Backend): Adjusted `self.__get_ik_chain()` to include the torso.
  - (Backend): Added pre-calculated data in `data/magnebot/ik/`
- **Fixed: Torso movement is slow and inaccurate.** Previously in the IK actions, the torso prismatic joint was handled iteratively in increments of 0.1 meters. Per iteration, an arm articulation action checked for a solution. Now, using a fork of the underlying `ikpy` module, prismatic joints are correctly supported, resulting in faster and more accurate IK actions.
  - (Backend): Added:  `self._y_position_to_torso_position()`. Converts from a y worldspace value to a torso joint position value.
  - (Backend): Added constants for various torso joint limits and values.
- Fixed: IK actions will sometimes try to reach for impossible positions. Now, they will immediately fail if there isn't a known solution at those coordinates or the position is beyond the reach of the arm.
- Fixed: `grasp()` often targets bad positions on the object's surface. Before bending the arm, TDW will raycast from the magnet to the object. If the ray hits the object, the Magnebot will aim for the raycast point. Additionally, `grasp()` won't target the bottom of an object if the object is above the magnet (i.e. on a countertop).
  - (Backend): Added: `self._get_grasp_target()` and `self._get_nearest_side()`
- Fixed: When checking the version, the Magnebot suggests upgrading to the currently-installed version.
- Added optional parameters `target_orientation` and `orientation_mode` to `reach_for()` and `grasp()`.
  - Added new enum classes: `TargetOrientation` and `OrientationMode`
  - (Backend): Added new class: `Orientation` (a wrapper class of pairings of `TargetOrientation` and `OrientationMode`)
- Adjusted all example, promo, and test controllers to use the improved IK system.
- Added: `doc/arm_articulation.md`
  - Added images of the IK orientation solutions: `doc/images/ik/`
- (Backend): Added: `util/ik_solution
- (Backend): `self._end_action()` returns the most recent response from the build (`resp`).
- (Backend): Added: `controllers/tests/benchmark/ik.py` IK action tests and benchmarks.

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

- Added field `drives`. Stores [drive data](api/drive.md).

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