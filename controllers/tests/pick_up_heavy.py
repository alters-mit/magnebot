from magnebot import Magnebot, Arm, ActionStatus


class PickUpHeavy(Magnebot):
    """
    Test Magnebot tipping. The Magnebot will try to pick up a heavy object, failed, and then correct the tip.
    """

    def __init__(self, port: int = 1071, screen_width: int = 1024, screen_height: int = 1024):
        super().__init__(port=port, screen_height=screen_height, screen_width=screen_width)
        self._debug = False
        self.target_id: int = -1

    def init_scene(self) -> ActionStatus:
        self.target_id = self._add_object(model_name="trunck",
                                          position={"x": 0.04, "y": 0, "z": 1.081}, mass=100)
        return super().init_scene()


if __name__ == "__main__":
    m = PickUpHeavy()
    m.init_scene()
    m.grasp(target=m.target_id, arm=Arm.left)
    m.reset_arm(arm=Arm.left)

    # Try to pick up a heavy object, start to tip over, and resolve the tipping.
    status = m.move_by(-1)
    assert status != ActionStatus.success, status
    status = m.move_by(1)
    assert status != ActionStatus.success, status
    status = m.move_by(-1)
    assert status == ActionStatus.success, status

    # Try to pick up something heavy, turn, and give up.
    m.move_by(1)
    status = m.grasp(target=m.target_id, arm=Arm.left)
    assert status == ActionStatus.success, status
    status = m.turn_by(45)
    assert status == ActionStatus.success, status
    status = m.move_by(-1)
    assert status != ActionStatus.success, status
    m.reset_position()
    m.end()
