from typing import Dict, List
from tdw.tdw_utils import TDWUtils
from magnebot import Arm, ActionStatus
from magnebot.test_controller import TestController


class Grasp(TestController):
    """
    Test the grasp() function.
    """

    def __init__(self, port: int = 1071):
        super().__init__(port=port)
        self.target_id: int = -1
        self.pos = {"x": -0.1024729, "y": 0, "z": -0.6279346}

    def _get_scene_init_commands(self, magnebot_position: Dict[str, float] = None) -> List[dict]:
        self.target_id = self._add_object(model_name="blue_satchal",
                                          position=self.pos,
                                          rotation={"x": -7.730941e+11, "y": 152.176, "z": 4.398})
        commands = super()._get_scene_init_commands(magnebot_position=magnebot_position)
        return commands

    def show_relative(self) -> None:
        self._start_action()
        p = self._absolute_to_relative(position=self.pos, state=self.state)
        self._next_frame_commands.append({"$type": "add_position_marker",
                                          "position": TDWUtils.array_to_vector3(p),
                                          "color": {"r": 0, "g": 0, "b": 1, "a": 1}})
        self._end_action()


if __name__ == "__main__":
    m = Grasp()
    m.init_scene()
    m.turn_by(-177)
    m.show_relative()
    status = m.grasp(m.target_id, arm=Arm.right)
    assert status == ActionStatus.success, status
    m.end()
