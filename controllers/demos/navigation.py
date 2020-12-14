import json
from magnebot.paths import SPAWN_POSITIONS_PATH
from magnebot.demo_controller import DemoController

"""
Create a demo video of basic Magnebot navigation.
"""


if __name__ == "__main__":
    m = DemoController(launch_build=False, images_directory="D:/magnebot/navigation_demo")
    m.init_scene(scene="2a", layout=0, room=4)

    m.add_camera(position={"x": 0.8, "y": 10, "z": -1.3}, look_at=True)

    # Go to the center of room 2.
    spawn_positions = json.loads(SPAWN_POSITIONS_PATH.read_text())
    m.navigate(target=spawn_positions["2"]["0"]["2"])
    m.end()
