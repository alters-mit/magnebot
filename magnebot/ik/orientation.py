from typing import List
from magnebot.ik.orientation_mode import OrientationMode
from magnebot.ik.target_orientation import TargetOrientation


class Orientation:
    """
    A convenient wrapper for combinations of [`OrientationMode`](orientation_mode.md) and [`TargetOrientation`](target_orientation.md).

    This class is used to store and look up pre-calculated orientation parameters per pre-calculated position.
    """

    def __init__(self, orientation_mode: OrientationMode, target_orientation: TargetOrientation):
        """
        :param orientation_mode: The orientation mode.
        :param target_orientation: The target orientation.
        """

        """:field
        The orientation mode.
        """
        self.orientation_mode: OrientationMode = orientation_mode
        """:field
        The target orientation.
        """
        self.target_orientation: TargetOrientation = target_orientation

    def __str__(self):
        return f"{self.orientation_mode.name}, {self.target_orientation.name}"


# A list of OrientationMode/TargetOrientation combinations. Combinations that are known to be bad aren't in the list.
# These are roughly in order of most-likely to be correct to least-likely.
ORIENTATIONS: List[Orientation] = [Orientation(orientation_mode=OrientationMode.none,
                                               target_orientation=TargetOrientation.none),
                                   Orientation(orientation_mode=OrientationMode.x,
                                               target_orientation=TargetOrientation.up),
                                   Orientation(orientation_mode=OrientationMode.z,
                                               target_orientation=TargetOrientation.up),
                                   Orientation(orientation_mode=OrientationMode.y,
                                               target_orientation=TargetOrientation.up),
                                   Orientation(orientation_mode=OrientationMode.z,
                                               target_orientation=TargetOrientation.forward),
                                   Orientation(orientation_mode=OrientationMode.x,
                                               target_orientation=TargetOrientation.right),
                                   Orientation(orientation_mode=OrientationMode.y,
                                               target_orientation=TargetOrientation.forward),
                                   Orientation(orientation_mode=OrientationMode.z,
                                               target_orientation=TargetOrientation.right),
                                   Orientation(orientation_mode=OrientationMode.x,
                                               target_orientation=TargetOrientation.forward),
                                   Orientation(orientation_mode=OrientationMode.y,
                                               target_orientation=TargetOrientation.right)]
