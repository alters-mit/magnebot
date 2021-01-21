# Changelog

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