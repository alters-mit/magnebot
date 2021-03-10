from enum import Enum


class CollisionAction(Enum):
    """
    Definition for a move or turn action that resulted in a collision.
    """

    none = 1
    move_positive = 2
    move_negative = 4
    turn_positive = 8
    turn_negative = 16
