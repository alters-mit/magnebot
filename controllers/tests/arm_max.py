import numpy as np
from magnebot import TestController, Arm, ArmJoint


class ArmMax(TestController):
    """
    Get an estimate of the maximum extent of the Magnebot's arm.
    """

    def get_max_arm_extent(self) -> float:
        """
        Extend the arm and incrementally rotate the column.

        :return: An estimate of the maximum distance from the magnet to the origin.
        """

        self._debug = False
        self._start_action()
        shoulder = self.magnebot_static.arm_joints[ArmJoint.shoulder_right]
        elbow = self.magnebot_static.arm_joints[ArmJoint.elbow_right]
        origin = np.array([0, 0, 0])
        self._next_frame_commands.extend([{"$type": "set_immovable",
                                           "immovable": True},
                                          {"$type": "set_spherical_target",
                                           "target": {"x": -90, "y": 90, "z": 0},
                                           "joint_id": shoulder},
                                          {"$type": "set_revolute_target",
                                           "target": 0,
                                           "joint_id": elbow}])
        self._do_arm_motion(joint_ids=[shoulder, elbow])
        self._end_action()
        magnet_position = self.state.joint_positions[self.magnebot_static.magnets[Arm.right]]
        magnet_position[1] = 0
        # How far the arm extends, given the torso rotation.
        return np.linalg.norm(origin - magnet_position)


if __name__ == "__main__":
    m = ArmMax()
    m.init_scene()
    print(m.get_max_arm_extent())
    m.end()
