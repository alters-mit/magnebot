# TestController

`from magnebot import TestController`

This controller will load an empty test room instead of a highly detailed scene.

This can be useful for testing the Magnebot.

***

#### \_\_init\_\_

**`TestController()`**

Initialize an empty test room with a Magnebot. The simulation will advance through frames until the Magnebot's body is in its neutral position.

This function must be called before any other API calls.

```python
from magnebot import TestController

m = TestController()
m.init_scene()

# Your code here.
```

You can safely call `init_scene()` more than once to reset the simulation.

Possible [return values](action_status.md):

- `success`

#### init_scene

**`self.init_scene()`**

Initialize an empty test room with a Magnebot. The simulation will advance through frames until the Magnebot's body is in its neutral position.

This function must be called before any other API calls.

```python
from magnebot import TestController

m = TestController()
m.init_scene()

# Your code here.
```

You can safely call `init_scene()` more than once to reset the simulation.

Possible [return values](action_status.md):

- `success`

