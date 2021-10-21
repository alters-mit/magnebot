##### MagnebotController

# Occupancy maps

When the [`MagnebotController`](../../api/magnebot_controller.md) calls `init_floorplan_scene(scene, layout)`, it also loads an occupancy map.

[**Images of each occupancy map can be found here.**](https://github.com/alters-mit/magnebot/tree/main/doc/images/occupancy_maps)

```python
from magnebot import MagnebotController

c = MagnebotController()
c.init_floorplan_scene(scene="1a", layout=0, room=0)
print(c.occupancy_map)
c.end()
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
```

Occupancy map key:

| Value | Meaning |
| --- | --- |
| -1 | The cell is out of bounds of the scene or not navigable. |
| 0 | The cell is unoccupied; there is a floor at this position but there are no objects. |
| 1 | The cell is occupied by at least one object or a wall. |

The size of each cell in the occupancy map is 0.49x0.49 meters.

To concert an occupancy map position to worldspace units, call `c.get_occupancy_position(x, z)`:



```python
from magnebot import MagnebotController

c = MagnebotController()
c.init_floorplan_scene(scene="1a", layout=0, room=0)
x = 30
z = 16
print(c.occupancy_map[x][z])  # 0 (free and navigable position)
print(c.get_occupancy_position(x, z))  # (1.1157886505126946, 2.2528389358520506)
c.end()
```

## Limitations

- Occupancy maps aren't generated if you initialize the scene via `c.init_scene()` or via a custom scene setup.
- Occupancy maps are static; when objects move, the occupancy map won't be updated.

***

[Return to the README](../../../README.md)
