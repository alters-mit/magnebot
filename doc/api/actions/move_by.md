# MoveBy

`from magnebot.move_by import MoveBy`

Move the Magnebot forward or backward by a given distance.

***

#### \_\_init\_\_

**`MoveBy(distance, dynamic, collision_detection)`**

**`MoveBy(distance, arrived_at=0.1, dynamic, collision_detection, previous=None)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| distance |  float |  | The target distance. |
| arrived_at |  float  | 0.1 | If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful. |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |
| collision_detection |  CollisionDetection |  | [The collision detection rules.](../collision_detection.md) |
| previous |  Action  | None | The previous action, if any. |

#### get_initialization_commands

**`self.get_initialization_commands(static, dynamic)`**


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| static |  MagnebotStatic |  | [The static Magnebot data.](../magnebot_static.md) |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |

_Returns:_  A list of commands to start spinning the wheels.

