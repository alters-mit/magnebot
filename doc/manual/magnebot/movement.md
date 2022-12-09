##### Magnebot

# Moving, turning, and collision detection

There are four movement actions in the [`Magnebot`](../../api/magnebot.md) that all all share basic functionality: `turn_by(angle)`, `turn_to(target)`, `move_by(distance)`, and `move_to(target)`. All of these actions set target angles for the Magnebot's wheels in order to move or turn the Magnebot.

## Directions

- `move_by(x)` moves the Magnebot forward by x meters.
- `move_by(-x)` moves the Magnebot backward by x meters.
- `turn_by(x)` turns the Magnebot clockwise by x degrees.
- `turn_by(-x)` turns the Magnebot counterclockwise by x degrees.

## `arrived_at`, `aligned_at`, and `arrived_offset`

`move_by(distance)` has an optional parameter `arrived_at`. If the Magnebot is within this many meters of the target distance, the action is a success. Increasing the `arrived_at` distance will result in faster but less accurate movement:

```python
from time import time
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus

c = Controller()
magnebot = Magnebot()
c.add_ons.append(magnebot)
for arrived_at in [0.1, 0.3]:
    magnebot.reset()
    c.communicate([{"$type": "load_scene",
                    "scene_name": "ProcGenScene"},
                   TDWUtils.create_empty_room(12, 12)])
    t0 = time()
    magnebot.move_by(distance=2, arrived_at=arrived_at)
    while magnebot.action.status == ActionStatus.ongoing:
        c.communicate([])
    c.communicate([])
    print(time() - t0)
    print(magnebot.dynamic.transform.position)
c.communicate({"$type": "terminate"})
```

Output:

```
0.9917201995849609
[2.77684233e-03 1.12304435e-04 1.90657449e+00]
0.7530558109283447
[1.40244537e-03 1.94922194e-03 1.72238994e+00]
```

`turn_by(angle)` and `turn_to(target)` have an optional parameter `aligned_at`. If the Magnebot is within this many degrees of the target angle, the action is a success. Increasing the `aligned_at` distance will result in faster but less accurate movement:

```python
from time import time
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus

c = Controller()
magnebot = Magnebot()
c.add_ons.append(magnebot)
for aligned_at in [1, 3]:
    magnebot.reset()
    c.communicate([{"$type": "load_scene",
                    "scene_name": "ProcGenScene"},
                   TDWUtils.create_empty_room(12, 12)])
    t0 = time()
    magnebot.turn_by(angle=45, aligned_at=aligned_at)
    while magnebot.action.status == ActionStatus.ongoing:
        c.communicate([])
    c.communicate([])
    print(time() - t0)
c.communicate({"$type": "terminate"})
```

Output:

```
0.9169998168945312
0.567000150680542
```

`move_to(target)` is a combination of `turn_to(target, aligned_at)` and `move_by(distance, arrived_at)` and therefore has both an `aligned_at` parameter and an `arrived_at` parameter. It also has an `arrived_offset` parameter. After automatically calculating `distance` (i.e. the distance to `target`), the action will subtract `arrived_offset`. This is useful for approaching an object without colliding with it:

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus

class MoveToTest(Controller):
    def __init__(self, port: int = 1071, check_version: bool = True, launch_build: bool = True):
        super().__init__(port=port, check_version=check_version, launch_build=launch_build)
        self.object_id = self.get_unique_id()
        self.magnebot = Magnebot()
        self.add_ons.append(self.magnebot)

    def init_scene(self):
        self.magnebot.reset()
        commands = [{"$type": "load_scene",
                     "scene_name": "ProcGenScene"},
                    TDWUtils.create_empty_room(12, 12)]
        commands.extend(self.get_add_physics_object(model_name="rh10",
                                                    position={"x": 0.04, "y": 0, "z": 1.081},
                                                    object_id=self.object_id))
        self.communicate(commands)

    def run(self, arrived_offset: float) -> None:
        self.init_scene()
        self.magnebot.move_to(self.object_id, arrived_at=0.3, aligned_at=1, arrived_offset=arrived_offset)
        while self.magnebot.action.status == ActionStatus.ongoing:
            self.communicate([])
        self.communicate([])
        print(self.magnebot.action.status)

if __name__ == "__main__":
    c = MoveToTest()
    c.run(arrived_offset=0)
    c.run(arrived_offset=0.3)
    c.communicate({"$type": "terminate"})
```

Output:

```
ActionStatus.collision
ActionStatus.success
```

## Resetting the torso

By default, all wheel motion actions (`move_by`, `move_to`, `turn_by`, and `turn_to`) will reset the Magnebot's torso to its default position and the Magenbot's column to its default rotation before moving. In some cases, you might want to keep the Magnebot's  torso at its current position, in which case you can set `set_torso=False`. For example: `magnebot.move_by(distance=2, set_torso=False)`. The Magnebot's column always resets to its default rotation, regardless of the `set_torso` value.

## Tipping over

While moving or turning, the Magnebot might start to tip over. This  can happen if the Magnebot is holding a heavy object, or if its wheels roll over a ramp-like surface, etc. If this happens, the action will  immediately halt and set its status to `ActionStatus.tipping`.

You can correct for tipping by reversing the action. For example, if `move_by(1)` returned `ActionStatus.tipping` then it is likely that `move_by(-1)` will correct the angle.

In the unlikely event that the Magnebot completely falls over, you can reset its position and rotation with the `reset_position()` action. The build will consider this to be a very fast motion, so it's not recommended you call this action unless you have to.

## Collision detection

By default, the Magnebot will stop moving or turning if:

- Any of its joints, wheels, or magnets collides with any object or any other Magnebot.
- If the previous action resulted in a collision and this action is the same "type". For example, if `move_by(8)` returns `ActionStatus.collision`, then `move_by(1)` will immediately return `ActionStatus.collision`; the Magnebot won't actually move on this second action.

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus

c = Controller()
magnebot = Magnebot()
c.add_ons.append(magnebot)
c.communicate([{"$type": "load_scene",
                "scene_name": "ProcGenScene"},
               TDWUtils.create_empty_room(12, 12)])
magnebot.move_by(8)
while magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate([])
print(magnebot.action.status, magnebot.dynamic.transform.position)
magnebot.move_by(1)
while magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate([])
print(magnebot.action.status, magnebot.dynamic.transform.position)
c.communicate({"$type": "terminate"})
```

Output:

```
ActionStatus.collision [4.25562859e-02 1.51729584e-03 4.93132305e+00]
ActionStatus.collision [4.28201407e-02 2.10822141e-03 4.94139528e+00]
```

Collision detection is handled in `magnebot.collision_detection`, a [`CollisionDetection`](../../api/collision_detection.md) object. You can set the collision detection rules at the start of an action.

In this example, the Magnebot will collide with a wall. To ignore the wall collision while backing away, we'll set `magnebot.collision_detction.walls = False`.

```python
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus

c = Controller()
magnebot = Magnebot()
c.add_ons.append(magnebot)
c.communicate([{"$type": "load_scene",
                "scene_name": "ProcGenScene"},
               TDWUtils.create_empty_room(12, 12)])
magnebot.move_by(8)
while magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate([])
print(magnebot.action.status, magnebot.dynamic.transform.position)
magnebot.collision_detection.walls = False
magnebot.move_by(-2)
while magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate([])
print(magnebot.action.status, magnebot.dynamic.transform.position)
magnebot.collision_detection.walls = True
c.communicate({"$type": "terminate"})
```

Output:

```
ActionStatus.collision [4.25562859e-02 1.51729584e-03 4.93132305e+00]
ActionStatus.success [1.72240399e-02 1.54382165e-03 3.06301975e+00]
```

- If `collision_detection.walls == True`, the Magnebot will stop moving as soon as it collides with a wall.
- If `collision_detection.floor == True`, the Magnebot will stop moving as soon as it collides with the floor. *This should almost always be False!*
- If `collision_detection.objects == True`, the Magnebot will stop moving as soon as it collides with any object.
- `collision_detection.exclude_objects` is a list of object IDs. If `collision_detection.objects == True` the Magnebot will continue to try to move if it collides with any objects in `exclude_objects`.
- `collision_detection.include_objects` is a list of object IDs.  If `collision_detection.objects == False` the Magnebot will stop moving if it collides with any objects in `include_objects`. 

**DO NOT set `collision_detection` such that the Magnebot can repeatedly collide with obstacles.** If the Magnebot repeatedly collides with an object, it can cause the build to crash. This is a bug in the underlying Unity physics engine. In real life, such behavior would snap off a wheel, an arm joint, or otherwise break the robot. Do NOT repeatedly send the Magnebot in impossible directions.

***

**Next: [Arm articulation](arm_articulation.md)**

[Return to the README](../../../README.md)

***

Examples controllers:

- [collision_detection.py](https://github.com/alters-mit/magnebot/blob/main/controllers/examples/magnebot/collision_detection.py) Show the difference between arrived_offset values and collision detection settings.
