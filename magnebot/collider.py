from enum import Enum


class Collider(Enum):
    """
    The type of collider in a collision.
    """

    obj = 1  # An object in the scene, such as a table, box, cup, etc.
    bot = 2  # Any part of the Magnebot, such as its base, joints, wheels, etc.
    env = 4  # The scene environment, such as a wall.
