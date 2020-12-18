from pathlib import Path
from magnebot import Magnebot


class SocialImage(Magnebot):
    """
    Generate the image used for the GitHub social preview card.
    """


if __name__ == "__main__":
    m = SocialImage(launch_build=False, screen_width=1280, screen_height=640)
    m.init_scene(scene="2b", layout=1, room=1)

    # Add a third-person camera.
    m.add_camera({"x": -10.5, "y": 1.51, "z": 3.51}, look_at=True)

    with Path("../../social.jpg").open("wb") as f:
        f.write(m.state.third_person_images["c"]["img"])
    m.end()
