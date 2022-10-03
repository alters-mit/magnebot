from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from tdw.add_ons.image_capture import ImageCapture
from tdw.backend.paths import EXAMPLE_CONTROLLER_OUTPUT_PATH
from magnebot import Magnebot, ActionStatus
from magnebot.constants import TORSO_MIN_Y
from magnebot.camera_coordinate_space import CameraCoordinateSpace

c = Controller()
m = Magnebot(visual_camera_mesh=True, parent_camera_to_torso=False)
c.add_ons.append(m)
c.communicate(TDWUtils.create_empty_room(12, 12))
c.communicate([])
m.move_camera({"x": 0, "y": 0.6, "z": 0}, coordinate_space=CameraCoordinateSpace.relative_to_camera)
c.communicate([])
m.rotate_camera(pitch=30)
while m.action.status == ActionStatus.ongoing:
    c.communicate([])
camera = ThirdPersonCamera(position={"x": -1, "y": 1.6, "z": 1.5},
                           look_at={"x": 0, "y": 0.7, "z": 0},
                           avatar_id="a")
path = EXAMPLE_CONTROLLER_OUTPUT_PATH.joinpath("magnebot_visual_camera")
print(f"Images will be saved to: {path}")
capture = ImageCapture(avatar_ids=["a", m.static.avatar_id], path=path)
c.add_ons.extend([camera, capture])
c.communicate([])
# Slide the torso away from the camera.
m.slide_torso(height=TORSO_MIN_Y)
while m.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate({"$type": "terminate"})
