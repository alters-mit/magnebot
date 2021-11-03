from tdw.tdw_utils import TDWUtils
from magnebot import MagnebotController
from magnebot.util import get_default_post_processing_commands


class MyController(MagnebotController):
    """
    Define a custom scene setup.
    """

    def init_scene(self):
        scene = [{"$type": "load_scene",
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12)]
        objects = []
        objects.extend(self.get_add_physics_object(model_name="rh10",
                                                   position={"x": 0.04, "y": 0, "z": 1.081},
                                                   object_id=self.get_unique_id()))
        self._init_scene(scene=scene,
                         objects=objects,
                         position={"x": 1, "y": 0, "z": -3},
                         rotation={"x": 0, "y": 46, "z": 0},
                         post_processing=get_default_post_processing_commands())


if __name__ == "__main__":
    c = MyController()
    c.init_scene()
    print(c.magnebot.dynamic.transform.position)
    c.end()
