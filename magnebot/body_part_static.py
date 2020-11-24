import numpy as np
from tdw.output_data import StaticRobot


class BodyPartStatic:
    def __init__(self, sr: StaticRobot, index: int):
        self.id = sr.get_joint_id(index)
        self.mass = sr.get_joint_mass(index)
        self.segmentation_color = np.array(sr.get_joint_segmentation_color(index))
        self.name = sr.get_joint_name(index)
