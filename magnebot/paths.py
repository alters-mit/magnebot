from pathlib import Path
from pkg_resources import resource_filename

"""
Paths to data files in this Python module.
"""

# The path to the data files.
DATA_DIRECTORY = Path(resource_filename(__name__, "data"))
# The path to object data.
OBJECT_DATA_DIRECTORY = DATA_DIRECTORY.joinpath("objects")
# The path to object categories dictionary.
OBJECT_CATEGORIES_PATH = OBJECT_DATA_DIRECTORY.joinpath("categories.json")
# Data for the Magnebot column's y values.
COLUMN_Y = OBJECT_DATA_DIRECTORY.joinpath("column_y.csv")
# The path to the scene data.
SCENE_DATA_DIRECTORY = DATA_DIRECTORY.joinpath("scenes")
# The path to the dictionary of where the robot can spawn.
SPAWN_POSITIONS_PATH = SCENE_DATA_DIRECTORY.joinpath("spawn_positions.json")
