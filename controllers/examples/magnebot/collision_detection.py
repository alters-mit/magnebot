from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.object_manager import ObjectManager
from magnebot import Magnebot, ActionStatus


class CollisionDetection(Controller):
    """
    Show the difference between arrived_offset values and collision detection settings.
    """

    def __init__(self, port: int = 1071, check_version: bool = True, launch_build: bool = True):
        super().__init__(port=port, check_version=check_version, launch_build=launch_build)
        self.object_id = self.get_unique_id()
        self.magnebot = Magnebot()
        self.object_manager = ObjectManager()
        self.add_ons.extend([self.object_manager, self.magnebot])
        self.object_id: int = -1

    def init_scene(self):
        self.object_id = self.get_unique_id()
        self.magnebot.reset()
        commands = [{"$type": "load_scene",
                     "scene_name": "ProcGenScene"},
                    TDWUtils.create_empty_room(12, 12)]
        commands.extend(self.get_add_physics_object(model_name="rh10",
                                                    position={"x": 0.04, "y": 0, "z": 1.081},
                                                    object_id=self.object_id))
        self.communicate(commands)

    def run(self, arrived_offset: float, objects: bool) -> None:
        self.init_scene()
        self.object_manager.initialized = False
        self.magnebot.collision_detection.objects = objects
        self.magnebot.move_to(self.object_id, arrived_at=0.3, aligned_at=1, arrived_offset=arrived_offset)
        while self.magnebot.action.status == ActionStatus.ongoing:
            self.communicate([])
        self.communicate([])
        print(self.magnebot.action.status)
        print(self.object_manager.transforms[self.object_id].position)


if __name__ == "__main__":
    c = CollisionDetection()
    c.run(arrived_offset=0, objects=True)
    c.run(arrived_offset=0.3, objects=True)
    c.run(arrived_offset=0, objects=False)
    c.communicate({"$type": "terminate"})
