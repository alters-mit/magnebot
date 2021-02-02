# TurnConstants

`from magnebot.turn_constants import TurnConstants`

Constants use for `turn_by()` and `turn_to()` depending on the angle.

There's probably a much better (more mathematically accurate) way to do this!
If you know the correct constants, please email us or raise a GitHub issue.

***

## Fields

- `angle` The angle of the turn.

- `magic_number` Multiply the spin of the wheels by this.

- `outer_track` Multiply the outer track wheel spin by this.

- `front` Multiply the front wheel spin by this.

***

## Functions

#### \_\_init\_\_

**`TurnConstants(angle, magic_number, outer_track, front)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| angle |  int |  | The angle of the turn. |
| magic_number |  float |  | Multiply the spin of the wheels by this. |
| outer_track |  float |  | Multiply the outer track wheel spin by this. |
| front |  float |  | Multiply the front wheel spin by this. |

