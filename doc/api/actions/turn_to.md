# TurnTo

`from magnebot.turn_to import TurnTo`

Turn to a target position or object.

***

## Fields

- `target_arr` The target position as a numpy array.

- `target_dict` The target position as a dictionary.

***

## Functions

#### \_\_init\_\_

**`TurnTo(target, dynamic, collision_detection)`**

**`TurnTo(target, aligned_at=1, dynamic, collision_detection, previous=None)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  Union[int, Dict[str, float] |  | The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array. |
| aligned_at |  float  | 1 | If the difference between the current angle and the target angle is less than this value, then the action is successful. |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |
| collision_detection |  CollisionDetection |  | [The collision detection rules.](../collision_detection.md) |
| previous |  Action  | None | The previous action, if any. |

#### get_initialization_commands

**`self.get_initialization_commands()`**

