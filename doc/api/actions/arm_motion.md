# ArmMotion

`from magnebot.arm_motion import ArmMotion`

Abstract base class for arm motions.

***

#### \_\_init\_\_

**`ArmMotion(arm)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| arm |  Arm |  | [The arm used for this action.](../arm.md) |

#### get_initialization_commands

**`self.get_initialization_commands(static, dynamic)`**


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| static |  MagnebotStatic |  | [The static Magnebot data.](../magnebot_static.md) |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |

_Returns:_  A list of commands to stop the arm's joints.

#### get_end_commands

**`self.get_end_commands(static, dynamic)`**


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| static |  MagnebotStatic |  | [The static Magnebot data.](../magnebot_static.md) |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |

_Returns:_  A list of commands to stop the arm's joints.

