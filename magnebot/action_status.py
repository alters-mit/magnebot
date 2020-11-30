from enum import Enum


class ActionStatus(Enum):
    """
    The status of the Magnebot after doing an action.

    Usage:

    ```python
    from magnebot import Magnebot

    m = Magnebot()
    m.init_scene(scene="2a", layout=1)
    status = m.move_by(1)
    print(status) # ActionStatus.success
    ```

    """

    success = 0  # The action was successful.
    overshot_move = 1  # The Magnebot tried to move somewhere but overshot the target distance or position.
    too_many_attempts = 2  # The Magnebot tried to move or turn too many times and gave up.
    unaligned = 3  # The Magnebot tried to turn but failed to align with the target angle, position, or object.
    too_far_to_reach = 4  # The Magnebot didn't try to reach for the target position because it's too far away.
    failed_to_reach = 5  # The Magnebot tried to reach for the target but failed; the magnet is too far away.
