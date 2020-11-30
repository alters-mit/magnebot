from enum import Enum


class Wheel(Enum):
    """
    The expected name of each wheel on the Magnebot.
    """

    wheel_left_forward = 0
    wheel_left_back = 1
    wheel_right_forward = 2
    wheel_right_back = 3
