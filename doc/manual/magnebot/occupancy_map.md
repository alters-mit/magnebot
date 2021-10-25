##### Magnebot

# Occupancy maps

The Magnebot API includes pre-cached occupancy maps for each floorplan scene.

[**Images of each occupancy map can be found here.**](https://github.com/alters-mit/magnebot/tree/main/doc/images/occupancy_maps)

```python
from json import loads
import numpy as np
from tdw.controller import Controller
from tdw.add_ons.floorplan import Floorplan
from magnebot import Magnebot
from magnebot.paths import OCCUPANCY_MAPS_DIRECTORY
from magnebot.paths import SPAWN_POSITIONS_PATH

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
```

Output:

```
[[-1 -1 -1 ... -1 -1 -1]
 [-1 -1 -1 ...  0  0  1]
 [-1 -1 -1 ...  0  0  0]
 ...
 [-1  1  1 ... -1 -1 -1]
 [-1  1  1 ... -1 -1 -1]
 [-1  1  1 ... -1 -1 -1]]
 
 [-1.11342115e+01  8.32513688e-05  3.23283815e+00]
```

Occupancy map key:

| Value | Meaning |
| --- | --- |
| -1 | The cell is out of bounds of the scene or not navigable. |
| 0 | The cell is unoccupied; there is a floor at this position but there are no objects. |
| 1 | The cell is occupied by at least one object or a wall. |

The size of each cell in the occupancy map is 0.49x0.49 meters.

***

[Return to the README](../../../README.md)
