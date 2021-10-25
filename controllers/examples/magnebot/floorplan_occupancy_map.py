from json import loads
import numpy as np
from tdw.controller import Controller
from tdw.add_ons.floorplan import Floorplan
from magnebot import Magnebot
from magnebot.paths import OCCUPANCY_MAPS_DIRECTORY
from magnebot.paths import SPAWN_POSITIONS_PATH

"""
Load a floorplan occupancy map.
"""

scene = "1a"
layout = 0
room = 0
spawn_positions = loads(SPAWN_POSITIONS_PATH.read_text())
# Scene 1a, layout 0, room 2.
magnebot_position = spawn_positions["1"]["0"]["2"]
# 1_0.npy
occupancy_map = np.load(str(OCCUPANCY_MAPS_DIRECTORY.joinpath(f"{scene[0]}_{layout}.npy")))
print(occupancy_map)

c = Controller()
magnebot = Magnebot(position=magnebot_position)
floorplan = Floorplan()
c.add_ons.extend([floorplan, magnebot])
floorplan.init_scene(scene=scene, layout=layout)
c.communicate([])
print(magnebot.dynamic.transform.position)
c.communicate({"$type": "terminate"})
