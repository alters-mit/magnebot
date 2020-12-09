from magnebot import TestController

"""
Test `Magnebot.turn_by()`.
"""

if __name__ == "__main__":
    m = TestController()
    m.init_scene()
    m.turn_by(45)
    m.turn_by(-30)
    m.turn_by(112)
    m.turn_by(-121)
    m.end()
