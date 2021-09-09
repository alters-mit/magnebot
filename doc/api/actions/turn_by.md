# TurnBy

`from magnebot.turn_by import TurnBy`

Turn the Magnebot by an angle.

While turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

***

#### \_\_init\_\_

**`TurnBy(angle, dynamic, collision_detection)`**

**`TurnBy(angle, dynamic, collision_detection, aligned_at=1, previous=None)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| angle |  float |  | The target angle in degrees. Positive value = clockwise turn. |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |
| collision_detection |  CollisionDetection |  | [The collision detection rules.](../collision_detection.md) |
| aligned_at |  float  | 1 | If the difference between the current angle and the target angle is less than this value, then the action is successful. |
| previous |  Action  | None | The previous action, if any. |

