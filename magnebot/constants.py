import numpy as np


# The radius of the Magnebot as defined by its longer axis.
MAGNEBOT_RADIUS: float = 0.22
# The cell size on the occupancy map. This is slightly bigger than diameter of the Magnebot.
OCCUPANCY_CELL_SIZE: float = (MAGNEBOT_RADIUS * 2) + 0.05
# The y value of the column's position assuming a level floor and angle.
COLUMN_Y: float = 0.159
# The minimum y value of the torso, offset from the column (see `COLUMN_Y`).
TORSO_MIN_Y: float = 0.2244872
# The maximum y value of the torso, offset from the column (see `COLUMN_Y`).
TORSO_MAX_Y: float = 1.07721
# The default torso position.
DEFAULT_TORSO_Y: float = 0.737074
# The default wheel friction coefficient.
DEFAULT_WHEEL_FRICTION: float = 0.05
# The circumference of the Magnebot.
MAGNEBOT_CIRCUMFERENCE: float = np.pi * 2 * MAGNEBOT_RADIUS
# The radius of the Magnebot wheel.
WHEEL_RADIUS: float = 0.1
# The circumference of the Magnebot wheel.
WHEEL_CIRCUMFERENCE: float = 2 * np.pi * WHEEL_RADIUS
# The wheel friction coefficient when braking during a move action.
BRAKE_FRICTION: float = 0.95
# The required TDW version.
TDW_VERSION: str = "1.9.0"
