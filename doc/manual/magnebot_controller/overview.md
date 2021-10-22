##### MagnebotController

# Overview

The [`MagnebotController`](../../api/magnebot_controller.md) offers a simplified API for single-agent simulations. Actions are non-interruptible; `self.move_by(2)` will simulate motion until the action ends (i.e. when the Magnebot has moved forward by 2 meters). 

```python
from magnebot import MagnebotController

c = MagnebotController() # On a server, change this to MagnebotController(launch_build=False)

c.init_scene()
c.move_by(2)
print(c.magnebot.dynamic.transform.position)
c.end()
```

The `MagnebotController` offers a higher-level API than the `Magnebot` agent with some built-in speed optimizations. We recommend using `MagnebotController` for most single-agent simulations.

***

**Next: [Scene setup](scene_setup.md)**

[Return to the README](../../../README.md)

***

Example controllers:

- [move_by.py](https://github.com/alters-mit/magnebot/blob/main/controllers/examples/magnebot_controller/move_by.py) Move the Magnebot forward by 2 meters.

