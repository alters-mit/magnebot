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

If, according to the status code, the Magnebot _tried to_ do something and failed, the Magnebot moved for _n_ frames before giving up.

If, according to the status code, the Magnebot _didn't try_ to do something, the action failed without advancing the simulation at all.

| Value | Description |
| --- | --- |
| `ongoing` | The action is ongoing. |
| `success` | The action was successful. |
| `overshot_move` | The Magnebot tried to move somewhere but overshot the target distance or position. |
| `too_many_attempts` | The Magnebot tried to do an action for too many frames and gave up. |
| `unaligned` | The Magnebot tried to turn but failed to align with the target angle, position, or object. |
| `cannot_reach` | The Magnebot didn't try to reach for the target position because it can't. |
| `failed_to_reach` | The Magnebot tried to reach for the target but failed; the magnet is too far away. |
| `bad_raycast` | The Magnebot didn't try to grasp the object bbecause there is something between the magnet and the object. |
| `failed_to_grasp` | The Magnebot tried to grasp the object and failed. |
| `not_holding` | The Magnebot didn't try to drop the object because it isn't holding the object with that magnet. |

***

