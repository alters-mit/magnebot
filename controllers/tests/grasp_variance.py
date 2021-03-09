from typing import Dict, List
from magnebot import TestController, Arm, ActionStatus


class Grasp(TestController):
    def __init__(self, port: int = 1071):
        super().__init__(port=port)
        self.object_id: int = -1

    def _get_scene_init_commands(self, magnebot_position: Dict[str, float] = None) -> List[dict]:
        self.object_id = self._add_object(model_name="square_wood_block",
                                          position={"x": 0.5, "y": 0.3, "z": 0.5},
                                          scale={"x": 3, "y": 3, "z": 6},
                                          mass=0.025)
        return super()._get_scene_init_commands(magnebot_position=magnebot_position)


if __name__ == "__main__":
    m = Grasp()
    for i in range(20):
        m.init_scene()
        m.reset_arm(Arm.right)
        m.move_to({'x': -0.005169665860227268, 'y': 0.0, 'z': -1.2665641808348211, 'arrived_at': 0.3})
        m.move_to({'x': 0.7047376874523255, 'y': 0.0, 'z': -0.9665679106526723, 'arrived_at': 0.3})
        m.move_to({'x': 0.5639010268187523, 'y': 0.0, 'z': -0.14685142489209524, 'arrived_at': 0.3})
        status = m.grasp(m.object_id, Arm.right)
        assert status == ActionStatus.success
