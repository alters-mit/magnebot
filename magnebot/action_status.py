from enum import Enum


class ActionStatus(Enum):
    """
    The status of the Magnebot after doing an action.

    Usage:

    ```python
    TODO
    ```

    """

    ongoing = 0  # The action is ongoing.
    success = 1  # The action was successful.
    overshot_move = 2  # The robot tried to move somewhere but overshot the target distance or position.
    too_many_attempts = 3  # The robot tried to move or turn too many times and gave up.
