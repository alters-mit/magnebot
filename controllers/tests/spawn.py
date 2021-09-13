from magnebot import MagnebotController, ActionStatus

"""
Test whether the Magnebot is initialized successfully.
"""

if __name__ == "__main__":
    m = MagnebotController()
    m.init_scene()
    status = m.move_by(1)
    assert status == ActionStatus.success, status
    m.end()
