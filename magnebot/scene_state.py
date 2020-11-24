from typing import List, Dict
import numpy as np
from tdw.output_data import Robot, Transforms
from magnebot.transform import Transform, JointState
from magnebot.util import get_data


class SceneState:
    def __init__(self, resp: List[bytes]):
        r = get_data(resp=resp, d_type=Robot)
        self.robot_joints: Dict[int, JointState] = dict()
        # Get data for the robot body parts.
        for i in range(r.get_num_joints()):
            self.robot_joints[r.get_joint_id(i)] = JointState(
                position=np.array(r.get_joint_position(i)),
                rotation=np.array(r.get_joint_rotation(i)),
                forward=np.array(r.get_joint_forward(i)),
                targets=r.get_joint_targets(i),
                angles=r.get_joint_positions(i))
        # Get data for the robot.
        self.robot: Transform = Transform(position=np.array(r.get_position()),
                                          rotation=np.array(r.get_rotation()),
                                          forward=np.array(r.get_forward()))

        # Get object data.
        transforms = get_data(resp=resp, d_type=Transforms)
        self.objects: Dict[int, Transform] = dict()
        for i in range(transforms.get_num()):
            self.objects[i] = Transform(position=np.array(transforms.get_position(i)),
                                        forward=np.array(transforms.get_forward(i)),
                                        rotation=np.array(transforms.get_rotation(i)))
