# Movement

There are four movement actions in the [Magnebot API](../api/magnebot_controller,md) that all all share basic functionality: `turn_by()`, `turn_to()`, `move_by()`, and `move_to()`. All of these actions set target angles for the Magnebot's wheels in order to move or turn the Magnebot.

## Directions

- `move_by(x)` moves the Magnebot forward by x meters.
- `move_by(-x)` moves the Magnebot backward by x meters.
- `turn_by(x)` turns the Magnebot clockwise by x degrees.
- `turn_by(-x)` turns the Magnebot counterclockwise by x degrees.

## Tipping over

While moving or turning, the Magnebot might start to tip over. This can happen if the Magnebot is holding a heavy object, if its wheels roll over a ramp-like surface, etc. If this happens, the action will immediately halt, the Magnebot will drop any objects with a mass greater than 8, and the action will return `ActionStatus.tipping`. 

You can correct for tipping by reversing the action. For example, if `move_by(1)` returned `ActionStatus.tipping` then it is likely that `move_by(-1)` will correct the angle. 

In the unlikely event that the Magnebot completely falls over, you can reset its position and rotation with the `reset_position()` action. The build will consider this to be a very fast motion, so it's not recommended you call this action unless you have to.

## Collisions

By default, the Magnebot will stop moving or turning if:

- On the previous frame, the Magnebot collided with a wall.
- On the previous frame, the Magnebot collided with an object with a mass greater than 8.
- The previous action ended in a collision and was in the same direction as the current action. For example, if the previous action was `move_by(1)` and it ended in a collision, `move_by(0.5)` will immediately fail. But `turn_by(20)` or `move_by(-2)` might succeed.

To determine what the Magnebot collided with at the end of an action, see `self.colliding_with_wall` (a boolean) and `self.colliding_objects` (a list of object IDs).

### The `stop_on_collision` parameter

Each move and  turn action has an optional `stop_on_collision` parameter. Its default value is True, meaning that the Magnebot will stop moving or turning if any of the aforementioned collision events happen.

You can override collision detection by setting `stop_on_collision=False` in any of the move or turn actions:

```python
from magnebot import Magnebot

m = Magnebot()
m.init_scene(scene="1a", layout=2, room=5)
status = m.move_by(8)
print(status)  # ActionStatus.collision
status = m.move_by(1)  # This action will immediately fail!
print(status)  # ActionStatus.collision
status = m.move_by(-3, stop_on_collision=False)
print(status)  # ActionStatus.tipping
m.end()
```

**Reasons to set `stop_on_collision=False` include:**

- You want the Magnebot to squeeze through a narrow passage in which it will harmlessly scrape alongside objects.
- You want the Magnebot to push objects out of the way as it moves.
- You want to move or turn the Magnebot away from an object or wall it is currently colliding with.

**Reasons to set `stop_on_collision=True` (the default value) include:**

- The default collision detection will prevent the Magnebot from entering situations that are difficult or impossible to recover from (for example, an arm getting caught on a chair).
- **Repeatedly colliding into the same obstacle can cause the build to crash to desktop.** In real life, such behavior would snap off a wheel, an arm joint, or otherwise break the robot. Do NOT repeatedly send the Magnebot in impossible directions.

### Customizing collision detection

So far this documentation has covered the behavior of `stop_on_collision` if it's a boolean. But it can also be a [`CollisionDetection` object](../api/collision_detection.md) if you want to fine-tune collision detection:

```python
from magnebot import Magnebot, ActionStatus
from magnebot.collision_detection import CollisionDetection

m = Magnebot()
m.init_scene(scene="4c", layout=1, room=1)
status = m.move_by(1)
if status == ActionStatus.collision:
    # For the next action, ignore these objects.
    exclude_objects = m.colliding_objects
    # If the Magnebot is colliding with the wall, ignore it for the next action.
    walls = not m.colliding_with_wall
    print("Colliding with:", [m.objects_static[o].name for o in m.colliding_objects])
    # Move backwards with custom collision detection.
    status = m.move_by(-1, stop_on_collision=CollisionDetection(walls=walls, exclude_objects=exclude_objects))
else:
    status = m.move_by(-1)
# The Magnebot collided with a different object!
if status == ActionStatus.collision:
    print(m.colliding_with_wall)
    print([m.objects_static[o].name for o in m.colliding_objects])
m.end()
```

**Reasons to set `stop_on_collision` to a custom `CollisionDetection` object include:**

- You want to move the Magnebot away from an object that it's colliding with while still detecting collisions with everything else.
- .You want the Magnebot to push certain objects while halting when it collides with other objects.
- There are certain objects in the scene that are either always ok or always not ok for the Magnebot to collide with, regardless of their mass.

**Reasons to set `stop_on_collision` to a boolean value:**

- Defining a `CollisionDetection` object involves a lot of parameters.  It might be easier to train a model using very simple collision detection rules.
- Usually, the boolean collision detection rules are sufficient for basic tasks.

## Defining your own custom movement action

Unlike [arm articulation](arm_articulation.md), where you will often need to define a custom action to achieve a certain pose or motion, the move and turn actions that already exist in the Magnebot API should be sufficient for most use cases. Additionally, move and turn actions are somewhat harder to code than arm articulation actions due to the complexities of collision detection.

As with all [custom actions](custom_apis.md), a move action should begin with `self._start_action()` and end with `self._end_action()`. You should also start the action with `self._start_move_or_turn()` which will make the Magnebot moveable and set its torso and column to their neutral positions.

To move or turn, you will need to set the angles of the Magnebot's wheels. The wheel IDs are stored in [`self.magnebot_static.wheels`](api/magnebot_static.md) and the current wheel angles are stored in [`self.state.joint_angles`](api/scene_state.md). Set the target angle with [`set_revolute_target`](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md#set_revolute_target). [This code in `move_by()`](https://github.com/alters-mit/magnebot/blob/3f537fcd95685efeadf7200208a310a4c6a2f10c/magnebot/magnebot_controller.py#L699-L707) is a good example of how to set the target angles for each wheel.

Below are useful backend functions for moving and turning:

| Function                | Description                                                  |
| ----------------------- | ------------------------------------------------------------ |
| `_start_move_or_turn()` | Start a move or turn action.                                 |
| `_stop_wheels()`        | Stop wheel movement.                                         |
| `_stop_tipping()`       | Handle situations where the Magnebot is tipping by dropping all heavy objects. |
| `_wheels_are_turning()` | Returns True if the wheels are currently turning.            |
| `_collided()`           | Returns True if the Magnebot collided with a wall or with an object that should cause it to stop moving. |

