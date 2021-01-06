# DemoController

`from magnebot.demo_controller import DemoController`

`DemoController` is used to generate demo videos of the Magnebot API. It is a superclass of [`Magnebot`](magnebot_controller.md) that adds the following functionality:

- Instead of saving images at the end of every action, they are saved every frame.
- The roof is removed from the scene.
- There is a `navigate()` action.

Most users shouldn't use this controller for the following reasons:

- Saving every image per frame is _very_ slow.
- `navigate()` isn't sufficiently reliable (see notes below).

***

#### \_\_init\_\_

**`DemoController()`**

See: [`Magnebot.add_camera()`](magnebot_controller.md#add_camera).

Adds some instructions to render images per-frame.

#### add_camera

**`self.add_camera()`**

See: [`Magnebot.add_camera()`](magnebot_controller.md#add_camera).

Adds some instructions to render images per-frame.

#### communicate

**`self.communicate()`**

See [`Magnebot.communicate()`](magnebot_controller.md#communicate).

Images are saved per-frame.

