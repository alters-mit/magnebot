# MoveTo

`from magnebot.move_to import MoveTo`

Turn the Magnebot to a target position or object and then move to it.

This action has two "sub-actions": A [`TurnBy`](turn_by.md) and a [`MoveBy`](move_by.md).

***

## Fields

- `status` [The current status of the action.](../action_status.md) By default, this is `ongoing` (the action isn't done).

- `initialized` If True, the action has initialized. If False, the action will try to send `get_initialization_commands(resp)` on this frame.

***

## Functions

#### \_\_init\_\_

**`MoveTo(target, dynamic, collision_detection)`**

**`MoveTo(target, arrived_at=0.1, aligned_at=1, dynamic, collision_detection, previous=None)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  Union[int, Dict[str, float] |  | The target. If int: An object ID. If dict: A position as an x, y, z dictionary. If numpy array: A position as an [x, y, z] numpy array. |
| arrived_at |  float  | 0.1 | If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful. |
| aligned_at |  float  | 1 | If the difference between the current angle and the target angle is less than this value, then the action is successful. |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |
| collision_detection |  CollisionDetection |  | [The collision detection rules.](../collision_detection.md) |
| previous |  Action  | None | The previous action, if any. |

##### get_initialization_commands

**`self.get_initialization_commands(resp, static, dynamic, image_frequency)`**


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| resp |  List[bytes] |  | The response from the build. |
| static |  MagnebotStatic |  | [The static Magnebot data.](../magnebot_static.md) |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |
| image_frequency |  ImageFrequency |  | [How image data will be captured during the image.](../image_frequency.md) |

_Returns:_  A list of commands to initialize this action.

#### get_ongoing_commands

**`self.get_ongoing_commands()`**

##### set_status_after_initialization

**`self.set_status_after_initialization()`**

In some cases (such as camera actions) that finish on one frame, we want to set the status after sending initialization commands.
To do so, override this method.

##### get_ongoing_commands

**`self.get_ongoing_commands(resp, static, dynamic)`**

Evaluate an action per-frame to determine whether it's done.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| resp |  List[bytes] |  | The response from the build. |
| static |  MagnebotStatic |  | [The static Magnebot data.](../magnebot_static.md) |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |

_Returns:_  Tuple: A list of commands to send to the build to continue the action.

##### get_end_commands

**`self.get_end_commands(resp, static, dynamic, image_frequency)`**


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| resp |  List[bytes] |  | The response from the build. |
| static |  MagnebotStatic |  | [The static Magnebot data.](../magnebot_static.md) |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |
| image_frequency |  ImageFrequency |  | [How image data will be captured during the image.](../image_frequency.md) |

_Returns:_  A list of commands that must be sent to end any action.


