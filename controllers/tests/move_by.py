from magnebot import Magnebot, ActionStatus

"""
Test `Magnebot.move_by()`.
"""


def assert_status(status: ActionStatus) -> None:
    assert status == ActionStatus.success, status


if __name__ == "__main__":
    c = Magnebot(launch_build=False, debug=True)
    c.init_test_scene()
    assert_status(c.move_by(0.8))
    assert_status(c.move_by(2))
    assert_status(c.move_by(-5))
    assert_status(c.move_by(0))
    c.end()
