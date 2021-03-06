# Arm Articulation

## Inverse Kinematics

Two of the Magnebot's arm articulation actions, `reach_for()` and `move_by()`, use an inverse kinematics (IK) solver. [This is the IK solver.](https://github.com/alters-mit/ikpy) It's a fork of [this repo](https://github.com/Phylliade/ikpy) with better support for prismatic joints.

The `reach_for()` and `move_by()` actions have optional `target_orientation` and `orientation_mode` parameters. `target_orientation` is the directional vector the Magnebot's magnet should align with, and `orientation_mode` is the referential vector. [For more information, read this.](https://notebook.community/Phylliade/ikpy/tutorials/Orientation) 

If `orientation_mode` and `target_orientation` are set to `none`, the solver will use the "full" referential frame, which is typically the most "normal" looking motion (the arm will extend towards the target). However, these are not typically the *best* orientation parameters; an IK action might fail with one set of orientation parameters and succeed with another: 

```python
from magnebot import Magnebot, Arm
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.ik.orientation_mode import OrientationMode

m = Magnebot()
m.init_scene()
m.add_camera(position={"x": 0.6, "y": 1.6, "z": 1.6})
target = {"x": 0.2, "y": 0.5, "z": 0.5}
# Use default orientation parameters (auto, auto).
m.reach_for(target=target, arm=Arm.left)
m.reset_arm(arm=Arm.left)
# Explicitly set orientation parameters. The motion will be very different!
m.reach_for(target=target, arm=Arm.left,
            target_orientation=TargetOrientation.right, orientation_mode=OrientationMode.y)
m.end()
```

### Automatic IK orientation solver

By default, `target_orientation=TargetOrientation.auto` and `orientation_mode=OrientationMode.auto`: 

```python
from magnebot import Magnebot, Arm

m = Magnebot()
m.init_scene()
# Use default orientation parameters (auto, auto).
target = {"x": 0.2, "y": 0.5, "z": 0.5}
m.reach_for(target=target, arm=Arm.left)
```

This means that the Magnebot will automatically choose an orientation solution, given the target position. It does this by comparing the target position to an array of pre-calculated positions and orientations. The positions and orientations were pre-calculated using `ik_solution.py` which can be found in the `util/` directory of this repo.

Additionally, it is possible for the IK action to fail even after taking a guess. In these cases, if orientation parameters are (`auto`, `auto`), the Magnebot will try to readjust the arm using parameters from neighboring cells in the grid of solutions (in other words, the Magnebot may try more than one motion to reach the target). If the parameters are set to anything else, the Magnebot won't automatically make multiple attempts to reach the target position.

The script `ik_images.py` (also located in `util/`) will generate images of vertical slices of the orientation solutions, which can be found [here](https://github.com/alters-mit/magnebot/tree/master/doc/images/ik). Below are a few examples:

![](images/ik/legend.jpg) ![](images/ik/left/0.1.jpg) ![](images/ik/left/0.2.jpg)

### Accuracy and performance

We've benchmarked the IK orientation solver using `controllers/tests/benchmark/ik.py`. In this test controller, the Magnebot will `reach_for()` an array of target positions and record whether the outcome of the action was guessed correctly. A correct guess is an action that returns `success` or `cannot_reach`. If the action returns `cannot_reach`, this means that the solver knew ahead of time that the action was going to fail and the Magnebot never tried to bend its arm, rather than reaching for an impossible target. If the action returns `failed_to_bend` or `failed_to_reach`, this counts as a failure; the Magnebot tried to reach for a position that the solver guessed was reachable, but failed to arrive at the target.

| Action                                                       | Accuracy | Time elapsed (200 trials) |
| ------------------------------------------------------------ | -------- | ------------------------- |
| `reach_for(target, arm)`                                     | 94.5%    | 02:45                     |
| `reach_for(target, arm, TargetOrientation.none, OrientationMode.none)` | 63%      | 02:15                     |

### Limitations to the IK orientation solver

- The pre-calculated IK solutions are only accurate assuming that the Magnebot's arms are in their neutral position. Successive `reach_for()` or `grasp()` actions will be less accurate than the initial action. You should either:
  - Reset the arms to their neutral positions with the `reset_arm()` function between IK actions.
  - Explicitly set IK orientation parameters (see below).
- The IK solver doesn't (and can't) automatically handle situations where there are obstructions such as walls, other objects, objects held by a magnet, or the Magnebot's body.
- **There is no general solution for orientation parameters.** We can't provide general guidelines for which orientation parameters to use for an arbitrary pose and target. It's far too complex a problem! The (`auto`, `auto`) parameters are meant to establish an accurate baseline under reasonable constraints. If you want to select orientation parameters accurately and automatically for more complex cases, you'll need to train your model to try different orientation parameters.

### Explicitly setting IK orientation parameters

You can explicitly set the `target_orientation` and `orientation_mode` parameters in the `reach_for()` and `grasp()` action. You might want to do this if:

- You want to try different orientations to move the arm around an obstruction.
- You want to use sequential IK actions without having to call `reset_arm()`.
- You want to train the Magnebot using different orientations (which might be more accurate than the default `auto` approach).
- You need to the Magnebot to pick up an object at a particular angle.

Some guidelines regarding the orientation parameters:

- For a complete list of enum values for `TargetOrientation` and `OrientationMode`, read [this](api/target_orientation.md) and [this](api/orientation_mode.md).
- Both parameters must be `auto` or neither.
- Both parameters must be `none` or neither.
- Setting both parameters to `none` is *usually* the best solution and will  make the arm bend in the most "direct" path. Approximately 50% of the pre-calculated solutions use (`none`, `none`) (not including positions where no solution is possible).

### Setting the `arrived_at` parameter

The `arrived_at` parameter in the `reach_for()` action determines minimum distance from the magnet to the target. The action immediately stops if the magnet is within this distance. Increasing `arrived_at` therefore "improves" the success rate of an IK action.

### Other miscellaneous notes:

- If the orientation parameters are (`auto`, `auto`), the the target orientation mode is selected via the function `self._get_ik_orientation()`. This function has been highly optimized: on average, it requires 0.003 seconds to run.
- The IK orientation solver will guess ahead of time whether there is any solution. We've compared this guess to whether the Magnebot can in fact reach the target and found it guesses correctly 96.25% of the time.

## Defining your own arm articulation action

You can define your own action that uses inverse kinematics by calling the hidden function `self._start_ik()`. For example implementation, see `controllers/examples/custom_api.py` which adds a `push()` action. For documentation, read the docstring for `_start_ik()` in `magnebot_controller.py`.

Every arm articulation action needs to begin with `self._start_action()` and end with `self._end_action()`:

```python
from magnebot import Magnebot, ActionStatus

class MyMagnebot(Magnebot):
    def my_action(self) -> ActionStatus:
        self._start_action()
        
        # Your code here.
        
        self._end_action()
        return ActionStatus.success
```

There are many other useful backend functions for creating a custom API. [Read this](custom_apis.md) for a list. The following are functions useful specifically for IK actions:

| Function                               | Description                                                  |
| -------------------------------------- | ------------------------------------------------------------ |
| `self._start_ik()`                     | Given a target position and other parameters, find an IK solution. Returns the angles of each joint. |
| `self._append_ik_commands()`           | Convert a list of angles to TDW commands. Unlike `_start_ik()`, it doesn't actually calculate an IK solution. |
| `self._do_ik()`                        | Higher-level function for code shared by `reach_for()` and `grasp()`. |
| `self._do_arm_motion()`                | Loop until the joints stop moving. If your action only involves a few specific joints, the action will generally run faster if you supply a `joint_ids` parameter. |
| `self._get_initial_angles()`           | Returns the angles of the arm joints prior to arm motion.    |
| `self._stop_joints()`                  | Stop all joint movement.                                     |
| `self._get_ik_orientations()`          | Returns a list of possible IK orientation parameters, given the target position and arm. |
| `self._y_position_to_torso_position()` | Converts a y worldspace coordinate to a torso prismatic joint position. |
| `self._absolute_to_relative()`         | Covert a worldspace position to a position relative to the Magnebot. |

## Getting a target position for `grasp()`

In the `grasp()` action, the Magnebot needs to pick a target position on the surface of the object.

- The Magnebot [spherecasts](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md#send_spherecast) from the magnet to the center of the object. If any of the rays hit the object, the Magnebot aims for the nearest hit point. There might not be any hits (for example, the object is on a counter, which obstructs the spherecast), in which case:
- The Magnebot gets the side on the object closest to the Magnet using [`Bounds` data](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md#send_bounds).
  - If the object is above the magnet, the Magnebot will ignore the lowest side (i.e. the base of the object), since that's usually impossible to reach.
  - There is a cached list of valid sides per object; the Magnebot selects the nearest side from this list. For example, if the object isn't an open box, the top of the box isn't a valid side because that's just empty space.
  - If there isn't a valid nearest side, the Magnebot will aim for the center of the object and hope for the best.
  - The controller [raycasts](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md#send_raycast) from the nearest side of the object to the center of the object to get the nearest point on the mesh surface.

## Other arm articulation actions

Other arm articulation actions, namely `reset_arm()` and `drop()`, don't rely on IK.

- `reset_arm()` explicitly sets the target positions of each arm joint via the backend function `self._get_reset_arm_commands()`. 
- `drop()` is similarly structured: The commands to drop the object are created via `self._append_drop_commands()`. Additionally, calling the function `self._wait_until_objects_stop(object_ids)` will wait until all of the objects in the list stop moving. This is potentially very useful for other actions: In the [Transport Challenge API](https://github.com/alters-mit/transport_challenge), for example, `self._wait_until_objects_stop()` is called within the `put_in()` action in order to wait until the objects that were put in the container stop moving before checking whether they're actually in the container.

## Debug mode

If `self._debug == True`, then `recach_for()`, `grasp()`, and any other custom action that calls `self._start_ik()` will create a plot of the IK solution. This doesn't work on remote servers.