from enum import Enum


class OrientationMode(Enum):
    """
    An orientation mode for an IK solution.
    """

    none = None  # Default orientation.
    auto = True  # Let the Magnebot choose an orientation mode.
    x = "X"  # The x axis.
    y = "Y"  # The y axis.
    z = "Z"  # The z axis.
