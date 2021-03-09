from time import sleep
from magnebot import TestController, Arm

# X [0, 1, 0]
# Y [0, 1, 0]
# Z [1, 0, 0]
# Z [0, 1, 0]
# Z [0, 0, 1]
class IkOrientation(TestController):
    def test(self):
        self.init_scene()
        for orientation_mode in "XYZ":
            for orientation in [[1, 0, 0], [0, 1, 0], [0, 0, 1]]:
                print(orientation_mode, orientation)
                self._start_action()
                self._start_ik(target={"x": 0.2, "y": 0.5, "z": 0.5}, arm=Arm.left, orientation_mode=orientation_mode,
                               target_orientation=orientation)
                self._do_arm_motion()
                sleep(1)
                self._end_action()
                self.reset_arm(arm=Arm.left)


if __name__ == "__main__":
    m = IkOrientation(skip_frames=0)
    m.test()
    m.end()
