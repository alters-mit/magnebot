from pathlib import Path
from typing import List, Dict
from magnebot import Magnebot, Arm


class SocialImage(Magnebot):
    """
    Generate the image used for the GitHub social preview card.
    """

    def __init__(self, port: int = 1071):
        super().__init__(port=port, launch_build=False, screen_width=1024, screen_height=1024)
        self.target_object_id = 0

    def _get_scene_init_commands(self, magnebot_position: Dict[str, float]) -> List[dict]:
        self.target_object_id = self._add_object("basket_18inx18inx12iin_plastic_lattice",
                                                 scale={"x": 0.4, "y": 0.4, "z": 0.4},
                                                 position={"x": -8.788, "y": 0, "z": 0.854})
        return super()._get_scene_init_commands(magnebot_position=magnebot_position)


if __name__ == "__main__":
    m = SocialImage()
    m.init_scene(scene="2b", layout=1, room=1)

    # Add a third-person camera.
    m.add_camera({"x": -9.752, "y": 0.916, "z": 2.066}, look_at=True)

    # Grasp and pick up the container.
    m.grasp(target=m.target_object_id, arm=Arm.right)
    m.reach_for(target={"x": -8.391, "y": 0.51, "z": 0.939}, arm=Arm.right)

    with Path("../../social.jpg").open("wb") as f:
        f.write(m.state.third_person_images["c"]["img"])
    m.end()
