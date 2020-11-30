# Transform

`from magnebot.transform import Transform`

Positional data for an object, Magnebot, body part, etc.

***

## Fields

- `position` The position of the object as a numpy array: `[x, y, z]` The position of each object is the bottom-center point of the object. The position of each Magnebot body part is in the exact center of the body part. `y` is the up direction.

- `rotation` The rotation (quaternion) of the object as a numpy array: `[x, y, z, w]` See: [`tdw.tdw_utils.QuaternionUtils`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/tdw_utils.md#quaternionutils).

- `forward` The forward directional vector of the object as a numpy array: `[x, y, z]`

***

## Functions

#### \_\_init\_\_

**`def __init__(self, position: np.array, rotation: np.array, forward: np.array)`**

| Parameter | Description |
| --- | --- |
| position | The position of the object as a numpy array. |
| rotation | The rotation (quaternion) of the object as a numpy array. |
| forward | The forward directional vector of the object as a numpy array. |

