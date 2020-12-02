from tdw.output_data import StaticRobot
from magnebot import Magnebot, Arm
from magnebot.action_status import ActionStatus
from magnebot.util import get_data


class Symmetry(Magnebot):
    """
    Test the symmetry of the Magnebot's parts before and after moving.
    """

    def __init__(self, port: int = 1071, launch_build: bool = True):
        super().__init__(port=port, launch_build=launch_build, id_pass=False, debug=True)
        self.left = {"shoulder_left": -1,
                     "upper_arm_left": -1,
                     "elbow_left": -1,
                     "wrist_left": -1,
                     "magnet_left": -1,
                     "wheel_left_front": -1,
                     "wheel_left_back": -1}
        self.right = {"shoulder_right": -1,
                      "upper_arm_right": -1,
                      "elbow_right": -1,
                      "wrist_right": -1,
                      "magnet_right": -1,
                      "wheel_right_front": -1,
                      "wheel_right_back": -1}
        self.center = {"base": -1,
                       "column": -1,
                       "torso": -1}
        self.front = {"axle_front": -1}
        self.back = {"axle_back": -1}

    def init_test_scene(self) -> None:
        super().init_test_scene()
        # Get the object IDs for all non-joints as well as joints.
        resp = self.communicate({"$type": "send_static_robots"})
        sr = StaticRobot(get_data(resp=resp, d_type=StaticRobot))
        for i in range(sr.get_num_joints()):
            j_name = sr.get_joint_name(i)
            j_id = sr.get_joint_id(i)
            for d in [self.left, self.right, self.center, self.front, self.back]:
                if j_name in d:
                    d[j_name] = j_id
        for i in range(sr.get_num_non_moving()):
            j_name = sr.get_non_moving_name(i)
            j_id = sr.get_non_moving_id(i)
            for d in [self.left, self.right, self.center, self.front, self.back]:
                if j_name in d:
                    d[j_name] = j_id

        self.assert_symmetry()

    def assert_symmetry(self) -> None:
        """
        Check whether each pair of body parts has symmetry over the expected axis.
        """

        # Assert left-right symmetry.
        for left_name, right_name in zip(self.left.keys(), self.right.keys()):
            left_pos = self.state.joint_transforms[self.left[left_name]].position
            right_pos = self.state.joint_transforms[self.right[right_name]].position
            # Assert that the (y, z) values are the same.
            for i, c in zip([1, 2], ["y", "z"]):
                assert left_pos[i] == right_pos[i], f"{c} coordinate of joints isn't the same: " \
                                                    f"{left_name} = {left_pos}, {right_name} = {right_pos}"
            # Assert that the x values are mirrored.
            assert left_pos[0] == -right_pos[0], f"x coordinate of joints isn't mirrored: " \
                                                 f"{left_name} = {left_pos}, {right_name} = {right_pos}"
        # Assert centrality.
        for name in self.center:
            pos = self.state.joint_transforms[self.center[name]].position
            for i, c in zip([0, 2], ["x", "z"]):
                assert pos[i] == 0, f"{c} coordinate of {name} isn't 0: {pos}"

        # Assert front-back symmetry.
        for front_name, back_name in zip(self.front.keys(), self.back.keys()):
            front_pos = self.state.joint_transforms[self.front[front_name]].position
            back_pos = self.state.joint_transforms[self.back[back_name]].position
            # Assert that the (x, y) values are the same.
            for i, c in zip([0, 1], ["x", "y"]):
                assert front_pos[i] == back_pos[i], f"{c} coordinate of joints isn't the same: " \
                                                    f"{front_name} = {front_pos}, {back_name} = {back_pos}"
            # Assert that the z values are mirrored.
            assert front_pos[2] == -back_pos[2], f"z coordinate of joints isn't mirrored: " \
                                                 f"{front_name} = {front_pos}, {back_name} = {back_pos}"


if __name__ == "__main__":
    m = Symmetry(launch_build=False)
    m.init_test_scene()
    # Bend both arms to mirrored targets.
    for direction, arm in zip([1, -1], [Arm.left, Arm.right]):
        status = m.reach_for(target={"x": 0.2 * direction, "y": 0.4, "z": 0.3}, arm=arm)
        assert status == ActionStatus.success, f"{arm}, {status}"
    m.assert_symmetry()
    # Reset the arms and assert symmetry.
    m.reset_arms()
    m.assert_symmetry()
