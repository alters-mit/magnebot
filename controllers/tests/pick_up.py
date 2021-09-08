from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from magnebot import MagnebotController, Arm
from magnebot.action_status import ActionStatus


class PickUp(MagnebotController):
    """
    Test the Magnebot's ability to grasp, lift, go to, and drop objects.
    """

    def __init__(self, port: int = 1071, screen_width: int = 256, screen_height: int = 256):
        super().__init__(port=port, screen_width=screen_width, screen_height=screen_height)
        self.target_object_0: int = -1
        self.target_object_1: int = -1
        self.box: int = -1

    def init_scene(self) -> None:
        # Add some objects to an empty room. Record their object IDs.
        self.target_object_0 = self._add_object("jug05", position={"x": -0.408, "y": 0, "z": 0.428},)
        self.target_object_1 = self._add_object("jug05", position={"x": -1.76, "y": 0, "z": -1.08})
        self.box = self._add_object("basket_18inx18inx12iin", position={"x": 0.03, "y": 0, "z": -2.38},
                                    scale={"x": 1, "y": 0.7, "z": 1})
        super().init_scene()


if __name__ == "__main__":
    m = PickUp()
    m.init_scene()

    camera = ThirdPersonCamera(position={"x": -2.36, "y": 2, "z": -2.27}, look_at=m.magnebot.robot_id)
    m.add_ons.append(camera)

    # Grasp the first object.
    status = m.grasp(target=m.target_object_0, arm=Arm.left)
    assert status == ActionStatus.success, status
    status = m.reset_arm(arm=Arm.left)
    # Failed to reset entirely due to the mass of the object.
    assert status == ActionStatus.success, status

    # Go to the next object.
    status = m.move_to(target=m.target_object_1, arrived_at=0.3)
    assert status == ActionStatus.success, status
    # Grasp the object.
    status = m.grasp(target=m.target_object_1, arm=Arm.right)
    assert status == ActionStatus.success, status
    status = m.reset_arm(arm=Arm.right)
    # Failed to reset entirely due to the mass of the object.
    assert status == ActionStatus.success, status
    # Go to the box.
    m.move_to(target=m.box, arrived_at=0.3)

    # Get a point above the box.
    box_top = m.objects.transforms[m.box].position[:]
    box_top[1] += m.objects.objects_static[m.box].size[1] + 0.7

    # Drop each object.
    for arm, object_id in zip([Arm.left, Arm.right], [m.target_object_0, m.target_object_1]):
        m.reach_for(target=TDWUtils.array_to_vector3(box_top), arm=arm, absolute=True)
        status = m.drop(target=object_id, arm=arm)
        assert status == ActionStatus.success, status
        m.reset_arm(arm=arm)
    m.move_by(distance=-0.8)
    m.end()
