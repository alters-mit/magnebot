from enum import Enum


class JointType(Enum):
    """
    Types of joint articulation.
    """

    revolute = 0
    spherical = 1
    prismatic = 2
