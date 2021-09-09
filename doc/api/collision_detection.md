# CollisionDetection

`from magnebot.collision_detection import CollisionDetection`

Parameters for how a Magnebot handles collision detection.

***

## Fields

- `walls` If True, the Magnebot will stop when it collides with a wall.

- `floor` If True, the Magnebot will stop when it collides with the floor.

- `objects` If True, the Magnebot will stop when it collides collides with an object with a mass greater than the `mass` value unless the object is in the `exclude_objects`.

- `include_objects` The Magnebot will stop if it collides with any object in this list, *regardless* of mass, whether or not `objects == True`, or the mass of the object. Can be None.

- `exclude_objects` The Magnebot will ignore a collision with any object in this list, *regardless* of whether or not `objects == True` or the mass of the object. Can be None.

- `previous_was_same` If True, the Magnebot will stop if the previous action resulted in a collision and was the same sort of action as the current one.

***

## Functions

#### \_\_init\_\_

**`CollisionDetection()`**

**`CollisionDetection(walls=True, floor=False, objects=True, include_objects=None, exclude_objects=None, previous_was_same=True)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| walls |  bool  | True | If True, the Magnebot will stop when it collides with a wall. |
| floor |  bool  | False | If True, the Magnebot will stop when it collides with the floor. |
| objects |  bool  | True | If True, the Magnebot will stop when it collides collides with an object with a mass greater than the `mass` value unless the object is in the `exclude_objects`. |
| include_objects |  List[int] | None | The Magnebot will stop if it collides with any object in this list, whether or not `objects == True`, or the mass of the object. Can be None. |
| exclude_objects |  List[int] | None | The Magnebot will ignore a collision with any object in this list, *regardless* of whether or not `objects == True`. Can be None. |
| previous_was_same |  bool  | True | If True, the Magnebot will stop if the previous action resulted in a collision and was the same sort of action as the current one. |

