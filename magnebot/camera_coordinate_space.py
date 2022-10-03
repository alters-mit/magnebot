from enum import Enum


class CameraCoordinateSpace(Enum):
    """
    A coordinate space for the camera. This is used in the `MoveCamera` action.
    """

    absolute = 1  # The position is in absolute worldspace coordinates.
    relative_to_camera = 2  # The position is relative to the camera's current position.
    relative_to_magnebot = 4  # The position is relative to the Magnebot's current position.
