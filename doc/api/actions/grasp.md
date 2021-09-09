# Grasp

`from magnebot.grasp import Grasp`

Try to grasp a target object.
The action ends when either the Magnebot grasps the object, can't grasp it, or fails arm articulation.

***

#### \_\_init\_\_

**`Grasp(target, arm, orientation_mode, target_orientation, dynamic)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  int |  | The ID of the target object. |
| arm |  Arm |  | [The arm used for this action.](../arm.md) |
| orientation_mode |  OrientationMode |  | [The orientation mode.](../../arm_articulation.md) |
| target_orientation |  TargetOrientation |  | [The target orientation.](../../arm_articulation.md) |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |

#### get_initialization_commands

**`self.get_initialization_commands()`**

#### get_end_commands

**`self.get_end_commands()`**

#### get_ongoing_commands

**`self.get_ongoing_commands()`**

