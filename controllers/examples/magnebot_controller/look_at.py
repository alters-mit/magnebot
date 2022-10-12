from tdw.tdw_utils import TDWUtils
from tdw.backend.paths import EXAMPLE_CONTROLLER_OUTPUT_PATH
from magnebot import MagnebotController
from magnebot.util import get_default_post_processing_commands


class LookAtExample(MagnebotController):
    """
    Minimal example of the `look_at(target)` action.
    """

    def init_scene(self):
        scene = [{"$type": "load_scene",
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12)]
        objects = []
        objects.extend(self.get_add_physics_object(model_name="rh10",
                                                   position={"x": -1, "y": 0, "z": 2},
                                                   object_id=self.get_unique_id()))
        self._init_scene(scene=scene,
                         objects=objects,
                         position={"x": 1, "y": 0, "z": -3},
                         rotation={"x": 0, "y": 46, "z": 0},
                         post_processing=get_default_post_processing_commands())


d = EXAMPLE_CONTROLLER_OUTPUT_PATH.joinpath("magnebot_look_at")
if not d.exists():
    d.mkdir(parents=True)
print(f"Images will be saved to: {d}")
c = LookAtExample()
c.init_scene()
c.look_at(target={"x": -1, "y": 0, "z": 2})
c.magnebot.dynamic.save_images(output_directory=d)
c.end()
