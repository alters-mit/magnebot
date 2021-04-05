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
# The path to the dictionary of which sides per object are convex.
CONVEX_SIDES_PATH = OBJECT_DATA_DIRECTORY.joinpath("convex.json")
# The path to the scene data.
SCENE_DATA_DIRECTORY = DATA_DIRECTORY.joinpath("scenes")
# The path to the dictionary of where the robot can spawn.
SPAWN_POSITIONS_PATH = SCENE_DATA_DIRECTORY.joinpath("spawn_positions.json")
# The directory for occupancy maps.
OCCUPANCY_MAPS_DIRECTORY = SCENE_DATA_DIRECTORY.joinpath("occupancy_maps")
# The directory for room maps.
ROOM_MAPS_DIRECTORY = SCENE_DATA_DIRECTORY.joinpath("room_maps")
# The directory of Magnebot data.
MAGNEBOT_DIRECTORY = DATA_DIRECTORY.joinpath("magnebot")
# The path to the turn constants data.
TURN_CONSTANTS_PATH = MAGNEBOT_DIRECTORY.joinpath("turn_constants.csv")
# The directory for IK orientation data.
IK_DIRECTORY = MAGNEBOT_DIRECTORY.joinpath("ik")
# The path to the IK target positions.
IK_POSITIONS_PATH = IK_DIRECTORY.joinpath("positions.npy")
# The path to the IK orientations data for the left arm.
IK_ORIENTATIONS_LEFT_PATH = IK_DIRECTORY.joinpath("orientations_left.npy")
# The path to the IK orientations data for the right arm.
IK_ORIENTATIONS_RIGHT_PATH = IK_DIRECTORY.joinpath("orientations_right.npy")
