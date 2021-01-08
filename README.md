# Magnebot

Magnebot is a high-level robotics-like API for [TDW](https://github.com/threedworld-mit/tdw). The Magnebot can move around the scene and manipulate objects by picking them up with "magnets". The scene and all of the Magnebot's actions are driven by a physics simulation.

![](doc/images/reach_high.gif)

[Read the Magnebot API documentation here.](https://github.com/alters-mit/magnebot/blob/main/doc/magnebot_controller.md) The Magnebot can be loaded into a [wide variety of scenes populated by interactable objects](https://github.com/alters-mit/magnebot/tree/main/doc/images/floorplans). All of the Magnebot's possible movements are divided into "actions", each corresponding to an API call, such as `turn_by()` and `move_to()`. Arm articulation is driven by an inverse kinematics (IK) system: specify a target position or object in the action `reach_for(target, arm)` and the `arm` will calculate a solution to reach the `target`. At the end of every action, the Magnebot controller script will return  [scene state data](https://github.com/alters-mit/magnebot/blob/main/doc/scene_state.md), which includes an image, a depth map, a segmentation color map, and physics metadata for each body part of the robot and each object in the scene.

# Requirements

See [Getting Started With TDW](https://github.com/threedworld-mit/tdw/blob/master/Documentation/getting_started.md).

# Installation

1. Clone this repo.
2. `cd path/to/magnebot` (replace `path/to` with the actual path).
3. Install the local `magnebot` pip module:

| Windows                    | OS X and Linux      |
| -------------------------- | ------------------- |
| `pip3 install -e . --user` | `pip3 install -e .` |

4. If  you want to run TDW on a headless server, [get the TDW Docker image](https://github.com/threedworld-mit/tdw/blob/master/Documentation/Docker/docker.md).

# Usage

1. Run this controller:

```python
from magnebot import Magnebot, Arm

# If you're running TDW in a docker container, add to the constructor: launch_build=False
m = Magnebot()
# Initialize the scene, populate it with objects, and add the Magnebot.
m.init_scene(scene="1a", layout=0, room=1)
# Reach for a target position.
status = m.reach_for(arm=Arm.left, target={"x": 0.1, "y": 0.6, "z": 0.4})
print(status) # ActionStatus.success
# End the simulation.
m.end()
```

2. If `launch_build=False`, [launch the TDW build now](https://github.com/threedworld-mit/tdw/blob/master/Documentation/getting_started.md).

# Documentation

- **Read the Magnebot API documentation [here.](https://github.com/alters-mit/magnebot/blob/main/doc/magnebot_controller.md)**
- Read the API Documentation for other classes in the `magnebot` module [here.](https://github.com/alters-mit/magnebot/tree/main/doc)
- [Changelog](https://github.com/alters-mit/magnebot/blob/master/changelog.md)
- For more information regarding TDW, see the [TDW repo](https://github.com/threedworld-mit/tdw/). Relevant documentation includes:
  - [Getting Started With TDW](https://github.com/threedworld-mit/tdw/blob/master/Documentation/getting_started.md) 
  - [The Command API documentation](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md)
  - [Robotics in TDW](https://github.com/threedworld-mit/tdw/blob/master/Documentation/misc_frontend/robots.md)
  - [Docker and TDW](https://github.com/threedworld-mit/tdw/blob/master/Documentation/Docker/docker.md)
 
# Examples

- [Example controllers](https://github.com/alters-mit/magnebot/tree/main/controllers/examples) show actual examples for an actual use-case.
- [Demo controllers](https://github.com/alters-mit/magnebot/tree/main/controllers/demos) are meant to be use to generate demo videos or images; they include low-level TDW commands that you won't need to ordinarily use, and extend the [`DemoController`](https://github.com/alters-mit/magnebot/blob/main/doc/demo_controller.md) class instead of [`Magnebot`](https://github.com/alters-mit/magnebot/blob/main/doc/magnebot_controller.md) class.
- [Test controllers](https://github.com/alters-mit/magnebot/tree/main/controllers/tests) load the Magnebot into an empty room using the [`TestController`](https://github.com/alters-mit/magnebot/blob/main/doc/test_controller.md) class and test basic functionality.

# Backend

- [`OccupancyMapper`](https://github.com/alters-mit/magnebot/blob/main/util/occupancy_mapper.py) generates occupancy maps for each scene+layout combination, as well as floorplan and room images.
- [`doc_gen.py`](https://github.com/alters-mit/magnebot/blob/main/util/doc_gen.py) generates API documentation using [`py-md-doc`](https://pypi.org/project/py-md-doc/).

# Troubleshooting and debugging

### "I got an error"

- Update TDW (`pip3 install tdw -U`)
- Update the TDW build to match the TDW version.
- In the Magnebot constructor, set `debug=True`. This can provide additional output.
- [Read this.](https://github.com/threedworld-mit/tdw/blob/master/Documentation/misc_frontend/debug_tdw.md)
- If the stacktrace appears to lead to an error not handled in this repo or the `tdw` repo, create a GitHub issue and we'll address it as soon as possible.
- If you see this error, your Internet connection is probably not working:
```
line 35, in get_major_release
    return v.split(".")[1].strip()
IndexError: list index out of range
```

### "I can't launch in the simulation in a Docker container"

- Use the [TDW Docker image](https://github.com/threedworld-mit/tdw/blob/master/Documentation/Docker/docker.md).
- Set `launch_build=False` in the constructor; otherwise, the controller will try to launch a build on the same machine (outside of the container):

```python
from magnebot import Magnebot

m = Magnebot(launch_build=False)
```

### "Images are grainy / very dark / obviously glitchy"

- [Check the player log for Open GL errors](https://github.com/threedworld-mit/tdw/blob/master/Documentation/misc_frontend/debug_tdw.md).

### "The simulation is hanging."

- The scene will take at least a minute to initialize.
- [Check the player log for Open GL errors](https://github.com/threedworld-mit/tdw/blob/master/Documentation/misc_frontend/debug_tdw.md).

### "The simulation is too slow"

- Make sure you're using a GPU.
- [Check the player log for Open GL errors](https://github.com/threedworld-mit/tdw/blob/master/Documentation/misc_frontend/debug_tdw.md).

### "Some actions are slow"

- Some actions will take longer to complete than others. For example, `move_by(2)` will take more time to complete than `move_by(1)` because the distance is longer.
- Sometimes, the Magnebot's interaction with objects and the environment will cause the action to take a long time, such as a collision with another object.

### "Sometimes a task fails unexpectedly / The Magnebot's movements are inaccurate"

This simulation is 100% physics-driven. *Every task will sometimes fail.* Possible reasons for failure include:

- The Magnebot tried to grasp an object but there was an obstacle in the way.
- The Magnebot tried to move forward but got caught on furniture.
- The Magnebot tried to put an object in a container but the object bounced out.

*You* will need to develop solutions to handle cases like this. You can use the [`ActionStatus`](https://github.com/alters-mit/magnebot/blob/master/doc/action_status.md) return values to figure out why a task failed and [`SceneData`](https://github.com/alters-mit/magnebot/blob/master/doc/scene_data.md) to get the current state of the simulation.

### "The simulation behaves differently on different machines / Physics aren't deterministic"

We can't fix this because this is how the Unity physics engine works.

### "I need to know what each scene and layout looks like"

Images of each scene+layout combination are [here](https://github.com/alters-mit/magnebot/tree/master/doc/images/floorplans).

Occupancy map images are [here](https://github.com/alters-mit/magnebot/tree/master/doc/images/occupancy_maps).

### "I can't navigate through the scene"

The API is built assuming that you'll write navigation logic yourself. See: [`Magnebot.occupancy_map`](https://github.com/alters-mit/magnebot/blob/main/doc/magnebot_controller.md) and [`SceneState`](https://github.com/alters-mit/magnebot/blob/main/doc/scene_state.md).

### "I have a problem not listed here"

Create a GitHub Issue on this repo. Describe the problem and include steps to reproduce the bug. Please include your controller code if possible.

