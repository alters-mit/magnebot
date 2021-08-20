# The radius of the Magnebot as defined by its longer axis.
MAGNEBOT_RADIUS: float = 0.22
# The cell size on the occupancy map. This is slightly bigger than diameter of the Magnebot.
OCCUPANCY_CELL_SIZE: float = (MAGNEBOT_RADIUS * 2) + 0.05
# The required version of TDW.
TDW_VERSION: str = "1.8.24"
# The y value of the column's position assuming a level floor and angle.
COLUMN_Y: float = 0.159
# The minimum y value of the torso, offset from the column (see `COLUMN_Y`).
TORSO_MIN_Y: float = 0.2244872
# The maximum y value of the torso, offset from the column (see `COLUMN_Y`).
TORSO_MAX_Y: float = 1.07721
