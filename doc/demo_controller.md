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

#### navigate

**`self.navigate(target)`**

Navigate to the target position by following a path of waypoints.

The path is generated using Unity's NavMesh. Then, each corner of the path is snapped to the occupancy map. Then, the Magnebot goes to each position using a `move_to()` action.

This isn't in the main `Magnebot` API because it's actually quite naive and won't work in many cases! For example:

- It doesn't account for objects moving in the scene after scene initialization.
- The waypoints are always centerpoints of occupancy map positions.
- Because waypoints are rather naively snapped to occupancy map positions, it is possible for this action to report that there is no path when there actually is one.

But for the purposes of generating a demo of the Magnebot API, this action is good enough!

Possible [return values](action_status.md):

- `success`
- `failed_to_move`
- `failed_to_turn`
- `no_path`


| Parameter | Type | Description |
| --- | --- | --- |
| target |  Dict[str, float] | The target destination. |

_Returns:_  An `ActionStatus` indicating if the Magnebot arrived at the destination and if not, why.

