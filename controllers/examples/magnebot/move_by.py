from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus

"""
Move the Magnebot forward by 2 meters.
"""

c = Controller()  # On a server, change this to Controller(launch_build=False)
magnebot = Magnebot()
c.communicate(TDWUtils.create_empty_room(12, 12))
magnebot.move_by(2)
while magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate([])
print(magnebot.dynamic.transform.position)
c.communicate({"$type": "terminate"})
