from typing import List, Optional, Dict
import numpy as np
from tdw.output_data import Robot, Transforms
from magnebot.transform import Transform, PhysicsTransform
from magnebot.util import get_data


class SceneState:
    def __init__(self, resp: List[bytes]):
        r = get_data(resp=resp, d_type=Robot)
        self.robot_body_parts: Dict[int, PhysicsTransform] = dict()
        # Get data for the robot body parts.
        for i in range(r.get_num_body_parts()):
            self.robot_body_parts[r.get_body_part_id(i)] = PhysicsTransform(
                position=np.array(r.get_body_part_position(i)),
                rotation=np.array(r.get_body_part_rotation(i)),
                forward=np.array(r.get_body_part_forward(i)),
                velocity=np.array(r.get_body_part_velocity(i)),
                angular_velocity=np.array(r.get_body_part_angular_velocity(i)))
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
