from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, Arm, ActionStatus


class ReachHigh(Magnebot):
    """
    Test whether the Magnebot can grasp an object on a shelf.
    """

    def __init__(self, port: int = 1071, screen_width: int = 1024, screen_height: int = 1024):
        super().__init__(port=port, screen_height=screen_height, screen_width=screen_width, skip_frames=0)
        self.target_id: int = -1

    def init_scene(self) -> ActionStatus:
        self._add_object(model_name="cabinet_36_wood_beach_honey", position={"x": 0.04, "y": 0, "z": 1.081}, mass=300)
        self.target_id = self._add_object(model_name="jug05",
                                          position={"x": -0.231, "y": 0.9215012, "z": 0.865})
        scene = [{"$type": "load_scene",
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12),
                 self.get_add_material("parquet_long_horizontal_clean", library="materials_high.json"),
                 {"$type": "set_proc_gen_floor_material",
                  "name": "parquet_long_horizontal_clean"},
                 {"$type": "set_proc_gen_floor_texture_scale",
                  "scale": {"x": 8, "y": 8}}]
        return self._init_scene(scene=scene,
                                post_processing=self._get_post_processing_commands())


if __name__ == "__main__":
    m = ReachHigh()
    m.init_scene()
    m.add_camera(position={"x": -2.36, "y": 2, "z": -2.27}, look_at=True)
    status = m.grasp(target=m.target_id, arm=Arm.left)
    assert status == ActionStatus.success, status
    m.reset_arm(arm=Arm.left)
    m.move_by(-0.8)
    m.turn_by(15)
    m.end()
