from magnebot import TestController, ActionStatus

"""
Test Magnebot moving and turning.
"""


def assert_status(status: ActionStatus) -> None:
    assert status == ActionStatus.success, status


if __name__ == "__main__":
    c = TestController()
    c.init_scene()
    assert_status(c.turn_by(45))
    assert_status(c.turn_by(-30))
    assert_status(c.move_by(0.8))
    assert_status(c.move_to(target={"x": 1.2, "y": 0, "z": -1}))
    assert_status(c.move_by(-3))
    assert_status(c.turn_to(target={"x": 3.2, "y": 0, "z": 0}))
    c.end()
