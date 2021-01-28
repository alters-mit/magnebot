import numpy as np


class Transform:
    """
    Positional data for an object, Magnebot, body part, etc.
    """

    def __init__(self, position: np.array, rotation: np.array, forward: np.array):
        """
        :param position: The position vector of the object as a numpy array.
        :param rotation: The rotation quaternion of the object as a numpy array.
        :param forward: The forward directional vector of the object as a numpy array.
        """

        """:field
        The position vector of the object as a numpy array: `[x, y, z]` The position of each object is the bottom-center point of the object. The position of each Magnebot body part is in the exact center of the body part. `y` is the up direction.
        """
        self.position = position
        """:field
        The rotation quaternion of the object as a numpy array: `[x, y, z, w]` See: [`tdw.tdw_utils.QuaternionUtils`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/tdw_utils.md#quaternionutils).
        """
        self.rotation = rotation
        """:field
        The forward directional vector of the object as a numpy array: `[x, y, z]`
        """
        self.forward = forward

