from magnebot import MagnebotController, Arm, ActionStatus

"""
Test arm movement symmetry.
"""


if __name__ == "__main__":
    m = MagnebotController()
    m.init_scene()
    # Bend both arms to mirrored targets.
    for direction, arm in zip([1, -1], [Arm.left, Arm.right]):
        status = m.reach_for(target={"x": 0.2 * direction, "y": 0.5, "z": 0.5}, arm=arm, absolute=False)
        assert status == ActionStatus.success, f"{arm}, {status}"
        m.reset_arm(arm=arm)
    m.end()
