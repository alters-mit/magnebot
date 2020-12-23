# Changelog

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