from typing import Dict
import numpy as np
from tdw.output_data import StaticRobot
from magnebot.drive import Drive


class JointStatic:
    """
    Static data for a joint of the Magnebot.
    """

    def __init__(self, sr: StaticRobot, index: int):
        """
        :param sr: The static robot output data.
        :param index: The index of this body part in `sr`.
        """

        """:field
        The unique ID of the body part object.
        """
        self.id: int = sr.get_joint_id(index)

        """:field
        The mass of the body part.
        """
        self.mass: float = sr.get_joint_mass(index)

        """:field
        The segmentation color of the object as a numpy array: `[r, g, b]`
        """
        self.segmentation_color: np.array = np.array(sr.get_joint_segmentation_color(index))

        """:field
        The name of the body part object.
        """
        self.name: str = sr.get_joint_name(index)

        """:field
        Static data for the joint's drives. Key = axis. Value = [drive data](drive.md).
        """
        self.drives: Dict[str, Drive] = dict()
        for j in range(sr.get_num_joint_drives(index)):
            axis = sr.get_joint_drive_axis(index, j)
            self.drives[axis] = Drive(sr=sr, joint_index=index, drive_index=j)
        """:field
        The type of joint. Optionals: `"revolute"`, `"spherical"`, `"prismatic"`, and `"fixed_joint"`.
        """
        self.joint_type: str = sr.get_joint_type(index)
