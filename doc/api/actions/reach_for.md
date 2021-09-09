# ReachFor

`from magnebot.reach_for import ReachFor`

Reach for a target position. The action ends when the magnet is at or near the target position, or if it fails to reach the target.
The Magnebot may try to reach for the target multiple times, trying different IK orientations each time, or no times, if it knows the action will fail.

***

#### \_\_init\_\_

**`ReachFor(target, absolute, arm, orientation_mode, target_orientation, dynamic)`**

**`ReachFor(target, absolute, arrived_at=0.125, arm, orientation_mode, target_orientation, dynamic)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  np.array |  | The target position. |
| absolute |  bool |  | If True, `target` is in absolute world coordinates. If `False`, `target` is relative to the position and rotation of the Magnebot. |
| arrived_at |  float  | 0.125 | If the magnet is this distance or less from `target`, then the action is successful. |
| arm |  Arm |  | [The arm used for this action.](../arm.md) |
| orientation_mode |  OrientationMode |  | [The orientation mode.](../../arm_articulation.md) |
| target_orientation |  TargetOrientation |  | [The target orientation.](../../arm_articulation.md) |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |

#### get_initialization_commands

**`self.get_initialization_commands()`**

#### get_ongoing_commands

**`self.get_ongoing_commands()`**

