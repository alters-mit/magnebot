# JointStatic

`from magnebot.joint_static import JointStatic`

Static data for a joint of the Magnebot.

***

## Fields

- `id` The unique ID of the body part object.

- `mass` The mass of the body part.

- `segmentation_color` The segmentation color of the object as a numpy array: `[r, g, b]`

- `name` The name of the body part object.

- `drives` Static data for the joint's drives. Key = axis. Value = [drive data](drive.md).

***

## Functions

#### \_\_init\_\_

**`JointStatic(sr, index)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| sr |  StaticRobot |  | The static robot output data. |
| index |  int |  | The index of this body part in `sr`. |

