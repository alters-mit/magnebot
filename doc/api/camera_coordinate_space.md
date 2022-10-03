# CameraCoordinateSpace

`from magnebot.camera_coordinate_space import CameraCoordinateSpace`

A coordinate space for the camera. This is used in the `MoveCamera` action.

| Value | Description |
| --- | --- |
| `absolute` | The position is in absolute worldspace coordinates. |
| `relative_to_camera` | The position is relative to the camera's current position. |
| `relative_to_magnebot` | The position is relative to the Magnebot's current position. |