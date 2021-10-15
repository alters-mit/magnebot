from pathlib import Path
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from tdw.tdw_utils import TDWUtils
from tdw.output_data import Images
from magnebot import MagnebotController

"""
Generate the image used for the GitHub social preview card.
"""

if __name__ == "__main__":
    m = MagnebotController(screen_width=1024, screen_height=1024, skip_frames=0)
    m.init_floorplan_scene(scene="2b", layout=1, room=1)
    camera = ThirdPersonCamera(position={"x": -9.39, "y": 0.85, "z": 2.18},
                               look_at=0,
                               avatar_id="c")
    m.add_ons.append(camera)
    resp = m.communicate([{"$type": "set_img_pass_encoding",
                           "value": False},
                          {"$type": "set_pass_masks",
                           "pass_masks": ["_img"],
                           "avatar_id": "c"},
                          {"$type": "send_images",
                           "frequency": "once",
                           "ids": ["c"]}])
    TDWUtils.save_images(images=Images(resp[0]),
                         filename="social",
                         output_directory=str(Path("../../").resolve()),
                         append_pass=False)
    m.end()
