from tdw.tdw_utils import TDWUtils
from magnebot import Arm, ActionStatus, MagnebotController
from magnebot.ik.orientation_mode import OrientationMode
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.util import get_default_post_processing_commands


class Grasp(MagnebotController):
    """
    Test the grasp() function.
    """

    def __init__(self, port: int = 1071):
        super().__init__(port=port)
        self.target_id: int = self.get_unique_id()

    def init_scene(self) -> None:
        scene = [{"$type": "load_scene",
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12)]
        objects = self.get_add_physics_object(object_id=self.target_id,
                                              model_name="blue_satchal",
                                              position={"x": -0.1024729, "y": 0, "z": -0.6279346},
                                              rotation={"x": -7.730941e+11, "y": 152.176, "z": 4.398})
        self._init_scene(scene=scene,
                         objects=objects,
                         post_processing=get_default_post_processing_commands())


if __name__ == "__main__":
    m = Grasp()
    m.init_scene()
    m.turn_to(m.target_id)
    status = m.grasp(m.target_id, arm=Arm.right,
                     target_orientation=TargetOrientation.up, orientation_mode=OrientationMode.y)
    assert status == ActionStatus.success, status
    m.end()
