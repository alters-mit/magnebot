##### MagnebotController

# Moving, turning, and collision detection

There are four movement actions in the [`MagnebotController`](../../api/magnebot_controller.md) that all all share basic functionality: `turn_by()`, `turn_to()`, `move_by()`, and `move_to()`. All of these actions set target angles for the Magnebot's wheels in order to move or turn the Magnebot.

## Directions

- `move_by(x)` moves the Magnebot forward by x meters.
- `move_by(-x)` moves the Magnebot backward by x meters.
- `turn_by(x)` turns the Magnebot clockwise by x degrees.
- `turn_by(-x)` turns the Magnebot counterclockwise by x degrees.

## Tipping over

While moving or turning, the Magnebot might start to tip over. This  can happen if the Magnebot is holding a heavy object, if its wheels roll over a ramp-like surface, etc. If this happens, the action will  immediately halt, the Magnebot will drop any objects with a mass greater than 8, and the action will return `ActionStatus.tipping`.

You can correct for tipping by reversing the action. For example, if `move_by(1)` returned `ActionStatus.tipping` then it is likely that `move_by(-1)` will correct the angle.

In the unlikely event that the Magnebot completely falls over, you can reset its position and rotation with the `reset_position()` action. The build will consider this to be a very fast motion, so it's not recommended you call this action unless you have to.

## Collision detection

By default, the Magnebot will stop moving or turning if:

- The Magnebot will start moving if any of its joints, wheels, or magnets collides with any object or any other Magnebot.
- If the previous action resulted in a collision and this action is the same "type". For example, if `move_by(8)` returns `ActionStatus.collision`, then `move_by(1)` will immediately return `ActionStatus.collision`; the Magnebot won't actually move on this second action.

```python
from magnebot import MagnebotController

c = MagnebotController()
c.init_scene()
status = c.move_by(8)
position = c.magnebot.dynamic.transform.position
print(status, position)
status = c.move_by(1)
position = c.magnebot.dynamic.transform.position
print(status, position)
c.end()
```

Output:

```
ActionStatus.collision [-7.31752580e-03  3.47320572e-03  4.94829607e+00]
ActionStatus.collision [-7.31752580e-03  3.47320572e-03  4.94829607e+00]
```

Collision detection is handled in `self.magnebot.collision_detection`, a [`CollisionDetection`](../../api/collision_detection.md) object. You can set the collision detection rules at the start of an action.

In this example, the Magnebot will collide with a wall. To ignore the wall collision while backing away, we'll set `self.magnebot.collision_detction.walls = False`

```python
from magnebot import MagnebotController

c = MagnebotController()
c.init_scene()
c.move_by(8)
c.magnebot.collision_detection.walls = False
c.move_by(-2)
c.magnebot.collision_detection.walls = True
c.end()
```

**DO NOT set `collision_detection` such that the Magnebot can repeatedly collide with obstacles.** If the Magnebot repeatedly collides with an object, it can cause the build to crash. This is a bug in the underlying Unity physics engine. In real life, such behavior would snap off a wheel, an arm joint, or otherwise break the robot. Do NOT repeatedly send the Magnebot in impossible directions.

***

**Next: [Arm articulation](arm_articulation.md)**

[Return to the README](../../../README.md)