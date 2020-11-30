import numpy as np
from tdw.output_data import StaticRobot


class BodyPartStatic:
    """
    Static data for a body part of the Magnebot.
    """

    def __init__(self, sr: StaticRobot, index: int):
        """
        :param sr: The static robot output data.
        :param index: The index of this body part in `sr`.
        """

        """:field
        The unique ID of the body part object.
        """
        self.id = sr.get_joint_id(index)

        """:field
        The mass of the body part.
        """
        self.mass = sr.get_joint_mass(index)

        """:field
        The segmentation color of the object as a numpy array: `[r, g, b]`
        """
        self.segmentation_color = np.array(sr.get_joint_segmentation_color(index))

        """:field
        The name of the body part object.
        """
        self.name = sr.get_joint_name(index)
