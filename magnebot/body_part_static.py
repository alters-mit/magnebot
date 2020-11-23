import numpy as np
from tdw.output_data import StaticRobot


class BodyPartStatic:
    def __init__(self, sr: StaticRobot, index: int):
        self.id = sr.get_body_part_id(index)
        self.mass = sr.get_body_part_mass(index)
        self.segmentation_color = np.array(sr.get_body_part_segmentation_color(index))
        self.name = sr.get_body_part_name(index)
