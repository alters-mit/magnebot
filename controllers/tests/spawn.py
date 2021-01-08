from magnebot.test_controller import TestController, ActionStatus

"""
Test whether the Magnebot is initialized successfully.
"""

if __name__ == "__main__":
    m = TestController()
    status = m.init_scene()
    assert status == ActionStatus.success, status
    status = m.move_by(1)
    assert status == ActionStatus.success, status
    m.end()
