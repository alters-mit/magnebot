from tdw.add_ons.third_person_camera import ThirdPersonCamera
from tdw.add_ons.image_capture import ImageCapture
from tdw.backend.paths import EXAMPLE_CONTROLLER_OUTPUT_PATH
from magnebot import MagnebotController

"""
A simple example of a third-person camera.
"""

c = MagnebotController()
c.init_scene()

# Create a camera and enable image capture.
camera = ThirdPersonCamera(position={"x": 2, "y": 3, "z": -1.5},
                           look_at=c.magnebot.robot_id,
                           avatar_id="a")
path = EXAMPLE_CONTROLLER_OUTPUT_PATH.joinpath("magnebot_third_person_camera")
print(f"Images will be saved to: {path}")
capture = ImageCapture(avatar_ids=["a"], path=path)
c.add_ons.extend([camera, capture])

c.move_by(3)
c.turn_by(45)
c.move_by(-2)
c.end()
