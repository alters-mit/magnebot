# MoveTo

`from magnebot.move_to import MoveTo`

Turn the Magnebot to a target position or object and then move to it.

This action has two "sub-actions": A [`TurnBy`](turn_by.md) and a [`MoveBy`](move_by.md).

***

#### \_\_init\_\_

**`MoveTo(target, dynamic, collision_detection)`**

**`MoveTo(target, arrived_at=0.1, aligned_at=1, dynamic, collision_detection, previous=None)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  Union[int, Dict[str, float] |  | The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array. |
| arrived_at |  float  | 0.1 | If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful. |
| aligned_at |  float  | 1 | If the difference between the current angle and the target angle is less than this value, then the action is successful. |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |
| collision_detection |  CollisionDetection |  | [The collision detection rules.](../collision_detection.md) |
| previous |  Action  | None | The previous action, if any. |

#### get_initialization_commands

**`self.get_initialization_commands()`**

#### get_ongoing_commands

**`self.get_ongoing_commands()`**

