# TestController

`from magnebot import TestController`

This controller will load an empty test room instead of a highly detailed scene.

This can be useful for testing the Magnebot.

***

#### \_\_init\_\_

**`TestController()`**

**Always call this function before any other API calls.** Initialize an empty test room with a Magnebot.

You can safely call `init_scene()` more than once to reset the simulation.

```python
from magnebot import TestController

m = TestController()
m.init_scene()

# Your code here.
```

Possible [return values](action_status.md):

- `success`

#### init_scene

**`self.init_scene()`**

**Always call this function before any other API calls.** Initialize an empty test room with a Magnebot.

You can safely call `init_scene()` more than once to reset the simulation.

```python
from magnebot import TestController

m = TestController()
m.init_scene()

# Your code here.
```

Possible [return values](action_status.md):

- `success`

