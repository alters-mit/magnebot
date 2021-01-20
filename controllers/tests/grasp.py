from typing import Dict, List
from magnebot import Arm, ActionStatus
from magnebot.test_controller import TestController


class Grasp(TestController):
    """
    Test the grasp() function.
    """

    def __init__(self, port: int = 1071):
        super().__init__(port=port)
        self.target_id: int = -1

    def _get_scene_init_commands(self, magnebot_position: Dict[str, float] = None) -> List[dict]:
        self.target_id = self._add_object(model_name="blue_satchal",
                                          position={"x": 0.1024729, "y": 0, "z": 0.6279346},
                                          rotation={"x": -7.730941e+11, "y": 152.176, "z": 4.398})
        commands = super()._get_scene_init_commands(magnebot_position=magnebot_position)
        return commands


if __name__ == "__main__":
    m = Grasp()
    m.init_scene()
    m.turn_by(160)
    m.turn_by(120)
    status = m.grasp(m.target_id, arm=Arm.right)
    assert status == ActionStatus.success, status
    m.end()
