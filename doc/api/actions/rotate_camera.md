# RotateCamera

`from magnebot.rotate_camera import RotateCamera`

Rotate the Magnebot's camera by the (roll, pitch, yaw) axes.

Each axis of rotation is constrained (see `Magnebot.CAMERA_RPY_CONSTRAINTS`).

| Axis | Minimum | Maximum |
| --- | --- | --- |
| roll | -55 | 55 |
| pitch | -70 | 70 |
| yaw | -85 | 85 |

***

## Class Variables

| Variable | Type | Description |
| --- | --- | --- |
| `JOINT_ORDER` | Dict[Arm, List[ArmJoint]] | The order in which joint angles will be set. |
| `CAMERA_RPY_CONSTRAINTS` | List[float] | The camera roll, pitch, yaw constraints in degrees. |

***

## Fields

- `status` [The current status of the action.](../action_status.md) By default, this is `ongoing` (the action isn't done).

- `initialized` If True, the action has initialized. If False, the action will try to send `get_initialization_commands(resp)` on this frame.

- `done` If True, this action is done and won't send any more commands.

- `deltas` Rotate the camera by these delta (roll, pitch, yaw). This will be clamped to the maximum RPY values.

- `camera_rpy` The adjust camera roll, pitch, yaw angles.

***

## Functions

#### \_\_init\_\_

**`RotateCamera(roll, pitch, yaw, camera_rpy)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| roll |  float |  | The roll angle in degrees. |
| pitch |  float |  | The pitch angle in degrees. |
| yaw |  float |  | The yaw angle in degrees. |
| camera_rpy |  np.array |  | The current camera angles. |

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



