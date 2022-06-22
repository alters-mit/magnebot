##### Magnebot

# Overview

The [`Magnebot`](../../api/magnebot.md) is an agent add-on for TDW. `Magnebot` actions can be interrupted and won't automatically advance the simulation (because `Magnebot` is not a controller).  `self.move_by(2)` will *start* the Magnebot's motion; you must manually check when the action ends.

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus

c = Controller()  # On a server, change this to Controller(launch_build=False)
magnebot = Magnebot()
c.add_ons.append(magnebot)
c.communicate(TDWUtils.create_empty_room(12, 12))
magnebot.move_by(2)
while magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate([])
print(magnebot.dynamic.transform.position)
c.communicate({"$type": "terminate"})
```

## How `Magnebot` is used in `Controller`

`Magnebot` is a lower-level API than `MagnebotController`. The most important difference is that it doesn't include any built-in scene setup logic; [read this for more information](scene_setup.md).

In order to use `Magnebot`, you need to understand more of TDW than if you use `MagenbotController`. [TDW is extensively documented.](https://github.com/threedworld-mit/tdw) We recommend reading these sections in particular:

- [Core concepts](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/core_concepts/controller.md) explains the fundamentals of TDW.
- [Scene Setup](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/scene_setup/overview.md) explains how to populate a scene with objects.
- [Visual perception](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/visual_perception/overview.md) explains how to access data image passes such as the depth map.
- [Physics (PhysX)](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/physx/physx.md) explains how the physics engine works in TDW.
- [Robots](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/robots/overview.md) explains TDW robotics simulation. The `Magnebot` agent uses TDW robotics commands and is itself a subclass of [`Robot`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/add_ons/robot.md).

 ## How `Magnebot` is used in `MagnebotController`

[`MagnebotController`](../magnebot_controller/overview.md) automatically adds a `Magnebot` agent to the scene. It has a function `self._do_action()` which calls `self.communicate()` until the `Magenbot`'s action is done.

For example, this is the code for `Magenbot.move_by`:

```
    def move_by(self, distance: float, arrived_at: float = 0.1) -> None:
        self.action = MoveBy(distance=distance, arrived_at=arrived_at, collision_detection=self.collision_detection,
                             previous=self._previous_action, dynamic=self.dynamic)
```

...and this is the code for `MagnebotController.move_by`:

```
    def move_by(self, distance: float, arrived_at: float = 0.1) -> ActionStatus:
        self.magnebot.move_by(distance=distance, arrived_at=arrived_at)
        return self._do_action()
```

## How `Magnebot` is used in multi-agent simulations

Creating multi-agent simulations with `Magnebot` is as simple as adding multiple `Magnebot` add-ons to a control. This is described in more depth in [this document](multi_agent.md).

***

**Next: [Scene setup](scene_setup.md)**

[Return to the README](../../../README.md)

***

Example controllers:

- [move_by.py](https://github.com/alters-mit/magnebot/blob/main/controllers/examples/magnebot/move_by.py) Move the Magnebot forward by 2 meters.

