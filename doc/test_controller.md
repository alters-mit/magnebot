# TestController

`from magnebot import TestController`

This controller will load an empty test room instead of a highly detailed scene.

This can be useful for testing the Magnebot.

***

#### init_scene

**`def init_scene(self, scene: str = None, layout: int = None, room: int = -1) -> ActionStatus`**

Initialize an empty test room with a Magnebot. The simulation will advance through frames until the Magnebot's body is in its neutral position.

This function must be called before any other API calls.

```python
from magnebot import Magnebot

m = Magnebot()
m.init_scene()

# Your code here.
```

You can safely call `init_scene()` more than once to reset the simulation.

Possible [return values](action_status.md):

- `success`
- `failed_to_bend` (Technically this is _possible_, but it shouldn't ever happen.)

