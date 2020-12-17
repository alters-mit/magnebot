# Changelog

## 0.1.2

### `magnebot` module

- Removed `int_pair.py` (moved to the `tdw` repo).

#### `Magnebot`

- `move_by()` and `move_to()` will stop directional movement if the Magnebot collides with the environment or any scene objects.
- Fixed: In `move_by()` and `move_to()`, the Magnebot goes the wrong way when making more than one attempt if `distance < 0`. 

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