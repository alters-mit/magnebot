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

If the Magnebot _tried to_ do something and failed, the Magnebot moved for _n_ frames before giving up.

If the Magnebot _didn't try_ to do something, the action failed without advancing the simulation at all.

| Value | Description |
| --- | --- |
| `ongoing` | The action is ongoing. |
| `success` | The action was successful. |
| `failed_to_move` | The Magnebot tried to move to a target position or object but failed. |
| `failed_to_turn` | The Magnebot tried to turn but failed to align with the target angle, position, or object. |
| `cannot_reach` | The Magnebot didn't try to reach for the target position because it can't. |
| `failed_to_reach` | The Magnebot tried to reach for the target but failed; the magnet isn't close to the target. |
| `failed_to_grasp` | The Magnebot tried to grasp the object and failed. |
| `not_holding` | The Magnebot didn't try to drop the object(s) because it isn't holding them. |
| `clamped_camera_rotation` | The Magnebot rotated its camera but at least one angle of rotation was clamped. |
| `failed_to_bend` | The Magnebot tried to bend its arm but failed to bend it all the way. |
| `collision` | The Magnebot tried to move or turn but failed because it collided with the environment (such as a wall). |
| `tipping` | The Magnebot tried to move or turn but failed because it started to tip over. |
| `not_in` | (Transport Challenge only) The Magnebot tried and failed to put the object in the container. |
| `still_in` | (Transport Challenge only) The Magnebot tried and failed to pour all objects out of the container. |