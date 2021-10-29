# Troubleshooting and debugging

## What to do if you find a bug or the simulation crashes: 

- Read the rest of this guide, which includes solutions to common errors.
- Try updating:
  - `pip3 install magnebot -U`
  - `pip3 install tdw -U`
  - Download [the latest release of the TDW build](https://github.com/threedworld-mit/tdw/releases/latest/) and unzip the file. 
- Read the rest of this guide.
- [Read the TDW debug guide](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/troubleshooting/overivew.md).
- If you're still getting errors or buggy behavior, create a GitHub Issue on this repo. Describe the problem and include steps to reproduce the bug. If possible, please also include [the player log](https://docs.unity3d.com/Manual/LogFiles.html).

## Common questions

**What do the floorplan scenes, layouts, rooms, and occupancy maps look like?**

- Images of each scene+layout combination are [here](https://github.com/alters-mit/magnebot/tree/main/doc/images/floorplans).
- Images of each room are [here](https://github.com/alters-mit/magnebot/tree/main/doc/images/rooms).
- Occupancy map images are [here](https://github.com/alters-mit/magnebot/tree/main/doc/images/occupancy_maps).

**How do I navigate through a scene?**

This API doesn't include navigation, but it does give you sufficient data to write your own navigation logic.

## Common errors and solutions

**[READ THIS DOCUMENT FIRST.](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/troubleshooting/common_errors.md)** This document covers common errors in TDW (as opposed to common errors that specifically affect the Magnebot API). Note that any errors and solutions involving the `Controller` also affect `MagnebotController`.

***

**`requests.exceptions.ConnectionError: HTTPSConnectionPool(host='pypi.org', port=443)`**

- **Cause:** The controller tried to check the latest version of `magnebot` on PyPi but failed due to lack of an Internet connection.
- **Solution:** Either enable your Internet connection or set `check_pypi_version=False` in the constructor. Note that if you don't have an Internet connection, you won't be able to add any objects to the scene.

```python
from magnebot import MagnebotController

c = MagnebotController(launch_build=False, check_pypi_version=False)
c.init_scene()
```

**The simulation hangs for more than 15 minutes after calling `c.init_floorplan_scene()**

- **Cause:** TDW downloads most of its assets (such as 3D models) at runtime rather than store them locally. The first time you call `init_floorplan_scene()`, it will need a minute or so to download everything. After that, the assets are cached in memory until the build process is terminated, meaning that subsequent `init_floorplan_scene()` calls will be much faster. That said, the total download time shouldn't exceed 3 minutes on a fast Internet connection and 15 minutes on a slow Internet connection. Users in China have reported very slow download times.
- **Solution:** Check the [player log](https://docs.unity3d.com/Manual/LogFiles.html) for any `Network error` messages; if  you see any, there is something wrong with your Internet connection.

**`AttributeError: 'NoneType' object has no attribute '<action>'`**

- **Cause:** You called an action in `MagnebotController` without a first initializing a scene:

  ```python
  from magnebot import MagnebotController
  
  c = MagnebotController()
  c.move_by(2)
  ```

- **Solution:** Initialize a scene before calling any actions:

  ```python
  from magnebot import MagnebotController
  
  c = MagnebotController()
  c.init_scene()
  c.move_by(2)
  ```

**The simulation is slow.**

- [Read  this for possible causes and solutions.](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/troubleshooting/performance_optimizations.md)
- [Compare your speed our performance benchmark](benchmark.md).

**Some actions are unusually slow.**

- **Cause:** Not a bug; some actions are slower than others.
  - Some actions will take longer to complete than others. For example, `move_by(2)` will take more time to complete than `move_by(1)` because the distance is longer.
  - Sometimes, the Magnebot's interaction with objects and the environment will cause the action to take a long time, such as a collision with another object.

**Sometimes a task fails unexpectedly / The Magnebot's movements are inaccurate**

- **Cause:** The simulation is 100% physics-driven. *Every task will sometimes fail.* Possible reasons for failure include:
  - The Magnebot tried to grasp an object but there was an obstacle in the way.
  - The Magnebot tried to move forward but got caught on furniture.
  - The Magnebot tried to put an object in a container but the object bounced out.
- **Solution:** *You* will need to develop solutions to handle cases like this. You can use the [`ActionStatus`](action_status.md) return values to figure out why a task failed and [`SceneState`](scene_state.md) to get the current state of the simulation.

**The Magnebot tipped over**

- **Cause:** is possible, though unlikely, that the Magnebot will tip over due to physics.
- **Solution:** Call `reset_position()`.

**I have a problem not listed here**

Create a GitHub Issue and explain the problem.