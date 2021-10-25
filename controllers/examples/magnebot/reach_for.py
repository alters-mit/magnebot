from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from magnebot import Magnebot, Arm, ActionStatus
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.ik.orientation_mode import OrientationMode

"""
Reach for a target position with different orientation parameters.
"""

c = Controller()
camera = ThirdPersonCamera(position={"x": 0.6, "y": 1.6, "z": 1.6},
                           look_at={"x": 0, "y": 0, "z": 0})
magnebot = Magnebot()
c.add_ons.extend([camera, magnebot])
c.communicate([{"$type": "load_scene",
                "scene_name": "ProcGenScene"},
               TDWUtils.create_empty_room(12, 12)])
target = {"x": 0.2, "y": 0.5, "z": 0.5}
# Use default orientation parameters (auto, auto).
magnebot.reach_for(target=target, arm=Arm.left)
while magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate([])
magnebot.reset_arm(arm=Arm.left)
while magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate([])
# Explicitly set orientation parameters. The motion will be very different!
magnebot.reach_for(target=target, arm=Arm.left,
                   target_orientation=TargetOrientation.right, orientation_mode=OrientationMode.z)
while magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate([])
c.communicate({"$type": "terminate"})
