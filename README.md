# Magnebot

Magnebot is a high-level robotics-like API for [TDW](https://github.com/threedworld-mit/tdw). The Magnebot can move around the scene and manipulate objects by picking them up with "magnets". The simulation is entirely driven by physics.

The Magnebot can be loaded into a [wide variety of scenes populated by interactable objects](https://github.com/alters-mit/magnebot/tree/main/doc/images/floorplans). 

At a low level, the Magnebot is driven by robotics commands such as set_revolute_target, which will turn a revolute drive. The high-level API combines the low-level commands into "actions", such as `grasp(target_object)` or `move_by(distance)`.

The Magnebot API supports both single-agent and multi-agent simulations.

<img src="https://raw.githubusercontent.com/alters-mit/magnebot/main/doc/images/reach_high.gif" />

# Requirements

See [TDW requirements](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/setup/install.md).

# Installation 

1. **`pip3 install magnebot`**
2. (Linux servers only): [Download the latest TDW build](https://github.com/threedworld-mit/tdw/releases/latest) and unzip it. For more information on setting up a TDW build on a server, [read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/setup/install.md). On a personal computer, the build will be downloaded and launched automatically.

#### Test if your installation was successful

1. Run this controller:

```python
from magnebot import MagnebotController

c = MagnebotController() # On a server, change this to MagnebotController(launch_build=False)

c.init_scene()
c.move_by(2)
print(c.magnebot.dynamic.transform.position)
c.end()
```

2. (Linux servers only): [Launch the TDW build.](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/core_concepts/launch_build.md) On a personal computer, the build will launch automatically.

#### Update an existing installation

1. `pip3 install tdw -U`
2. `pip3 install magnebot -U`
3. (Linux servers only): [Download the latest TDW build](https://github.com/threedworld-mit/tdw/releases/latest) and unzip it. On a personal computer, the build will automatically be upgraded the next time you create a TDW controller.

**If you are upgrading from Magnebot 1.3.2 or earlier, be aware that there are many changes to the API in Magnebot 2.0.0 and newer. [Read the changelog for more information.](doc/changelog.md)**

# Manual

## General

- [Changelog](doc/changelog.md)
- [Troubleshooting and debugging](doc/troubleshooting.md)
- [Performance benchmark](doc/benchmark.md)

## TDW Documentation

Before using Magnebot, we recommend you read TDW's documentation to familiarize yourself with some of the underlying concepts in this API:

- [Setup](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/setup/install.md)
- [Core Concepts](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/core_concepts/controller.md)
- [Objects and scenes](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/objects_and_scenes/overview.md)
- [Robots](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/robots/overview.md)
- [Multi-agent simulations](https://github.com/threedworld-mit/tdw/blob/master/Documentation/lessons/multi_agent/overview.md)

## `MagnebotController` (single-agent, high-level API)

The [`MagnebotController`](doc/api/magnebot_controller.md) offers a simplified API for single-agent simulations. Actions are non-interruptible; `self.move_by(2)` will simulate motion until the action ends (i.e. when the Magnebot has moved forward by 2 meters). This API mode has been optimized for ease of use and simulation speed.

- [Overview](doc/manual/magnebot_controller/overview.md)
- [Scene setup](doc/manual/magnebot_controller/scene_setup.md)
- [Output data](doc/manual/magnebot_controller/output_data.md)
- [Actions](doc/manual/magnebot_controller/actions.md)
- [Moving, turning, and collision detection](doc/manual/magnebot_controller/movement.md)
- [Arm articulation](doc/manual/magnebot_controller/arm_articulation.md)
- [Grasp action](doc/manual/magnebot_controller/grasp.md)
- [Camera rotation](doc/manual/magnebot_controller/camera_rotation.md)
- [Third-person cameras](doc/manual/magnebot_controller/third_person_camera.md)
- [Occupancy maps](doc/manual/magnebot_controller/occupancy_map.md)

## `Magnebot` (*n*-agent, lower-level API)

[`Magnebot`](doc/api/magnebot.md) is a TDW add-on that must be added to a TDW controller to be usable. `Magnebot` can be used in multi-agent simulations, but it requires a more extensive understanding of TDW than `MagnebotController`.

- [Overview](doc/manual/magnebot/overview.md)
- [Scene setup](doc/manual/magnebot/scene_setup.md)
- [Output data](doc/manual/magnebot/output_data.md)
- [Actions](doc/manual/magnebot/actions.md)
- [Moving, turning, and collision detection](doc/manual/magnebot/movement.md)
- [Arm articulation](doc/manual/magnebot/arm_articulation.md)
- [Grasp action](doc/manual/magnebot/grasp.md)
- [Camera](doc/manual/magnebot/camera.md)
- [Third-person cameras](doc/manual/magnebot/third_person_camera.md)
- [Occupancy maps](doc/manual/magnebot/occupancy_map.md)
- [Multi-agent simulations](doc/manual/magnebot/multi_agent.md)

## Actions

It is possible to define custom Magnebot actions by extending the [`Action`](doc/api/actions/action.md) class.

- [Overview](doc/manual/actions/overview.md)
- [Move and turn actions](doc/manual/actions/movement.md)
- [Arm articulation actions](doc/manual/actions/arm_articulation.md)
- [Inverse kinematics (IK) actions](doc/manual/actions/ik.md)
- [Camera actions](doc/manual/actions/camera.md)

***

# API

- [`MagnebotController`](doc/api/magnebot_controller.md)
- [`Magnebot`](doc/api/magnebot.md)
- [Other API documentation](doc/api)

***

# Examples

[Example controllers](https://github.com/alters-mit/magnebot/tree/main/controllers/examples) show actual examples for an actual use-case.

Other controllers in this repo:

- [Promo controllers](https://github.com/alters-mit/magnebot/tree/main/controllers/promos) are meant to be use to generate promo videos or images; they include low-level TDW commands that you won't need to ordinarily use.
- [Test controllers](https://github.com/alters-mit/magnebot/tree/main/controllers/tests) load the Magnebot into an empty room and test basic functionality.

***

# Higher-level APIs

The Magnebot API relies on the `tdw` Python module.  Every action in this API uses combinations of low-level TDW commands and output data, typically across multiple simulation steps.

This API is designed to be used as-is or as the base for an API with higher-level actions, such as the [Transport Challenge](https://github.com/alters-mit/transport_challenge). 

<img src="https://raw.githubusercontent.com/alters-mit/magnebot/main/doc/images/api_hierarchy.png" style="zoom:67%;" />

| API                                                          | Description                                                  |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| [Transport Challenge](https://github.com/alters-mit/transport_challenge) | Transport objects from room to room using containers as tools. |
| [Multimodal Challenge](https://github.com/alters-mit/multimodal_challenge) | Perceive objects in the scene using visual and audio input.  |
