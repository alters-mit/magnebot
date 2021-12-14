from enum import Enum


class TargetOrientation(Enum):
    """
    A target orientation vector for an IK solution.
    """

    none = None  # Default orientation.
    auto = True  # Let the Magnebot choose a target orientation.
    up = [0, 1, 0]  # Corresponds to `[0, 1, 0]`.
    forward = [0, 0, 1]  # Corresponds to `[0, 0, 1]`.
    right = [1, 0, 0]  # Corresponds to `[1, 0, 0]`.
