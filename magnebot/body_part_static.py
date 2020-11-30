import numpy as np
from tdw.output_data import StaticRobot


class BodyPartStatic:
    """
    Static data for a body part of the Magnebot.

    ***

    ## Fields

    - `id` The unique ID of the body part object.
    - `mass` The mass of the body part.
    - `segmentation_color` The segmentation color of the object as a numpy array: `[r, g, b]`
    - `name` The name of the body part object.

    ***

    ## Functions

    """

    def __init__(self, sr: StaticRobot, index: int):
        self.id = sr.get_joint_id(index)
        self.mass = sr.get_joint_mass(index)
        self.segmentation_color = np.array(sr.get_joint_segmentation_color(index))
        self.name = sr.get_joint_name(index)
