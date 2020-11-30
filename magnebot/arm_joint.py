from enum import Enum


class ArmJoint(Enum):
    """
    The expected prefix of the name of an arm joint.
    """

    spine = 0
    shoulder = 1
    elbow = 2
    wrist = 3
