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
| `CAMERA_RPY_CONSTRAINTS` | List[float] | The camera roll, pitch, yaw constraints in degrees. |

***

## Fields

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

**`self.get_initialization_commands()`**

#### set_status_after_initialization

**`self.set_status_after_initialization()`**

