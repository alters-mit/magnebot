##### MagnebotController

# Moving, turning, and collision detection

There are four movement actions in the [`MagnebotController`](../../api/magnebot_controller.md) that all all share basic functionality: `turn_by(angle)`, `turn_to(target)`, `move_by(distance)`, and `move_to(target)`. All of these actions set target angles for the Magnebot's wheels in order to move or turn the Magnebot.

## Directions

- `move_by(x)` moves the Magnebot forward by x meters.
- `move_by(-x)` moves the Magnebot backward by x meters.
- `turn_by(x)` turns the Magnebot clockwise by x degrees.
- `turn_by(-x)` turns the Magnebot counterclockwise by x degrees.

## `arrived_at`, `aligned_at`, and `arrived_offset`

`move_by(distance)` has an optional parameter `arrived_at`. If the Magnebot is within this many meters of the target distance, the action is a success. Increasing the `arrived_at` distance will result in faster but less accurate movement:

```python
from time import time
from magnebot import MagnebotController

c = MagnebotController()
c.init_scene()
t0 = time()
c.move_by(distance=2, arrived_at=0.1)
print(c.magnebot.dynamic.transform.position)
print(time() - t0)

c.init_scene()
t0 = time()
c.move_by(distance=2, arrived_at=0.3)
print(c.magnebot.dynamic.transform.position)
print(time() - t0)

c.end()
```

Output:

```
[-8.41087010e-03  1.10985515e-04  1.91277754e+00]
0.76544189453125
[-0.00764174  0.0022367   1.73882854]
0.23400402069091797
```

`turn_by(angle)` and `turn_to(target)` have an optional parameter `aligned_at`. If the Magnebot is within this many degrees of the target angle, the action is a success. Increasing the `aligned_at` distance will result in faster but less accurate movement:

```python
from time import time
from magnebot import MagnebotController

c = MagnebotController()
c.init_scene()
t0 = time()
c.turn_by(angle=45, aligned_at=1)
print(time() - t0)

c.init_scene()
t0 = time()
c.turn_by(angle=45, aligned_at=3)
print(time() - t0)

c.end()
```

Output:

```
0.2699716091156006
0.18059253692626953
```

`move_to(target)` is a combination of `turn_to(target, aligned_at)` and `move_by(distance, arrived_at)` and therefore has both an `aligned_at` parameter and an `arrived_at` parameter. It also has an `arrived_offset` parameter. After automatically calculating `distance` (i.e. the distance to `target`), the action will subtract `arrived_offset`. This is useful for approaching an object without colliding with it:

```python
from tdw.tdw_utils import TDWUtils
from magnebot import MagnebotController

class MyController(MagnebotController):
    def init_scene(self):
        scene = [{"$type": "load_scene",
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12)]
        objects = self.get_add_physics_object(model_name="rh10",
                                        position={"x": 0.04, "y": 0, "z": 1.081},
                                        object_id=self.get_unique_id())
        self._init_scene(scene=scene,
                         objects=objects,
                         position={"x": 1, "y": 0, "z": -3},
                         rotation={"x": 0, "y": 46, "z": 0})

    def run(self, arrived_offset: float) -> None:
        self.init_scene()
        object_id = list(self.objects.transforms.keys())[0]
        status = self.move_to(object_id, arrived_at=0.3, aligned_at=1, arrived_offset=arrived_offset)
        print(status)

if __name__ == "__main__":
    c = MyController()
    c.run(arrived_offset=0)
    c.run(arrived_offset=0.3)
    c.end()
```

Output:

```
ActionStatus.collision
ActionStatus.success
```

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