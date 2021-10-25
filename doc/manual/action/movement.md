##### Action

# Move and turn actions

Move and turn actions are relatively difficult to write because the default actions (`TurnBy`, `TurnTo`, `MoveBy`, and `MoveTo`) have been carefully optimized and use specialized commands to monitor the state of the Magnebot.

In this document, we'll define a relatively simple action: An improved version of `ApplyForceToWheels`, as seen in [the previous document](overview.md). We'll use [`WheelMotion`](../../api/actions/wheel_motion.md) instead of [`Action`](../../api/actions/action.md).

`WheelMotion` adds the following functionality:

| Function                      | Addition                                                     |
| ----------------------------- | ------------------------------------------------------------ |
| `__init__` (constructor)      | Adds [`collision_detection`](../../api/collision_detection.md) parameter<br>Adds [`dynamic`](../../api/magnebot_dynamic.md) parameter<br>Immediately ends the action if the Magnebot is tipping over or has tipped over<br>Immediately ends the action if the previous action was the "same" as this one and resulted in a collision |
| `get_initialization_commands` | **Final; cannot be overridden!**<br>Resets the column and torso before starting to spin the wheels<br>Resets wheel drive values to their defaults<br>Makes the Magnebot moveable if it isn't |
| `get_ongoing_commands`        | **Final; cannot be overridden!**<br/>Evaluates whether the column and torso are still resetting; if they finished resetting on this frame, start the wheel motion |
| `get_end_commands`            | **Final; cannot be overridden!**<br/>Appends commands to stop the wheels at their current angles |

`WheelMotion` adds the following hidden *final* helper functions. These functions can't be overridden:

| Function                                                     | Description                                                  |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| `_is_valid_ongoing(dynamic: MagnebotDynamic)`                | Returns True if the Magnebot isn't tipping over and didn't collide with something that should make it stop. |
| `_is_collision(dynamic: MagnebotDynamic)`                    | Returns True if there was a collision that according to the current detection rules means that the Magnebot needs to stop moving. |
| `_set_brake_wheel_drives(static: MagnebotStatic)`            | Returns a list of commands to lower the force limit of the wheels, causing a "braking" action. |
| `_wheel_motion_complete(static: MagnebotStatic, resp: List[bytes])` | A specialized function that returns True if `MagnebotWheels` is in `resp`. This is useful only for `TurnBy`, `TurnTo`, `MoveBy`, and `MoveTo`. |
| `_wheels_are_turning(static: MagnebotStatic, dynamic: MagnebotDynamic)` | Returns True if any of the wheels are currently spinning.    |

`WheelMotion` includes the following *abstract* functions.  These functions *must* be overridden or there will be an error:

| Function                                                     | Description                                                  |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| `_previous_was_same(previous: Action)`                       | Returns True if the previous action was the "same" as this action for the purposes of collision detection. |
| `_get_ongoing_commands(resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic)` | Returns a list of ongoing commands.                          |
| `_get_start_wheels_commands(static: MagnebotStatic, dynamic: MagnebotDynamic)` | Returns a list of commands to start spinning the wheels.     |

In summary, this is a minimal `WheelMotion` subclass:

```python
from typing import List
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.actions.wheel_motion import WheelMotion
from magnebot.actions.action import Action

class ApplyForceToWheels(WheelMotion):
    def _previous_was_same(self, previous: Action) -> bool:
        return False
    
    def _get_start_wheels_commands(self, static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        return []

    def _get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        return []
```

## Create an `ApplyForceToWheels` action

The above example doesn't actually make the Magnebot do anything. We need to add code to each of those three functions to have a useful action.

First, we'll define our constructor to include a `force` parameter:

```python
from typing import List
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.collision_detection import CollisionDetection
from magnebot.actions.wheel_motion import WheelMotion
from magnebot.actions.action import Action


class ApplyForceToWheels(WheelMotion):
    def __init__(self, force: float, dynamic: MagnebotDynamic, collision_detection: CollisionDetection, previous: Action = None):
        super().__init__(dynamic=dynamic, collision_detection=collision_detection, previous=previous)
        self.force: float = force
```

Then, we'll define `_previous_was_same`. The important thing to check for is whether or not the Magnebot is trying to move forward after a forward movement resulted in a collision, or backward after a backward movement resulted in a collision:

```python
from typing import List
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.collision_detection import CollisionDetection
from magnebot.actions.wheel_motion import WheelMotion
from magnebot.actions.action import Action
from magnebot.actions.move_by import MoveBy


class ApplyForceToWheels(WheelMotion):
    def __init__(self, force: float, dynamic: MagnebotDynamic, collision_detection: CollisionDetection, previous: Action = None):
        super().__init__(dynamic=dynamic, collision_detection=collision_detection, previous=previous)
        self.force: float = force
        
    def _previous_was_same(self, previous: Action) -> bool:
        if isinstance(previous, MoveBy):
            return (previous.distance > 0 and self.force > 0) or (previous.distance < 0 and self.force < 0)
        elif isinstance(previous, ApplyForceToWheels):
            return (previous.force > 0 and self.force > 0) or (previous.force < 0 and self.force < 0)
        else:
            return False
```

Next, we'll define `_get_start_wheels_commands` to start spinning the wheels:

```python
from typing import List
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.collision_detection import CollisionDetection
from magnebot.actions.wheel_motion import WheelMotion
from magnebot.actions.action import Action
from magnebot.actions.move_by import MoveBy


class ApplyForceToWheels(WheelMotion):
    def __init__(self, force: float, dynamic: MagnebotDynamic, collision_detection: CollisionDetection, previous: Action = None):
        super().__init__(dynamic=dynamic, collision_detection=collision_detection, previous=previous)
        self.force: float = force

    def _previous_was_same(self, previous: Action) -> bool:
        if isinstance(previous, MoveBy):
            return (previous.distance > 0 and self.force > 0) or (previous.distance < 0 and self.force < 0)
        elif isinstance(previous, ApplyForceToWheels):
            return (previous.force > 0 and self.force > 0) or (previous.force < 0 and self.force < 0)
        else:
            return False
        
    def _get_start_wheels_commands(self, static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        commands = []
        for wheel in static.wheels:
            commands.append({"$type": "add_torque_to_revolute",
                             "torque": self.force,
                             "joint_id": static.wheels[wheel],
                             "id": static.robot_id})
        return commands
```

Finally, we'll define `_get_ongoing_commands` to check if the action is done:

```python
from typing import List
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.action_status import ActionStatus
from magnebot.collision_detection import CollisionDetection
from magnebot.actions.wheel_motion import WheelMotion
from magnebot.actions.action import Action
from magnebot.actions.move_by import MoveBy


class ApplyForceToWheels(WheelMotion):
    def __init__(self, force: float, dynamic: MagnebotDynamic, collision_detection: CollisionDetection, previous: Action = None):
        super().__init__(dynamic=dynamic, collision_detection=collision_detection, previous=previous)
        self.force: float = force

    def _previous_was_same(self, previous: Action) -> bool:
        if isinstance(previous, MoveBy):
            return (previous.distance > 0 and self.force > 0) or (previous.distance < 0 and self.force < 0)
        elif isinstance(previous, ApplyForceToWheels):
            return (previous.force > 0 and self.force > 0) or (previous.force < 0 and self.force < 0)
        else:
            return False

    def _get_start_wheels_commands(self, static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        commands = []
        for wheel in static.wheels:
            commands.append({"$type": "add_torque_to_revolute",
                             "torque": self.force,
                             "joint_id": static.wheels[wheel],
                             "id": static.robot_id})
        return commands
    
    def _get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        # The action is success if the wheels aren't turning and there isn't a collision.
        if self._is_valid_ongoing(dynamic=dynamic) and not self._wheels_are_turning(static=static, dynamic=dynamic):
            self.status = ActionStatus.success
        return []
```

...And that's it! Now we need to add it to a controller. Note that we pass `self.collision_detection and `self.dynamic` to the constructor:

```python
from typing import List
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.action_status import ActionStatus
from magnebot.collision_detection import CollisionDetection
from magnebot.actions.wheel_motion import WheelMotion
from magnebot.actions.action import Action
from magnebot.actions.move_by import MoveBy
from magnebot.magnebot import Magnebot
from magnebot.magnebot_controller import MagnebotController


class ApplyForceToWheels(WheelMotion):
    def __init__(self, force: float, dynamic: MagnebotDynamic, collision_detection: CollisionDetection, previous: Action = None):
        super().__init__(dynamic=dynamic, collision_detection=collision_detection, previous=previous)
        self.force: float = force

    def _previous_was_same(self, previous: Action) -> bool:
        if isinstance(previous, MoveBy):
            return (previous.distance > 0 and self.force > 0) or (previous.distance < 0 and self.force < 0)
        elif isinstance(previous, ApplyForceToWheels):
            return (previous.force > 0 and self.force > 0) or (previous.force < 0 and self.force < 0)
        else:
            return False

    def _get_start_wheels_commands(self, static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        commands = []
        for wheel in static.wheels:
            commands.append({"$type": "add_torque_to_revolute",
                             "torque": self.force,
                             "joint_id": static.wheels[wheel],
                             "id": static.robot_id})
        return commands

    def _get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        # The action is success if the wheels aren't turning and there isn't a collision.
        if self._is_valid_ongoing(dynamic=dynamic) and not self._wheels_are_turning(static=static, dynamic=dynamic):
            self.status = ActionStatus.success
        return []


class MyMagnebot(Magnebot):
    def apply_force_to_wheels(self, force: float) -> None:
        self.action = ApplyForceToWheels(force=force,
                                         collision_detection=self.collision_detection,
                                         dynamic=self.dynamic)


if __name__ == "__main__":
    c = Controller()
    magnebot = MyMagnebot()
    c.add_ons.append(magnebot)
    commands = [{"$type": "load_scene",
                 "scene_name": "ProcGenScene"},
                TDWUtils.create_empty_room(12, 12)]
    commands.extend(MagnebotController.get_default_post_processing_commands())
    c.communicate(commands)
    magnebot.apply_force_to_wheels(force=70)
    while magnebot.action.status == ActionStatus.ongoing:
        c.communicate([])
    c.communicate([])
    print(magnebot.action.status)
    print(magnebot.dynamic.transform.position)
    c.communicate({"$type": "terminate"})
```

Output:

```
ActionStatus.collision
[2.54202285e-03 1.64114428e-03 4.92368460e+00]
```

***

**Next: [Arm articulation actions](arm_articulation.md)**

[Return to the README](../../../README.md)

***

Example controllers:

- [apply_force_to_wheels.py](https://github.com/alters-mit/magnebot/blob/main/controllers/examples/actions/custom_action.py) Define a custom `WheelMotion` and use it in a controller.