from typing import Dict, List
from magnebot import TestController, ActionStatus


class Tip(TestController):
    """
    Test collision detection, to prevent the Magnebot from tipping over.
    """

    def _get_scene_init_commands(self, magnebot_position: Dict[str, float]) -> List[dict]:
        self._add_object(model_name="fridge_large", position={"x": 0, "y": 0, "z": -2})
        return super()._get_scene_init_commands(magnebot_position=magnebot_position)


if __name__ == "__main__":
    m = Tip()
    m.init_scene()
    status = m.move_by(12)
    assert status == ActionStatus.collision, status
    status = m.move_by(-1)
    assert status == ActionStatus.success, status
    status = m.move_by(-12)
    assert status == ActionStatus.collision, status

