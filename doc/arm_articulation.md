# Arm Articulation

## Inverse Kinematics

Two of the Magnebot's arm articulation actions, `reach_for()` and `move_by()`, use an inverse kinematics (IK) solver. [This is the IK solver.](https://github.com/Phylliade/ikpy)

The `reach_for()` and `move_by()` actions have optional `target_orientation` and `orientation_mode` parameters. `target_orientation` is the directional vector the Magnebot's magnet should align with, and `orientation_mode` is the referential vector. [For more information, read this.](https://notebook.community/Phylliade/ikpy/tutorials/Orientation) 

If `orientation_mode` and `target_orientation` are set to `none`, the solver will use the "full" referential frame; also, this is the fastest option to solve. However, the orientation parameters can affect the motion of the arm and whether the action succeeds or fails:

```python
from magnebot import TestController, Arm
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.ik.orientation_mode import OrientationMode

m = TestController()
m.init_scene()
m.add_camera(position={"x": 0.6, "y": 1.6, "z": 1.6})
# Use default orientation parameters.
m.reach_for(target={"x": 0.2, "y": 0.5, "z": 0.5}, arm=Arm.left, absolute=False)
m.reset_arm(arm=Arm.left)
# Explicitly set orientation parameters. The motion will be very different!
status = m.reach_for(target={"x": 0.2, "y": 0.5, "z": 0.5}, arm=Arm.left, absolute=False,
                     target_orientation=TargetOrientation.right, orientation_mode=OrientationMode.y)
m.end()
```

### Automatic IK orientation solver

By default, `target_orientation=TargetOrientation.auto` and `orientation_mode=OrientationMode.auto`. This means that the Magnebot will automatically choose an orientation solution, given the target position. It does this by comparing the target position to an array of pre-calculated positions and orientations. The positions and orientations are pre-calculated using `ik_solution.py` which can be found in the `util/` directory of this repo. You can run this yourself with different parameters but be aware that it is a *long* process (at least 36 hours).

The script `ik_images.py` (also located in `util/`) will generate images of vertical slices of the orientation solutions, which can be found [here](https://github.com/alters-mit/magnebot/tree/master/doc/images/ik).

![](images/ik/legend.jpg) ![](images/ik/left/0.1.jpg) ![](images/ik/left/0.2.jpg)

### Accuracy and performance

We benchmark the IK orientation solver using `controllers/tests/benchmark/ik_orientation.py`. In this test controller, the Magnebot will `reach_for()` an array of target positions and record whether the outcome of the action was guessed correctly:

| `target_orientation`, `orientation_mode`      | Accuracy | Total time elapsed   |
| --------------------------------------------- | -------- | -------------------- |
| `none`, `none`                                | 47.5%    | 3 minutes 48 seconds |
| `auto`, `auto` (1 consecutive attempt)        | 79%      | 4 minutes 5 seconds  |
| `auto`, `auto` (up to 5 consecutive attempts) | 81.5%    | 5 minutes 50 seconds |

### Limitations to the IK orientation solver

- The automatic IK orientation solver can be inaccurate due to the granularity of the pre-calculated array; if the cloud of positions was denser, it could choose a more tightly-fitting solution. Due to the time required to generate these solutions, we haven't yet calculated how position cloud density actually affects accuracy and performance but we believe that the current data is a reasonable balance between the two.
- The Magnebot IK orientation solver assumes that the Magnebot's arms are in their neutral position. If they're at any other position, the IK solution found using `auto`, `auto` parameters will be inaccurate. You can reset the arms to their neutral positions with the `reset_arm()` function.
- The IK solver doesn't (and can't) automatically handle situations where there are obstructions such as walls or other objects.

### Explicitly setting IK orientation parameters

You can explicitly set the `target_orientation` and `orientation_mode` parameters in the `reach_for()` and `grasp()` action. You might want to do this if:

- You want to try different orientations to move the arm around an obstruction.
- You want to train the Magnebot using different orientations (which might be more accurate than the default `auto` approach).
- You need to the Magnebot to pick up an object at a particular angle.

Some guidelines regarding the orientation parameters:

- For a complete list of enum values for `TargetOrientation` and `OrientationMode`, read [this](api/target_orientation.md) and [this](api/orientation_mode.md).
- Both parameters must be `auto` or neither.
- Both parameters must be `none` or neither.
- Setting both parameters to `none` will usually make the arm bend in the most "direct" path.

## Torso movement

The Magnebot's torso slides up and down on a prismatic joint. Prismatic joints aren't defined in the underlying `ikpy` module (though [apparently it *is* possible to implement one](https://github.com/Phylliade/ikpy/issues/96)).

In the Magnebot API, prismatic movement is handled *iteratively*. The function `self._start_ik()` will take a best-guess of the torso position and get an IK solution. If the IK solution fails (if the magnet won't be close enough to the target), a different torso position is tried.

## Defining your own arm articulation action

You can define your own action that uses inverse kinematics by calling the hidden function `self._start_ik()`. For example implementation, see `controllers/examples/custom_api.py` which adds a `push()` action.

Other useful functions:

- `self._do_arm_motion()` will loop until the joints stop moving. If your action only involves a few specific joints, the action will generally run faster if you supply a `joint_ids` parameter.
- `self._append_ik_commands()` converts a list of angles to TDW commands. Unlike `_start_ik()`, it doesn't actually plot an IK solution.

## Getting a target position for `grasp()`

In the `grasp()` action, the Magnebot needs to pick a target position on the surface of the object. The target is determined in `self._get_grasp_target()`.

- The Magnebot gets the side on the object closest to the Magnet using [`Bounds` data](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/output_data.md#Bounds) in the function `self._get_nearest_side()`
  - If the object is above the magnet, the Magnebot will ignore the lowest side (i.e. the base of the object), since that's usually impossible to reach.
- The Magnebot [raycasts](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/output_data.md#Raycast) from the Magnet to that position on the bounds. If the raycast hits the target, the Magnebot opts for the raycast position instead (which is usually tighter-fitting to the actual geometry of the object). The raycast might fail if there is an object in the way.

## Debug mode

If `self._debug == True`, then `recach_for()`, `grasp()`, and any other custom action that calls `self._start_ik()` will create a plot of the IK solution. This doesn't work on remote servers.