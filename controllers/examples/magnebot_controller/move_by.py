from magnebot import MagnebotController

"""
Move the Magnebot forward by 2 meters.
"""

c = MagnebotController()  # On a server, change this to: MagnebotController(launch_build=False)

c.init_scene()
c.move_by(2)
print(c.magnebot.dynamic.transform.position)
c.end()
