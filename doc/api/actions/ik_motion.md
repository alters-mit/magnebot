# IKMotion

`from magnebot.ik_motion import IKMotion`

Abstract base class for arm motions that utilize IK.

***

#### \_\_init\_\_

**`IKMotion(arm, orientation_mode, target_orientation, dynamic)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| arm |  Arm |  | [The arm used for this action.](../arm.md) |
| orientation_mode |  OrientationMode |  | [The orientation mode.](../../arm_articulation.md) |
| target_orientation |  TargetOrientation |  | [The target orientation.](../../arm_articulation.md) |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |

#### get_end_commands

**`self.get_end_commands(static, dynamic, arrived_at)`**

Set the lists of commands for arm articulation.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| static |  MagnebotStatic |  | [The static Magnebot data.](../magnebot_static.md) |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |
| arrived_at |  |  | If the magnet is this distance from the target, it has arrived. |

