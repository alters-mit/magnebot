from enum import Enum


class ActionStatus(Enum):
    """
    The status of the Magnebot after doing an action.

    Usage:

    ```python
    TODO
    ```

    """

    success = 0  # The action was successful.
    overshot_move = 1  # The robot tried to move somewhere but overshot the target distance or position.
    too_many_attempts = 2  # The robot tried to move or turn too many times and gave up.
    unaligned = 3  # The robot tried to turn but failed to align with the target angle, position, or object.
