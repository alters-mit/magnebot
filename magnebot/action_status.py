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

    If the Magnebot _tried to_ do something and failed, the Magnebot moved for _n_ frames before giving up.

    If the Magnebot _didn't try_ to do something, the action failed without advancing the simulation at all.

    """

    ongoing = 0  # The action is ongoing.
    success = 1  # The action was successful.
    failed_to_move = 2  # The Magnebot tried to move to a target position or object but failed.
    failed_to_turn = 3  # The Magnebot tried to turn but failed to align with the target angle, position, or object.
    cannot_reach = 4  # The Magnebot didn't try to reach for the target position because it can't.
    failed_to_reach = 5  # The Magnebot tried to reach for the target but failed; the magnet isn't close to the target.
    failed_to_grasp = 6  # The Magnebot tried to grasp the object and failed.
    not_holding = 7  # The Magnebot didn't try to drop the object(s) because it isn't holding them.
    clamped_camera_rotation = 8  # The Magnebot rotated its camera but at least one angle of rotation was clamped.
    failed_to_bend = 9  # The Magnebot tried to bend its arm but failed to bend it all the way.
    collision = 10  # The Magnebot tried to move collided with an object with mass > 1, or part of the environment (such as a wall).
    not_in = 100  # (Transport Challenge only) The Magnebot tried and failed to put the object in the container.
    still_in = 101 # (Transport Challenge only) The Magnebot tried and failed to pour all objects out of the container.
