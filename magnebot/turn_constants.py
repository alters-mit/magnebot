class TurnConstants:
    """
    Constants use for `turn_by()` and `turn_to()` depending on the angle.

    There's probably a much better (more mathematically accurate) way to do this!
    If you know the correct constants, please email us or raise a GitHub issue.
    """

    def __init__(self, angle: int, magic_number: float, outer_track: float, front: float):
        """
        :param angle: The angle of the turn.
        :param magic_number: Multiply the spin of the wheels by this.
        :param outer_track: Multiply the outer track wheel spin by this.
        :param front: Multiply the front wheel spin by this.
        """

        """:field
        The angle of the turn.
        """
        self.angle: int = angle
        """:field
        Multiply the spin of the wheels by this.
        """
        self.magic_number: float = magic_number
        """:field
        Multiply the outer track wheel spin by this.
        """
        self.outer_track: float = outer_track
        """:field
        Multiply the front wheel spin by this.
        """
        self.front: float = front
