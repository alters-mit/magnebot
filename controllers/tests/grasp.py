from magnebot import Arm, ActionStatus, Magnebot
from magnebot.ik.orientation_mode import OrientationMode
from magnebot.ik.target_orientation import TargetOrientation


class Grasp(Magnebot):
    """
    Test the grasp() function.
    """

    def __init__(self, port: int = 1071):
        super().__init__(port=port)
        self.target_id: int = -1

    def init_scene(self) -> ActionStatus:
        self.target_id = self._add_object(model_name="blue_satchal",
                                          position={"x": -0.1024729, "y": 0, "z": -0.6279346},
                                          rotation={"x": -7.730941e+11, "y": 152.176, "z": 4.398})
        return super().init_scene()


if __name__ == "__main__":
    m = Grasp()
    m.init_scene()
    m.turn_to(m.target_id)
    status = m.grasp(m.target_id, arm=Arm.right,
                     target_orientation=TargetOrientation.up, orientation_mode=OrientationMode.y)
    assert status == ActionStatus.success, status
    m.end()
