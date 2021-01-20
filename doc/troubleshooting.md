# Troubleshooting and debugging

### "I got an error / I found a bug"

- Read the rest of this guide, which includes solutions to common errors.
- Try updating:
  - `pip3 install magnebot -U`
  - `pip3 install tdw -U`
  - Download [the latest release of the TDW build](https://github.com/threedworld-mit/tdw/releases/latest/) and unzip the file. 
- Read the rest of this guide.
- In the Magnebot constructor, set `debug=True`. This can provide additional output.
- [Read the TDW debug guide](https://github.com/threedworld-mit/tdw/blob/master/Documentation/misc_frontend/debug_tdw.md).
- If you're still getting errors or buggy behavior, create a GitHub Issue on this repo. Describe the problem and include steps to reproduce the bug. If possible, please also include [the player log](https://github.com/threedworld-mit/tdw/blob/master/Documentation/misc_frontend/debug_tdw.md).

### "I got an IndexError that says that a list index is out of range"

If you see this error, your Internet connection is probably not working:

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

### "The simulation is hanging."

- TDW downloads most of its assets (such as 3D models) at runtime rather than store them locally. The first time you call `init_scene()`, it will need a minute or so to download everything. After that, the assets are cached in memory until the build process is terminated, meaning that subsequent `init_scene()` calls will be much faster.
  - We have found that certain locations in China download TDW models very slowly.
- [Check the player log for errors](https://github.com/threedworld-mit/tdw/blob/master/Documentation/misc_frontend/debug_tdw.md).

### "The simulation is too slow"

- Make sure the build is using a GPU.
- [Check the player log for errors](https://github.com/threedworld-mit/tdw/blob/master/Documentation/misc_frontend/debug_tdw.md).

### "Images are grainy / very dark / obviously glitchy"

- [Check the player log for Open GL errors](https://github.com/threedworld-mit/tdw/blob/master/Documentation/misc_frontend/debug_tdw.md).

### "Some actions are slow"

- Some actions will take longer to complete than others. For example, `move_by(2)` will take more time to complete than `move_by(1)` because the distance is longer.
- Sometimes, the Magnebot's interaction with objects and the environment will cause the action to take a long time, such as a collision with another object.

### "Sometimes a task fails unexpectedly / The Magnebot's movements are inaccurate"

This simulation is 100% physics-driven. *Every task will sometimes fail.* Possible reasons for failure include:

- The Magnebot tried to grasp an object but there was an obstacle in the way.
- The Magnebot tried to move forward but got caught on furniture.
- The Magnebot tried to put an object in a container but the object bounced out.

*You* will need to develop solutions to handle cases like this. You can use the [`ActionStatus`](action_status.md) return values to figure out why a task failed and [`SceneState`](scene_state.md) to get the current state of the simulation.

### "The simulation behaves differently on different machines / Physics aren't deterministic"

We can't fix this because this is how the Unity physics engine works.

### "I need to know what each scene and layout looks like"

- Images of each scene+layout combination are [here](https://github.com/alters-mit/magnebot/tree/main/doc/images/floorplans).
- Occupancy map images are [here](https://github.com/alters-mit/magnebot/tree/main/doc/images/occupancy_maps).

### "I can't navigate through the scene"

This API doesn't include navigation, but it does give you sufficient data to write your own navigation logic. See: [`Magnebot.occupancy_map`](magnebot_controller.md) and [`SceneState`](scene_state.md).

### "The Magnebot tipped over"

It is possible, though unlikely, that the Magnebot will tip over. If this happens, you can call `reset_position()`.

### "The Magnebot dropped a held object while moving"

While moving, if the Magnebot is about to tip over, it will immediately stop moving and drop all held objects because it could be tipping due to an overly heavy object. The API always prioritizes preventing the Magnebot from tipping over.

### "I have a problem not listed here"

Create a GitHub Issue and explain the problem.