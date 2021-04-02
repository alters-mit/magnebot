# CollisionDetection

`from magnebot.collision_detection import CollisionDetection`

Parameters for how a Magnebot handles collision detection.

***

## Fields

- `walls` If True, the Magnebot will stop when it collides with a wall.

- `floor` If True, the Magnebot will stop when it collides with the floor.

- `objects` If True, the Magnebot will stop when it collides collides with an object with a mass greater than the `mass` value that is either listed in `include_objects` or not listed in `exclude_objects`.

- `mass` If `objects == True`, the Magnebot will only stop if it collides with an object with mass greater than or equal to this value.

- `include_objects` If `objects == True`, the Magnebot will stop if it collides with any object in this list, regardless of mass. Can be None.

- `exclude_objects` If `objects == True`, the Magnebot will ignore a collision with any object in this list, regardless of mass. Can be None.

- `previous_was_same` If True, the Magnebot will stop if the previous action resulted in a collision and was the [same sort of action as the current one](collision_action.md).

***

## Functions

#### \_\_init\_\_

**`CollisionDetection()`**

**`CollisionDetection(walls=True, floor=False, objects=True, mass=8, include_objects=None, exclude_objects=None, previous_was_same=True)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| walls |  bool  | True | If True, the Magnebot will stop when it collides with a wall. |
| floor |  bool  | False | If True, the Magnebot will stop when it collides with the floor. |
| objects |  bool  | True | If True, the Magnebot will stop when it collides with an object with a mass greater than the `mass` value that is either listed in `include_objects` or not listed in `exclude_objects`. |
| mass |  float  | 8 | If `objects == True`, the Magnebot will only stop if it collides with an object with mass greater than or equal to this value. |
| include_objects |  List[int] | None | If `objects == True`, the Magnebot will stop if it collides with any object in this list, regardless of mass. Can be None. |
| exclude_objects |  List[int] | None | If `objects == True`, the Magnebot will ignore a collision with any object in this list, regardless of mass. Can be None. |
| previous_was_same |  bool  | True | If True, the Magnebot will stop if the previous action resulted in a collision and was the [same sort of action as the current one](collision_action.md). |

