from enum import Enum


class ArmJoint(Enum):
    """
    The name of an arm joint.
    """

    column = 0
    torso = 1
    shoulder_left = 2
    elbow_left = 3
    wrist_left = 4
    shoulder_right = 5
    elbow_right = 6
    wrist_right = 7
