from typing import Dict, List
from tdw.tdw_utils import TDWUtils
from magnebot.demo_controller import DemoController
from magnebot import Arm


class Carry(DemoController):
    """
    Pick up to objects and carry them to the destination.
    """

    def __init__(self, port: int = 1071, launch_build: bool = True, screen_width: int = 1024, screen_height: int = 1024,
                 debug: bool = False, images_directory: str = "images"):
        super().__init__(port=port, launch_build=launch_build, screen_width=screen_width, screen_height=screen_height,
                         images_directory=images_directory, debug=debug, image_pass_only=True)
        self.target_id_0: int = -1
        self.target_id_1: int = -1

    def run(self) -> None:
        self.init_scene(scene="2b", layout=1, room=4)
        # The position for the third-person camera. We'll use this later to parent it to the Magnebot.
        camera_position = {"x": 4.54, "y": 8, "z": -2.56}
        self.add_camera(position=camera_position, look_at=True)

        # Go to the first target and pick it up.
        self.move_to(target=self.target_id_0, arrived_at=0.75)
        self.grasp(target=self.target_id_0, arm=Arm.right)
        self.reset_arm(arm=Arm.right)

        # Go to the second object.
        self.move_to(target={"x": 5.8, "y": 0, "z": -1.1725}, arrived_at=0.75)
        p = self.state.object_transforms[self.target_id_1].position
        p[1] = 0
        self.turn_to(target=TDWUtils.array_to_vector3(p))
        self.grasp(target=self.target_id_1, arm=Arm.left)
        # Back away.
        self.move_by(-0.8)
        self.reset_arm(arm=Arm.left)

        # Start to follow the Magnebot.
        relative_position = TDWUtils.vector3_to_array(camera_position) - self.state.magnebot_transform.position
        self._next_frame_commands.append({"$type": "parent_avatar_to_robot",
                                          "avatar_id": "c",
                                          "position": TDWUtils.array_to_vector3(relative_position)})

        # Go to the "goal position".
        self.navigate(target={"x": 8.557, "y": 0, "z": 1.31}, aligned_at=0.75)
        # Drop each target.
        for object_id, arm in zip([self.target_id_0, self.target_id_1], [Arm.right, Arm.left]):
            self.reach_for(target={"x": 9.152, "y": 0.75, "z": 0.731}, arm=arm)
            self.drop(target=object_id, arm=arm)
            self.reset_arm(arm=arm)
        # Back away.
        self.move_by(-1)
        self.end()

    def _get_scene_init_commands(self, magnebot_position: Dict[str, float]) -> List[dict]:
        # Add two target objects.
        self.target_id_0: int = self._add_object(model_name="jug05",
                                                 position={"x": 7.73, "y": 0, "z": -3.43})
        self.target_id_1: int = self._add_object(model_name="jug05",
                                                 position={"x": 5.548, "y": 0.9215012, "z": -0.595})
        return super()._get_scene_init_commands(magnebot_position=magnebot_position)


if __name__ == "__main__":
    m = Carry(launch_build=False, images_directory="D:/magnebot/carry", debug=True)
    m.run()
