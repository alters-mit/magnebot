from enum import Enum


class CollisionAction(Enum):
    """
    Definition for a move or turn action that resulted in a collision.
    """

    none = 1  # There was no collision on the previous action.
    move_positive = 2  # Previous action ended in a collision and was positive movement (e.g. `move_by(1)`).
    move_negative = 4  # Previous action ended in a collision and was negative movement (e.g. `move_by(-1)`).
    turn_positive = 8  # Previous action ended in a collision and was positive turn (e.g. `turn_by(45)`).
    turn_negative = 16  # Previous action ended in a collision and was negative turn (e.g. `turn_by(-45)`).
