import numpy as np


class JointAngles:
    """
    The angles and targets of a Magnebot joint.
    This is useful mainly for the backend code when tracking whether joints have stopped moving.

    ***

    ## Fields

    - `angles` The current angles of a joint in degrees as a numpy array.. If this is a revolute or prismatic joint, this has 1 element. If this is a spherical joint, this has 3 elements: `[x, y, z]`.
    - `targets` The current target angles of a joint in degrees as a numpy array.. If this is a revolute or prismatic joint, this has 1 element. If this is a spherical joint, this has 3 elements: `[x, y, z]`.

    ***

    ## Functions

    """

    def __init__(self, angles: np.array, targets: np.array):
        self.angles = angles
        self.targets = targets
