from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from tdw.add_ons.image_capture import ImageCapture
from tdw.backend.paths import EXAMPLE_CONTROLLER_OUTPUT_PATH
from magnebot import Magnebot, ActionStatus

"""
A simple example of a third-person camera.
"""

c = Controller()
magnebot = Magnebot()
# Create a camera and enable image capture.
camera = ThirdPersonCamera(position={"x": 2, "y": 3, "z": -1.5},
                           look_at=magnebot.robot_id,
                           avatar_id="a")
path = EXAMPLE_CONTROLLER_OUTPUT_PATH.joinpath("magnebot_third_person_camera")
print(f"Images will be saved to: {path}")
capture = ImageCapture(avatar_ids=["a"], path=path)
# Note the order of add-ons. The Magnebot must be added first so that the camera can look at it.
c.add_ons.extend([magnebot, camera, capture])
c.communicate([{"$type": "load_scene",
                "scene_name": "ProcGenScene"},
               TDWUtils.create_empty_room(12, 12)])
magnebot.move_by(3)
while magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate([])
magnebot.turn_by(45)
while magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate([])
magnebot.move_by(-2)
while magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate([])
c.communicate({"$type": "terminate"})
