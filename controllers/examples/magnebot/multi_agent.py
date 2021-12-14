from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from magnebot import Magnebot, ActionStatus

"""
A minimal multi-agent simulation with Magnebots.
"""

c = Controller()
# Create a camera.
camera = ThirdPersonCamera(position={"x": 2, "y": 6, "z": -1.5},
                           look_at={"x": 0, "y": 0.5, "z": 0},
                           avatar_id="a")
# Add two Magnebots.
magnebot_0 = Magnebot(position={"x": -2, "y": 0, "z": 0},
                      robot_id=c.get_unique_id())
magnebot_1 = Magnebot(position={"x": 2, "y": 0, "z": 0},
                      robot_id=c.get_unique_id())
c.add_ons.extend([camera, magnebot_0, magnebot_1])
# Load the scene.
c.communicate([{"$type": "load_scene",
                "scene_name": "ProcGenScene"},
               TDWUtils.create_empty_room(12, 12)])
# Move the Magnebots.
magnebot_0.move_by(-2)
magnebot_1.move_by(4)
while magnebot_0.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate([])
c.communicate({"$type": "terminate"})
