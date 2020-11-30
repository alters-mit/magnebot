# ActionStatus

`from magnebot import ActionStatus`

The status of the Magnebot after doing an action.

Usage:

```python
from magnebot import Magnebot

m = Magnebot()
m.init_scene(scene="2a", layout=1)
status = m.move_by(1)
print(status) # ActionStatus.success
```

| Value | Description |
| --- | --- |
| `success` | The action was successful. |
| `overshot_move` | The Magnebot tried to move somewhere but overshot the target distance or position. |
| `too_many_attempts` | The Magnebot tried to move or turn too many times and gave up. |
| `unaligned` | The Magnebot tried to turn but failed to align with the target angle, position, or object. |
| `too_far_to_reach` | The Magnebot didn't try to reach for the target position because it's too far away. |
| `failed_to_reach` | The Magnebot tried to reach for the target but failed; the magnet is too far away. |

***

