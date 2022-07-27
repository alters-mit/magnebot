# Drop

`from magnebot.actions.drop import Drop`

Drop an object held by a magnet.

## Class Variables

| Variable | Type | Description | Value |
| --- | --- | --- | --- |
| `JOINT_ORDER` | Dict[Arm, List[ArmJoint]] | The order in which joint angles will be set. | `{Arm.left: [ArmJoint.column,` |

***

## Fields

- `status` [The current status of the action.](../action_status.md) By default, this is `ongoing` (the action isn't done).

- `initialized` If True, the action has initialized. If False, the action will try to send `get_initialization_commands(resp)` on this frame.

- `done` If True, this action is done and won't send any more commands.

- `status` [The current status of the action.](../action_status.md) By default, this is `ongoing` (the action isn't done).

- `initialized` If True, the action has initialized. If False, the action will try to send `get_initialization_commands(resp)` on this frame.

- `done` If True, this action is done and won't send any more commands.

***

## Functions

#### \_\_init\_\_

**`Drop(target, arm, wait_for_object, dynamic)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  int |  | The ID of the object currently held by the magnet. |
| arm |  Arm |  | [The arm used for this action.](../arm.md) |
| wait_for_object |  bool |  | If True, the action will continue until the object has finished falling. If False, the action advances the simulation by exactly 1 frame. |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |

#### get_initialization_commands

**`self.get_initialization_commands(resp, static, dynamic, image_frequency)`**


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| resp |  List[bytes] |  | The response from the build. |
| static |  MagnebotStatic |  | [The static Magnebot data.](../magnebot_static.md) |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |
| image_frequency |  ImageFrequency |  | [How image data will be captured during the image.](../image_frequency.md) |

_Returns:_  A list of commands to initialize this action.

#### set_status_after_initialization

**`self.set_status_after_initialization()`**

In some cases (such as camera actions) that finish on one frame, we want to set the status after sending initialization commands.
To do so, override this method.

#### get_ongoing_commands

**`self.get_ongoing_commands(resp, static, dynamic)`**

Evaluate an action per-frame to determine whether it's done.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| resp |  List[bytes] |  | The response from the build. |
| static |  MagnebotStatic |  | [The static Magnebot data.](../magnebot_static.md) |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |

_Returns:_  A list of commands to send to the build to continue the action.

#### get_end_commands

**`self.get_end_commands(resp, static, dynamic, image_frequency)`**


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| resp |  List[bytes] |  | The response from the build. |
| static |  MagnebotStatic |  | [The static Magnebot data.](../magnebot_static.md) |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |
| image_frequency |  ImageFrequency |  | [How image data will be captured during the image.](../image_frequency.md) |

_Returns:_  A list of commands that must be sent to end any action.