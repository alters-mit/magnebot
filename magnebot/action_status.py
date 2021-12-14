from enum import Enum


class ActionStatus(Enum):
    """
    The status of the Magnebot after doing an action.

    Usage:

    With a [`Magnebot` agent](magnebot.md):

    ```python
    from tdw.controller import Controller
    from tdw.tdw_utils import TDWUtils
    from magnebot import Magnebot, ActionStatus

    m = Magnebot(robot_id=0, position={"x": 0.5, "y": 0, "z": -1})
    c = Controller()
    c.add_ons.append(m)
    c.communicate(TDWUtils.create_empty_room(12, 12))
    m.move_by(1)
    print(m.action.status) # ActionStatus.ongoing
    while m.action.status == ActionStatus.ongoing:
        c.communicate([])
    print(m.action.status) # ActionStatus.success
    c.communicate({"$type": "terminate"})
    ```

    With a single-agent [`MagnebotController`](magnebot_controller.md):

    ```python
    from magnebot import MagnebotController

    m = MagnebotController()
    m.init_scene()
    status = m.move_by(1)
    print(status) # ActionStatus.success
    m.end()
    ```

    If the status description states that the Magnebot _tried to_ do something and failed, it means that the Magnebot moved for _n_ frames before giving up.

    If the status description states that the Magnebot _didn't try_ to do something, it means that the action failed without advancing the simulation at all.

    """

    ongoing = 0  # The action is ongoing.
    failure = 1  # Generic failure code (useful for custom APIs).
    success = 2  # The action was successful.
    failed_to_move = 3  # Tried to move to a target position or object but failed.
    failed_to_turn = 4  # Tried to turn but failed to align with the target angle, position, or object.
    cannot_reach = 5  # Didn't try to reach for the target position because it can't.
    failed_to_reach = 6  # Tried to reach for the target but failed; the magnet isn't close to the target.
    failed_to_grasp = 7  # Tried to grasp the object and failed.
    not_holding = 8  # Didn't try to drop the object(s) because it isn't holding them.
    clamped_camera_rotation = 9  # Rotated the camera but at least one angle of rotation was clamped.
    failed_to_bend = 10  # Tried to bend its arm but failed to bend it all the way.
    collision = 11  # Tried to move or turn but failed because it collided with the environment (such as a wall) or a large object (mass > 30).
    tipping = 12  # Tried to move or turn but failed because it started to tip over.
    held_by_other = 13  # Didn't try to grasp a target object because another Magnebot is already holding it.
    cannot_reset_position = 14  # Didn't try to reset the position because the Magnebot hasn't tipped over.
