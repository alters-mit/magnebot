# Custom APIs

The Magnebot API is designed to be easily extendable for specialized APIs. Generally, we expect that frontend users won't need to write their own specialized APIs, but if they do, here are some helpful notes on the backend programming.

## Scene initialization

`self._get_init_scene_commands()` returns the list of commands used to initialize the scene. Extend or override this list to create a custom scene.

See `magnebot/demo_controller.py` and `magnebot/test_controller.py` for examples of custom scene initialization.

## Adding objects

To add custom objects to the scene, call `_add_object()` within `_get_scene_init_commands()`. This will create a list of commands for adding an object, and then append that list to `super()._get_scene_init_commands()`. It will return the ID of the object.

```python
def _get_scene_init_commands(self, magnebot_position: Dict[str, float] = None) -> List[dict]:
    # All of theses parameters except `model_name` are optional and have default values.
    # See the docstring in `magnebot_controller.py` for parameter descriptions.
    object_id = self._add_object(model_name="rh10",
                                 position={"x": 0.04, "y": 0, "z": 1.081},
                                 rotation={"x": 0, "y": 0, "z": 0},
                                 library="models_core.json",
                                 scale={"x": 1, "y": 1, "z": 1},
                                 audio=None,
                                 mass=5)
    
    # Initialize the scene. This will add rh10
    commands = super()._get_scene_init_commands(magnebot_position=magnebot_position)
    
    # Append a low-level TDW command that affects rh10
    # Note the order in which this appears: 
    # _add_object() THEN _get_scene_init_commands() THEN any extra low-level commands.
    commands.append({"$type": "apply_force_magnitude_to_object", 
                     "magnitude": 100, 
                     "id": object_id})
    return commands
```

## Commands and Output Data

[Read these documents](https://github.com/threedworld-mit/tdw/tree/master/Documentation/api) to learn more about the low-level TDW API works.

## Custom actions

All Magnebot actions need to:

- Begin with `_start_action()` (disables the image sensor)
- End with `_end_action()` (enables the image sensor and sets `self.state`)
- Return an `ActionStatus` (not strictly necessary but strongly recommended)

```python
from magnebot import Magnebot, ActionStatus

class CustomMagnebot(Magnebot):
    def custom_action(self) -> ActionStatus:
        self._start_action()
        print("Custom action!")
        self._end_action()
        return ActionStatus.success
```

If you want to send commands, it is often useful to append those commands to `self._next_frame_commands`.  The next time `communicate()` is called, all the commands in `self._next_frame_commands` will be sent along with any others you add:

```python
from magnebot import Magnebot, ActionStatus

class CustomMagnebot(Magnebot):
    def custom_action(self) -> ActionStatus:
        self._start_action()
        # This will happen on the next frame.
        self._next_frame_commands.append({"$type": "reset_sensor_container_rotation"})
        
        # self._end_action calls communicate(), so the sensor container will be reset on the same frame as the image capture.
        self._end_action()
        return ActionStatus.success
```

If you want to send the same command every time `communicate()` is called (for example, if you want a camera to track an object), add the command to `self._per_frame_commands`.

### Arm articulation (IK) actions

We are still learning how to best develop arm articulation actions. The following guidelines will be updated continuously.

- You should usually use `_start_ik()` to start an IK action. The `orientation_mode` and `target_orientation` parameters will affect the direction that the arm travels. [Read this for more information](https://notebook.community/Phylliade/ikpy/tutorials/Orientation).
- If `self._debug == True`, then `_stark_ik()` will create a plot of the IK solution. This doesn't work on remote servers.
- `_do_arm_motion()` will loop until the joints stop moving. If your action only involves a few specific joints, the action will generally run faster if you supply a `joint_ids` parameter.

- Very small changes to parameters can result in dramatically different behavior. We're still in the process of learning how to best handle fine motor control with the Magnebot.
- `_append_ik_commands()` converts a list of angles to TDW commands. Unlike `_start_ik()`, it doesn't actually plot an IK solution.

## Other useful functions

These functions aren't in the API documentation because they are intended for only backend coding. For further documentation, including a description of their parameters, please see the docstrings for each of these functions in the [`magnebot_controller.py`](https://github.com/alters-mit/magnebot/blob/main/magnebot/magnebot_controller.py) code.

| Function                     | Description                                                  |
| ---------------------------- | ------------------------------------------------------------ |
| `_start_move_or_turn()`      | Start a move or turn action.                                 |
| `_start_ik()`                | Start an IK (arm articulation) action.                       |
| `_get_initial_angles()`      | Get the angles of the arm in the current state.              |
| `_append_ik_commands()`      | Convert target angles to TDW commands and append them to `_next_frame_commands`. |
| `_get_reset_arm_commands()`  | Get a list of commands to reset an arm.                      |
| `_do_arm_motion()`           | Wait until the arms have stopped moving.                     |
| `_is_grasping()`             | Returns True if the arm is holding the object.               |
| `_cache_static_data()`       | Cache static data after initializing the scene. You probably shouldn't override this, but you'll need to call it if you override `init_scene()`. |
| `_append_drop_commands()`    | Append commands to drop an object to `_next_frame_commands`  |
| `_wait_until_objects_stop()` | Wait until all objects in the list stop moving.              |
| `_absolute_to_relative()`    | Get the converted position relative to the Magnebot's position and rotation. |
| `_magnet_is_at_target()`     | Returns True if the magnet is at the target position.        |
| `_stop_wheels()`             | Stop wheel movement.                                         |
| `_stop_tipping()`            | Handle situations where the Magnebot is tipping by dropping all heavy objects. |
| `_get_bounds_sides()`        | Returns the bounds sides that can be used for `grasp()` targets. You might want to adjust this for certain objects. For example, in the Transport Challenge API, the Magnebot never tries to grasp a container from the top because containers don't have lids on the top. |
| `_wheels_are_turning()`      | Returns True if the wheels are currently turning.            |
| `_stop_joints()`             | Stop all joint movement.                                     |
