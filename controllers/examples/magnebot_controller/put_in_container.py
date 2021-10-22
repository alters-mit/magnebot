from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from magnebot import MagnebotController, Arm
from magnebot.action_status import ActionStatus


class PickUp(MagnebotController):
    """
    Pick up multiple objects in the scene and put them in a container.
    """

    def __init__(self, port: int = 1071, screen_width: int = 256, screen_height: int = 256):
        super().__init__(port=port, screen_width=screen_width, screen_height=screen_height)
        self.target_object_0: int = self.get_unique_id()
        self.target_object_1: int = self.get_unique_id()
        self.box: int = self.get_unique_id()

    def init_scene(self) -> None:
        scene = [{"$type": "load_scene",
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12)]
        objects = self.get_add_physics_object(model_name="jug05",
                                              object_id=self.target_object_0,
                                              position={"x": -0.408, "y": 0, "z": 0.428})
        objects.extend(self.get_add_physics_object(model_name="jug05",
                                                   object_id=self.target_object_1,
                                                   position={"x": -1.76, "y": 0, "z": -1.08}))
        objects.extend(self.get_add_physics_object(model_name="basket_18inx18inx12iin",
                                                   object_id=self.box,
                                                   scale_factor={"x": 1, "y": 0.7, "z": 1},
                                                   position={"x": 0.03, "y": 0, "z": -2.38}))
        self._init_scene(scene=scene,
                         objects=objects,
                         post_processing=self.get_default_post_processing_commands())


if __name__ == "__main__":
    c = PickUp()
    c.init_scene()

    camera = ThirdPersonCamera(position={"x": -2.36, "y": 2, "z": -2.27}, look_at=c.magnebot.robot_id)
    c.add_ons.append(camera)

    # Grasp the first object.
    c.grasp(target=c.target_object_0, arm=Arm.left)
    c.reset_arm(arm=Arm.left)

    # Go to the next object.
    c.move_to(target=c.target_object_1, arrived_offset=0.3)
    # Grasp the object.
    c.grasp(target=c.target_object_1, arm=Arm.right)
    c.reset_arm(arm=Arm.right)
    # Go to the box.
    c.move_to(target=c.box, arrived_offset=0.3)

    # Get a point above the box.
    box_top = c.objects.transforms[c.box].position[:]
    box_top[1] += c.objects.objects_static[c.box].size[1] + 0.4

    # Drop each object.
    for arm, object_id in zip([Arm.left, Arm.right], [c.target_object_0, c.target_object_1]):
        c.reach_for(target=TDWUtils.array_to_vector3(box_top), arm=arm, absolute=True)
        status = c.drop(target=object_id, arm=arm)
        assert status == ActionStatus.success, status
        c.reset_arm(arm=arm)
    c.move_by(distance=-0.8)
    c.end()
