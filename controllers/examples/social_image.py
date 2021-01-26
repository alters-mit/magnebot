from pathlib import Path
from magnebot import Magnebot

"""
Generate the image used for the GitHub social preview card.
"""

if __name__ == "__main__":
    m = Magnebot(launch_build=False, screen_width=1024, screen_height=1024, skip_frames=0)
    m.init_scene(scene="2b", layout=1, room=1)

    # Add a third-person camera.
    m.add_camera({"x": -9.39, "y": 0.85, "z": 2.18}, look_at=True)

    with Path("../../social.jpg").open("wb") as f:
        f.write(m.state.third_person_images["c"]["img"])
    m.end()
