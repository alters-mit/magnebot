from tdw.tdw_utils import TDWUtils
from magnebot import MagnebotController
from magnebot.util import get_default_post_processing_commands


class CollisionDetection(MagnebotController):
    """
    Show the difference between arrived_offset values and collision detection settings.
    """

    def init_scene(self):
        scene = [{"$type": "load_scene",
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12)]
        objects = self.get_add_physics_object(model_name="rh10",
                                              position={"x": 0.04, "y": 0, "z": 1.081},
                                              object_id=self.get_unique_id())
        self._init_scene(scene=scene,
                         objects=objects,
                         position={"x": 1, "y": 0, "z": -3},
                         rotation={"x": 0, "y": 46, "z": 0},
                         post_processing=get_default_post_processing_commands())

    def run(self, arrived_offset: float, objects: bool) -> None:
        self.init_scene()
        object_id = list(self.objects.transforms.keys())[0]
        self.magnebot.collision_detection.objects = objects
        status = self.move_to(object_id, arrived_at=0.3, aligned_at=1, arrived_offset=arrived_offset)
        print(status)
        print(self.objects.transforms[object_id].position)


if __name__ == "__main__":
    c = CollisionDetection()
    c.run(arrived_offset=0, objects=True)
    c.run(arrived_offset=0.3, objects=True)
    c.run(arrived_offset=0, objects=False)
    c.end()
