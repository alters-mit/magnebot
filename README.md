# Magnebot

Magnebot is a high-level robotics-like API for [TDW](https://github.com/threedworld-mit/tdw). The Magnebot can move around the scene and manipulate objects by picking them up with "magnets". The simulation is entirely driven by physics.

The Magnebot can be loaded into a [wide variety of scenes populated by interactable objects](https://github.com/alters-mit/magnebot/tree/main/doc/images/floorplans). 

At a low level, the Magnebot is driven by robotics commands such as set_revolute_target, which will turn a revolute drive. The high-level API combines the low-level commands into "actions", such as `grasp(target_object)` or `move_by(distance)`.

<img src="https://raw.githubusercontent.com/alters-mit/magnebot/main/doc/images/reach_high.gif" />

# Requirements

See [TDW requirements](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/core_concepts/install.md).

# Installation 

1. **`pip3 install magnebot`**
2. (Linux servers only): [Download the latest TDW build](https://github.com/threedworld-mit/tdw/releases/latest) and unzip it. For more information on setting up a TDW build on a server, [read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/core_concepts/install.md). On a personal computer, the build will be downloaded and launched automatically.

#### Test if your installation was successful

1. Run this controller:

```python
from magnebot import MagnebotController

m = MagnebotController() # On a server, change this to MagnebotController(launch_build=False)

m.init_scene()
m.move_by(2)
m.end()
```

2. (Linux servers only): [Launch the TDW build.](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/core_concepts/launch_build.md) On a personal computer, the build will launch automatically.

#### Update an existing installation

1. `pip3 install tdw -U`
2. `pip3 install magnebot -U`
3. (Linux servers only): [Download the latest TDW build](https://github.com/threedworld-mit/tdw/releases/latest) and unzip it. On a personal computer, the build will automatically be upgraded the next time you create a TDW controller.

# API Modes

The Magnebot API supports two modes:

### 1. `MagnebotController`

`MagnebotController` offers an easy to use API. Each action call ends when the action is totally done; for example, `move_by(2)` will iterate through physics steps until the Magnebot has moved 2 meters or until it otherwise needs to stop, such as on a collision.

Advantages:

- Simple API
- Automatically adds useful settings such as frame-skipping and an object manager

 Disadvantages: 

- Single-agent only
- Actions can't be interrupted

```python
from magnebot import MagnebotController

m = MagnebotController() # On a server, change this to MagnebotController(launch_build=False)

m.init_scene()
m.move_by(2)
print(m.magnebot.dynamic.transform.position)
m.end()
```

### 2. `Magnebot`

`Magnebot` is an add-on that can be attached to a controller; it is automatically initialized within a `MagnebotController`. 

Advantages:

- Can be used in *any* TDW controller
- Actions can be interrupted
- Supports multi-agent simulations

Disadvantages:

- API is more complicated and requires more familiarization with TDW
- By default, it lacks certain key add-ons that are automatically added to the `MagnebotController` (you can add them manually in your own controller).

This example replicates the behavior of the previous example, but using a `Magnebot` agent instead of a `MagnebotController`:

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.step_physics import StepPhysics
from magnebot import Magnebot, ActionStatus

c = Controller()
step_physics = StepPhysics(num_frames=10)
magnebot = Magnebot()
c.add_ons.extend([step_physics, magnebot])
c.communicate(TDWUtils.create_empty_room(12, 12))
magnebot.move_by(2)
while magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])
print(magnebot.dynamic.transform.position)
c.communicate({"$type": "terminate"})
```

# Documentation

- **[Magnebot API](https://github.com/alters-mit/magnebot/blob/main/doc/api/magnebot_controller.md)**
- [**APIs for other classes in the Magnebot module**](https://github.com/alters-mit/magnebot/tree/main/doc/api)
- **[How to define custom APIs](https://github.com/alters-mit/magnebot/blob/main/doc/custom_apis.md)**
  - [Scene setup](https://github.com/alters-mit/magnebot/blob/main/doc/scene.md)
  - [Arm articulation](https://github.com/alters-mit/magnebot/blob/main/doc/arm_articulation.md)
  - [Movement](https://github.com/alters-mit/magnebot/blob/main/doc/movement.md)
- [Changelog](https://github.com/alters-mit/magnebot/blob/main/doc/changelog.md)
- [Troubleshooting and debugging](https://github.com/alters-mit/magnebot/blob/main/doc/troubleshooting.md)
- For more information regarding TDW, see the [TDW repo](https://github.com/threedworld-mit/tdw/). Relevant documentation includes:
  - [Getting Started With TDW](https://github.com/threedworld-mit/tdw/blob/master/Documentation/getting_started.md) 
  - [The Command API documentation](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md)
  - [Robotics in TDW](https://github.com/threedworld-mit/tdw/blob/master/Documentation/misc_frontend/robots.md)
  - [Docker and TDW](https://github.com/threedworld-mit/tdw/blob/master/Documentation/Docker/docker.md)
- [Benchmark](https://github.com/alters-mit/magnebot/blob/main/doc/benchmark.md)

# Examples

[Example controllers](https://github.com/alters-mit/magnebot/tree/main/controllers/examples) show actual examples for an actual use-case.

| Controller      | Description                                                  |
| --------------- | ------------------------------------------------------------ |
| `pick_up.py`    | A simple example of how to pick up an object in the scene. You should try and review this example first. |
| `custom_api.py` | An example of how to create a custom scene and a custom action. This is meant for more advanced users. |

#### Other controllers in this repo

- [Promo controllers](https://github.com/alters-mit/magnebot/tree/main/controllers/promos) are meant to be use to generate promo videos or images; they include low-level TDW commands that you won't need to ordinarily use.
- [Test controllers](https://github.com/alters-mit/magnebot/tree/main/controllers/tests) load the Magnebot into an empty room and test basic functionality.

# API Hierarchy

The Magnebot API relies on the `tdw` Python module.  Every action in this API uses combinations of low-level TDW commands and output data, typically across multiple simulation steps.

This API is designed to be used as-is or as the base for an API with higher-level actions, such as the [Transport Challenge](https://github.com/alters-mit/transport_challenge). To learn how to write your own API extension, [read this](https://github.com/alters-mit/magnebot/blob/main/doc/custom_apis.md).

<img src="https://raw.githubusercontent.com/alters-mit/magnebot/main/doc/images/api_hierarchy.png" style="zoom:67%;" />

| API                                                          | Description                                                  |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| [Transport Challenge](https://github.com/alters-mit/transport_challenge) | Transport objects from room to room using containers as tools. |

# Backend

- [`OccupancyMapper`](https://github.com/alters-mit/magnebot/blob/main/util/occupancy_mapper.py) generates occupancy maps for each scene+layout combination, as well as floorplan and room images.
- [`doc_gen.py`](https://github.com/alters-mit/magnebot/blob/main/util/doc_gen.py) generates API documentation using [`py-md-doc`](https://pypi.org/project/py-md-doc/).
