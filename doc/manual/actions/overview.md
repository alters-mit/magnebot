##### Action

# Overview

Actions in the Magnebot API are [`Action`](../../api/actions/action.md) objects assigned to a [`Magnebot`](../../api/magnebot.md) agent. A [`MagnebotController`](../../api/magnebot.md) then evaluates the action until its done.

This `MagnebotController` action...

```python
from magnebot import MagnebotController, Arm

c = MagnebotController()
c.init_scene()
c.reach_for(target={"x": 0.3, "y": 0.5, "z": 0.4},
            arm=Arm.left)
c.end()
```

...is the same as this `Magnebot` action...

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.step_physics import StepPhysics
from magnebot import Magnebot, Arm, ActionStatus
from magnebot.util import get_default_post_processing_commands

c = Controller()
step_physics = StepPhysics(num_frames=10)
magnebot = Magnebot()
c.add_ons.extend([magnebot, step_physics])
commands = [{"$type": "load_scene",
             "scene_name": "ProcGenScene"},
            TDWUtils.create_empty_room(12, 12)]
commands.extend(get_default_post_processing_commands())
c.communicate(commands)
magnebot.reach_for(target={"x": 0.3, "y": 0.5, "z": 0.4},
                   arm=Arm.left)
while magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate([])
c.communicate({"$type": "terminate"})
```

...which is the same as this, which manually assigns a [`ReachFor`](../../api/actions/reach_for.md) action object:

```python
import numpy as np
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.step_physics import StepPhysics
from magnebot import Magnebot, Arm, ActionStatus
from magnebot.actions.reach_for import ReachFor
from magnebot.ik.orientation_mode import OrientationMode
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.util import get_default_post_processing_commands

c = Controller()
step_physics = StepPhysics(num_frames=10)
magnebot = Magnebot()
c.add_ons.extend([magnebot, step_physics])
commands = [{"$type": "load_scene",
             "scene_name": "ProcGenScene"},
            TDWUtils.create_empty_room(12, 12)]
commands.extend(get_default_post_processing_commands())
c.communicate(commands)
magnebot.action = ReachFor(target=np.array([0.3, 0.5, 0.4]),
                           arm=Arm.left,
                           absolute=True,
                           dynamic=magnebot.dynamic,
                           orientation_mode=OrientationMode.auto,
                           target_orientation=TargetOrientation.auto,
                           set_torso=True)
while magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate([])
c.communicate({"$type": "terminate"})
```

## The `Action` class

[`Action`](../../api/actions/action.md) is similar to a TDW add-on in that it will automatically inject commands per `communicate(commands)` call. Unlike TDW add-ons, `Action` has access to various parameters such as the [static](../../api/magnebot_static.md) and [dynamic](../../api/magnebot_dynamic.md) state of the Magnebot.

To define your own action, at minimum you need to define `get_ongoing_commands(resp, static, dynamic)`, which returns a list of commands In practice,  you'll likely want to override additional functions as well:

## `__init__` (the constructor)

*Always* call the superclass constructor. This initializes the fields in `Action`:

```python
from magnebot.actions.action import Action

class ApplyForceToWheels(Action):
    def __init__(self, force: float):
        super().__init__()
        self.force = force
```

### `get_initialization_commands`

You can optionally override `get_initialization_commands(resp, static, dynamic, image_frequency)` to send commands when an action begins. You should *always* call `commands = super().get_initialization_commands(resp, static, dynamic, image_frequency)` because this will add commands that should be at the start of *every* action.

You can cause an action to immediately succeed or fail under certain conditions by setting `self.status` within this function.

In this example, we'll send commands to apply torque forces to each of the Magnebot's wheels. If the force is 0, the action immediately fails. If the Magnebot is currently immovable, we'll make it moveable.

```python
from typing import List
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.image_frequency import ImageFrequency
from magnebot.actions.action import Action
from magnebot.action_status import ActionStatus

class ApplyForceToWheels(Action):
    def __init__(self, force: float):
        super().__init__()
        self.force = force

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        if self.force == 0:
            self.status = ActionStatus.failure
            return []
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        if dynamic.immovable:
            commands.append({"$type": "set_immovable",
                             "immovable": False,
                             "id": static.robot_id})
        for wheel in static.wheels:
            commands.append({"$type": "add_torque_to_revolute",
                             "torque": self.force,
                             "joint_id": static.wheels[wheel],
                             "id": static.robot_id})
        return commands
```

## `get_ongoing_commands`

You must override `get_ongoing_commands(resp, static, dynamic)` or else there will be an error. This function returns commands that should be sent per `communicate(commands)` call. Use this function to evaluate the status of the action.

- At the start of the action, if, after calling `get_initialization_commands()`, `self.status == ActionStatus.ongoing`, then the controller will receive initialization commands + ongoing commands. If `self.status != ActionStatus.ongoing`, the controller will receive an empty list.
- Set `self.status` within `get_ongoing_commands` to end the action.

In this example, the action returns an empty list every frame until the wheels stop turning:

```python
from typing import List
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.image_frequency import ImageFrequency
from magnebot.actions.action import Action
from magnebot.action_status import ActionStatus

class ApplyForceToWheels(Action):
    def __init__(self, force: float):
        super().__init__()
        self.force = force

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        if self.force == 0:
            self.status = ActionStatus.failure
            return []
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        if dynamic.immovable:
            commands.append({"$type": "set_immovable",
                             "immovable": False,
                             "id": static.robot_id})
        for wheel in static.wheels:
            commands.append({"$type": "add_torque_to_revolute",
                             "torque": self.force,
                             "joint_id": static.wheels[wheel],
                             "id": static.robot_id})
        return commands
    
    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        moving = True
        for wheel in static.wheels:
            if not dynamic.joints[static.wheels[wheel]].moving:
                moving = False
                break
        if not moving:
            self.status = ActionStatus.success
        return []
```

### `get_end_commands`

You can optionally override `get_end_commands(resp, static, dynamic, image_frequency)` to send commands when an action begins. You should *always* call `commands = super().get_initialization_commands(resp, static, dynamic, image_frequency)` because this will add commands that should be at the end of *every* action.

If, after `get_ongoing_commands()` is called, `action.status != ActionStatus.ongoing`, the commands returned by `get_end_commands()` are sent to the controller *instead* of  the commands returned by `get_ongoing_commands()`.

In this example, we'll make the Magnebot immovable at the end of the action:

```python
from typing import List
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.image_frequency import ImageFrequency
from magnebot.actions.action import Action
from magnebot.action_status import ActionStatus

class ApplyForceToWheels(Action):
    def __init__(self, force: float):
        super().__init__()
        self.force = force

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        if self.force == 0:
            self.status = ActionStatus.failure
            return []
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        if dynamic.immovable:
            commands.append({"$type": "set_immovable",
                             "immovable": False,
                             "id": static.robot_id})
        for wheel in static.wheels:
            commands.append({"$type": "add_torque_to_revolute",
                             "torque": self.force,
                             "joint_id": static.wheels[wheel],
                             "id": static.robot_id})
        return commands

    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        moving = True
        for wheel in static.wheels:
            if not dynamic.joints[static.wheels[wheel]].moving:
                moving = False
                break
        if not moving:
            self.status = ActionStatus.success
        return []
    
    def get_end_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                         image_frequency: ImageFrequency,) -> List[dict]:
        commands = super().get_end_commands(resp=resp, static=static, dynamic=dynamic, image_frequency=image_frequency)
        commands.append({"$type": "set_immovable",
                         "immovable": True,
                         "id": static.robot_id})
        return commands
```

### `set_status_after_initialization`

You can optionally override `set_status_after_initialization()` in cases where you want the action to end on the first frame *and* you want to use the commands in `get_initialization_commands()`.

This action sets the screen size:

```python
from typing import List
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.image_frequency import ImageFrequency
from magnebot.actions.action import Action
from magnebot.action_status import ActionStatus

class SetScreenSize(Action):
    def __init__(self, width: int, height: int):
        super().__init__()
        self.width: int = width
        self.height: int = height
        
    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        commands.append({"$type": "set_screen_size",
                         "width": self.width,
                         "height": self.height})
        return commands
    
    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        return []
    
    def set_status_after_initialization(self) -> None:
        self.status = ActionStatus.success
```

## Use a custom action

In this example, we'll define the two actions from the above example and use them in a controller. We'll also make a subclass of `Magnebot` to add wrapper functions around the new actions. Then we'll add our `MyMagnebot` to a controller:

```python
from typing import List
from tdw.tdw_utils import TDWUtils
from tdw.controller import Controller
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.image_frequency import ImageFrequency
from magnebot.actions.action import Action
from magnebot.action_status import ActionStatus
from magnebot.magnebot import Magnebot
from magnebot.util import get_default_post_processing_commands


class SetScreenSize(Action):
    def __init__(self, width: int, height: int):
        super().__init__()
        self.width: int = width
        self.height: int = height

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        commands.append({"$type": "set_screen_size",
                         "width": self.width,
                         "height": self.height})
        return commands

    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        return []

    def set_status_after_initialization(self) -> None:
        self.status = ActionStatus.success


class ApplyForceToWheels(Action):
    def __init__(self, force: float):
        super().__init__()
        self.force = force

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        if self.force == 0:
            self.status = ActionStatus.failure
            return []
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        if dynamic.immovable:
            commands.append({"$type": "set_immovable",
                             "immovable": False,
                             "id": static.robot_id})
        for wheel in static.wheels:
            commands.append({"$type": "add_torque_to_revolute",
                             "torque": self.force,
                             "joint_id": static.wheels[wheel],
                             "id": static.robot_id})
        return commands

    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        moving = True
        for wheel in static.wheels:
            if not dynamic.joints[static.wheels[wheel]].moving:
                moving = False
                break
        if not moving:
            self.status = ActionStatus.success
        return []

    def get_end_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                         image_frequency: ImageFrequency,) -> List[dict]:
        commands = super().get_end_commands(resp=resp, static=static, dynamic=dynamic, image_frequency=image_frequency)
        commands.append({"$type": "set_immovable",
                         "immovable": True,
                         "id": static.robot_id})
        return commands


class MyMagnebot(Magnebot):
    def apply_force_to_wheels(self, force: float) -> None:
        self.action = ApplyForceToWheels(force=force)

    def set_screen_size(self, width: int, height: int) -> None:
        self.action = SetScreenSize(width=width, height=height)


if __name__ == "__main__":
    c = Controller()
    magnebot = MyMagnebot()
    c.add_ons.append(magnebot)
    commands = [{"$type": "load_scene",
                 "scene_name": "ProcGenScene"},
                TDWUtils.create_empty_room(12, 12)]
    commands.extend(get_default_post_processing_commands())
    c.communicate(commands)
    # Set the screen size.
    magnebot.set_screen_size(width=256, height=256)
    c.communicate([])
    print(magnebot.action.status)
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
ActionStatus.success
ActionStatus.success
[1.20176852e-03 2.98727304e-02 5.02923775e+00]
```

## Using subclasses of `Action`

In the above example, the Magnebot actually collides with a wall at the end of the action. However, the action ends with `ActionStatus.success`. This is because there isn't any collision detection system. To access that, we'd need to use [`WheelMotion`](../../api/actions/wheel_motion.md), a subclass of `Action`.

The remainder of this section of the Magnebot manual will cover the various subclasses of `Action` and how to use them.

## Hidden functions in `Action`

The base `Action` class includes various hidden functions that are used by its subclasses:

| Function                                                     | Description                                                  |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| `_absolute_to_relative(position: np.array, dynamic: MagnebotDynamic)` | Converts `position` from worldspace coordinates to a coordinate space relative to the Magnebot's position and rotation. Returns a numpy array of the relative position. |
| `_is_tipping(dynamic: MagnebotDynamic)`                      | Returns a tuple of two booleans. First boolean: True if the Magnebot has tipped over. Second boolean: True if the Magnebot is tilted such that it is starting to tip over. |
| `_get_stop_wheels_commands(static: MagnebotStatic, dynamic: MagnebotDynamic)` | Returns a list of commands that will stop the wheels at their present angles. |
| `_y_position_to_torso_position(y_position: float)`           | Static function. Converts a `y` worldspace coordinate value to a torso prismatic joint position. |
| `_get_initial_angles(arm: Arm, static: MagnebotStatic, dynamic: MagnebotDynamic)` | Static function. Returns a numpy array of the current angles of the joints in the given arm in radians. |
| `_get_stop_arm_commands(arm: Arm, static: MagnebotStatic, dynamic: MagnebotDynamic, set_torso: bool)` | Static function. Returns a list of commands to stop the arm's joints at their present angles (including the column and the prismatic torso joint). |
| `_get_reset_arm_commands(arm: Arm, static: MagnebotStatic)`  | Static function. Returns a list of commands to reset the arm to its neutral position. |

***

**Next: [Move and turn actions](movement.md)**

[Return to the README](../../../README.md)

***

Example controllers:

- [custom_action.py](https://github.com/alters-mit/magnebot/blob/main/controllers/examples/actions/custom_action.py) Define custom actions and use them in a controller.
