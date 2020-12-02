class IntPair:
    """
    A pair of unordered integers.
    """

    def __init__(self, int1: int, int2: int):
        """
        :param int1: The first integer.
        :param int2: The second integer.
        """

        self.int1 = int1
        self.int2 = int2

    def __eq__(self, other):
        if not isinstance(other, IntPair):
            return False
        return (other.int1 == self.int1 and other.int2 == self.int2) or\
               (other.int1 == self.int2 and other.int2 == self.int1)

    def __hash__(self):
        if self.int1 > self.int2:
            return hash((self.int1, self.int2))
        else:
            return hash((self.int2, self.int1))
