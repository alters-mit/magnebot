import numpy as np
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus

"""
Move forward by 8 meters. Stop before colliding with a wall.
"""

c = Controller()
magnebot = Magnebot()
c.add_ons.append(magnebot)
c.communicate([{"$type": "load_scene",
                "scene_name": "ProcGenScene"},
               TDWUtils.create_empty_room(12, 12)])
initial_position = np.array(magnebot.dynamic.transform.position[:])
magnebot.move_by(distance=8)
while magnebot.action.status == ActionStatus.ongoing:
    distance = np.linalg.norm(initial_position - magnebot.dynamic.transform.position)
    # Stop before the Magnebot collides with a wall.
    if distance > 4.75:
        magnebot.stop()
    c.communicate([])
# End the action.
c.communicate([])
print(magnebot.action.status)
c.communicate({"$type": "terminate"})
