# Turn

`from magnebot.turn import Turn`

Abstract base class for a turn action.

***

#### \_\_init\_\_

**`Turn(dynamic, collision_detection)`**

**`Turn(aligned_at=1, dynamic, collision_detection, previous=None)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| aligned_at |  float  | 1 | If the difference between the current angle and the target angle is less than this value, then the action is successful. |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |
| collision_detection |  CollisionDetection |  | [The collision detection rules.](../collision_detection.md) |
| previous |  Action  | None | The previous action, if any. |

