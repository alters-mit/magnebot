# JointStatic

`from magnebot.joint_static import JointStatic`

Static data for a joint the Magnebot.

***

## Fields

- `id` The unique ID of the body part object.

- `mass` The mass of the body part.

- `segmentation_color` The segmentation color of the object as a numpy array: `[r, g, b]`

- `name` The name of the body part object.

***

## Functions

#### \_\_init\_\_

**`def __init__(self, sr: StaticRobot, index: int)`**

| Parameter | Description |
| --- | --- |
| sr | The static robot output data. |
| index | The index of this body part in `sr`. |

