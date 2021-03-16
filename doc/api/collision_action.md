# CollisionAction

`from magnebot.collision_action import CollisionAction`

Definition for a move or turn action that resulted in a collision.

| Value | Description |
| --- | --- |
| `none` | There was no collision on the previous action. |
| `move_positive` | Previous action ended in a collision and was positive movement (e.g. `move_by(1)`). |
| `move_negative` | Previous action ended in a collision and was negative movement (e.g. `move_by(-1)`). |
| `turn_positive` | Previous action ended in a collision and was positive turn (e.g. `turn_by(45)`). |
| `turn_negative` | Previous action ended in a collision and was negative turn (e.g. `turn_by(-45)`). |