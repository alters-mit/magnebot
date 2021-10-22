from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from magnebot import MagnebotController, Arm, ActionStatus


class ReachHigh(MagnebotController):
    """
    Grasp an object on a shelf.
    """

    def __init__(self, port: int = 1071, screen_width: int = 1024, screen_height: int = 1024):
        super().__init__(port=port, screen_height=screen_height, screen_width=screen_width, skip_frames=0)
        self.target_id: int = self.get_unique_id()

    def init_scene(self) -> None:
        objects = self.get_add_physics_object(model_name="cabinet_36_wood_beach_honey",
                                              position={"x": 0.04, "y": 0, "z": 1.081},
                                              kinematic=True,
                                              object_id=self.get_unique_id())
        objects.extend(self.get_add_physics_object(model_name="jug05",
                                                   position={"x": -0.231, "y": 0.9215012, "z": 0.865},
                                                   object_id=self.target_id))
        scene = [TDWUtils.create_empty_room(12, 12),
                 self.get_add_material("parquet_long_horizontal_clean", library="materials_high.json"),
                 {"$type": "set_proc_gen_floor_material",
                  "name": "parquet_long_horizontal_clean"},
                 {"$type": "set_proc_gen_floor_texture_scale",
                  "scale": {"x": 8, "y": 8}}]
        self._init_scene(scene=scene,
                         objects=objects,
                         post_processing=self.get_default_post_processing_commands())


if __name__ == "__main__":
    c = ReachHigh()
    c.init_scene()
    camera = ThirdPersonCamera(position={"x": -2.36, "y": 2, "z": -2.27}, look_at=c.magnebot.robot_id)
    c.add_ons.append(camera)
    status = c.grasp(target=c.target_id, arm=Arm.left)
    assert status == ActionStatus.success, status
    c.reset_arm(arm=Arm.left)
    c.move_by(-0.8)
    c.turn_by(15)
    c.end()
