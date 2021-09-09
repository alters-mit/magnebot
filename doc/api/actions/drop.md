# Drop

`from magnebot.drop import Drop`

Drop an object held by a magnet.

***

#### \_\_init\_\_

**`Drop(target, arm, wait_for_object, dynamic)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  int |  | The ID of the object currently held by the magnet. |
| arm |  Arm |  | [The arm used for this action.](../arm.md) |
| wait_for_object |  bool |  | If True, the action will continue until the object has finished falling. If False, the action advances the simulation by exactly 1 frame. |
| dynamic |  MagnebotDynamic |  | [The dynamic Magnebot data.](../magnebot_dynamic.md) |

#### get_initialization_commands

**`self.get_initialization_commands(resp)`**

Update the object's position and check if it's still moving.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| resp |  List[bytes] |  | The response from the build. |

_Returns:_  True if the object is moving.

#### set_status_after_initialization

**`self.set_status_after_initialization(resp)`**

Update the object's position and check if it's still moving.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| resp |  |  | The response from the build. |

_Returns:_  True if the object is moving.

#### get_ongoing_commands

**`self.get_ongoing_commands(resp)`**

Update the object's position and check if it's still moving.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| resp |  List[bytes] |  | The response from the build. |

_Returns:_  True if the object is moving.

