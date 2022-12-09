# TurnBy

`from magnebot.actions.turn_by import TurnBy`

Turn the Magnebot by an angle.

While turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

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

**`TurnBy(angle, dynamic, collision_detection, set_torso)`**

**`TurnBy(angle, dynamic, collision_detection, set_torso, aligned_at=1, previous=None)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| angle |  float |  | The target angle in degrees. Positive value = clockwise turn. |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |
| collision_detection |  CollisionDetection |  | [The collision detection rules.](../collision_detection.md) |
| set_torso |  bool |  | If True, slide the torso to its default position when the wheel motion begins. |
| aligned_at |  float  | 1 | If the difference between the current angle and the target angle is less than this value, then the action is successful. |
| previous |  Action  | None | The previous action, if any. |

#### get_initialization_commands

**`self.get_initialization_commands(resp, static, dynamic, image_frequency)`**


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| resp |  List[bytes] |  | The response from the build. |
| static |  MagnebotStatic |  | [The static Magnebot data.](../magnebot_static.md) |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |
| image_frequency |  ImageFrequency |  | [How image data will be captured during the image.](../image_frequency.md) |

_Returns:_  A list of commands to initialize this action.

#### get_ongoing_commands

**`self.get_ongoing_commands(resp, static, dynamic)`**

Evaluate an action per-frame to determine whether it's done.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| resp |  List[bytes] |  | The response from the build. |
| static |  MagnebotStatic |  | [The static Magnebot data.](../magnebot_static.md) |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |

_Returns:_  A list of commands to send to the build if the action is ongoing.

#### get_end_commands

**`self.get_end_commands(resp, static, dynamic, image_frequency)`**


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| resp |  List[bytes] |  | The response from the build. |
| static |  MagnebotStatic |  | [The static Magnebot data.](../magnebot_static.md) |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |
| image_frequency |  ImageFrequency |  | [How image data will be captured during the image.](../image_frequency.md) |

_Returns:_  A list of commands that must be sent to end any action.

#### set_status_after_initialization

**`self.set_status_after_initialization()`**

In some cases (such as camera actions) that finish on one frame, we want to set the status after sending initialization commands.
To do so, override this method.