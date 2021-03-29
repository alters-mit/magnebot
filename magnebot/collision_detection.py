from typing import List


class CollisionDetection:
    """
    Parameters for how a Magnebot handles collision detection.
    """

    def __init__(self, walls: bool = True, floor: bool = False, objects: bool = True, mass: float = 8,
                 include_objects: List[int] = None, exclude_objects: List[int] = None,
                 exclude_joints: List[int] = None, previous_was_same: bool = True):
        """
        :param walls: If True, the Magnebot will stop when it collides with a wall.
        :param floor: If True, the Magnebot will stop when it collides with the floor.
        :param objects: If True, the Magnebot will stop when it collides with an object with a mass greater than the `mass` value that is either listed in `include_objects` or not listed in `exclude_objects`.
        :param mass: If `objects == True`, the Magnebot will only stop if it collides with an object with mass greater than or equal to this value.
        :param include_objects: If `objects == True`, the Magnebot will stop if it collides with any object in this list, regardless of mass. Can be None.
        :param exclude_objects: If `objects == True`, the Magnebot will ignore a collision with any object in this list, regardless of mass. Can be None.
        :param exclude_joints: The Magnebot will ignore any collisions that occur between and object or wall and joints in this list. Can be None.
        :param previous_was_same: If True, the Magnebot will stop if the previous action resulted in a collision and was the [same sort of action as the current one](collision_action.md).
        """

        """:field
        If True, the Magnebot will stop when it collides with a wall.
        """
        self.walls: bool = walls
        """:field
        If True, the Magnebot will stop when it collides with the floor.
        """
        self.floor: bool = floor
        """:field
        If True, the Magnebot will stop when it collides collides with an object with a mass greater than the `mass` value that is either listed in `include_objects` or not listed in `exclude_objects`.
        """
        self.objects: bool = objects
        """:field
        If `objects == True`, the Magnebot will only stop if it collides with an object with mass greater than or equal to this value.
        """
        self.mass: float = mass
        if include_objects is None:
            """:field
            If `objects == True`, the Magnebot will stop if it collides with any object in this list, regardless of mass. Can be None.
            """
            self.include_objects: List[int] = list()
        else:
            self.include_objects: List[int] = include_objects
        if exclude_objects is None:
            """:field
            If `objects == True`, the Magnebot will ignore a collision with any object in this list, regardless of mass. Can be None.
            """
            self.exclude_objects: List[int] = list()
        else:
            self.exclude_objects: List[int] = exclude_objects
        if exclude_joints is None:
            """:field
            The Magnebot will ignore any collisions that occur between and object or wall and joints in this list. Can be None.
            """
            self.exclude_joints: List[int] = list()
        else:
            self.exclude_joints: List[int] = exclude_joints
        """:field
        If True, the Magnebot will stop if the previous action resulted in a collision and was the [same sort of action as the current one](collision_action.md).
        """
        self.previous_was_same: bool = previous_was_same
