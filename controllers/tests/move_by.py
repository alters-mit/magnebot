from magnebot import TestController, ActionStatus

"""
Test `Magnebot.move_by()`.
"""


def assert_status(status: ActionStatus) -> None:
    assert status == ActionStatus.success, status


if __name__ == "__main__":
    c = TestController()
    c.init_scene()
    assert_status(c.move_by(0.8))
    assert_status(c.move_by(2))
    assert_status(c.move_by(-3))
    assert_status(c.move_by(0))
    c.end()
