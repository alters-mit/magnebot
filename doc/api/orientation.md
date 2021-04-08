# Orientation

`from magnebot.orientation import Orientation`

A convenient wrapper for combinations of [`OrientationMode`](orientation_mode.md) and [`TargetOrientation`](target_orientation.md).

For an overview of how orientations work in the Magnebot API, [read this](../arm_articulation.md). This class is used to store and look up pre-calculated orientation parameters per pre-calculated position.

***

## Fields

- `orientation_mode` The orientation mode.

- `target_orientation` The target orientation.

***

## Functions

#### \_\_init\_\_

**`Orientation(orientation_mode, target_orientation)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| orientation_mode |  OrientationMode |  | The orientation mode. |
| target_orientation |  TargetOrientation |  | The target orientation. |

