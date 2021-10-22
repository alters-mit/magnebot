from tdw.tdw_utils import TDWUtils
from magnebot import MagnebotController, Arm, ActionStatus


class PickUpHeavy(MagnebotController):
    """
    Test Magnebot tipping. The Magnebot will try to pick up a heavy object, failed, and then correct the tip.
    """

    def __init__(self, port: int = 1071, screen_width: int = 1024, screen_height: int = 1024):
        super().__init__(port=port, screen_height=screen_height, screen_width=screen_width)
        self._debug = False
        self.target_id: int = self.get_unique_id()

    def init_scene(self) -> None:
        scene = [{"$type": "load_scene",
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12)]
        objects = self.get_add_physics_object(model_name="trunck",
                                              object_id=self.target_id,
                                              position={"x": 0.04, "y": 0, "z": 1.081})
        self._init_scene(scene=scene,
                         objects=objects,
                         post_processing=self.get_default_post_processing_commands())


if __name__ == "__main__":
    c = PickUpHeavy()
    c.init_scene()
    c.grasp(target=c.target_id, arm=Arm.left)
    c.reset_arm(arm=Arm.left)

    # Try to pick up a heavy object, start to tip over, and resolve the tipping.
    status = c.move_by(-1)
    assert status != ActionStatus.success, status
    c.drop(c.target_id, arm=Arm.left)
    status = c.move_by(1)
    assert status == ActionStatus.success, status
    status = c.move_by(-1)
    assert status == ActionStatus.success, status

    # Try to pick up something heavy, turn, and give up.
    c.move_by(1)
    status = c.grasp(target=c.target_id, arm=Arm.left)
    assert status == ActionStatus.success, status
    status = c.turn_by(45)
    assert status == ActionStatus.success, status
    status = c.move_by(-1)
    assert status != ActionStatus.success, status
    c.reset_position()
    c.end()
