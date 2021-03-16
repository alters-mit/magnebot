from typing import Dict, List
from magnebot import TestController, Arm, ActionStatus


class GraspSmall(TestController):
    """
    Try to grasp small objects.
    """

    def __init__(self, port: int = 1071):
        super().__init__(port=port, skip_frames=0)
        self.object_ids: List[int] = list()

    def _get_scene_init_commands(self, magnebot_position: Dict[str, float] = None) -> List[dict]:
        self.object_ids.append(self._add_object(model_name="square_wood_block",
                                                position={"x": 0.379, "y": 0, "z": 0.662}))
        self.object_ids.append(self._add_object(model_name="square_wood_block",
                                                position={"x": -0.635, "y": 0, "z": 0.662}))
        self.object_ids.append(self._add_object(model_name="square_wood_block",
                                                position={"x": 0.379, "y": 0, "z": -0.569}))
        return super()._get_scene_init_commands(magnebot_position=magnebot_position)


if __name__ == "__main__":
    m = GraspSmall()
    m.init_scene()
    for object_id in m.object_ids:
        status = m.grasp(object_id, Arm.right)
        assert status == ActionStatus.success, status
        m.drop(object_id, Arm.right)
        m.reset_arm(arm=Arm.right)
    m.end()
