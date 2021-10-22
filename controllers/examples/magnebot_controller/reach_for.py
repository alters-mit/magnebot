from tdw.add_ons.third_person_camera import ThirdPersonCamera
from magnebot import MagnebotController, Arm
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.ik.orientation_mode import OrientationMode

"""
Reach for a target position with different orientation parameters.
"""

c = MagnebotController(skip_frames=0)
c.init_scene()
camera = ThirdPersonCamera(position={"x": 0.6, "y": 1.6, "z": 1.6},
                           look_at={"x": 0, "y": 0, "z": 0})
c.add_ons.append(camera)
target = {"x": 0.2, "y": 0.5, "z": 0.5}
# Use default orientation parameters (auto, auto).
c.reach_for(target=target, arm=Arm.left)
print(c.magnebot.dynamic.joints[c.magnebot.static.magnets[Arm.left]].position)
c.reset_arm(arm=Arm.left)
# Explicitly set orientation parameters. The motion will be very different!
c.reach_for(target=target, arm=Arm.left,
            target_orientation=TargetOrientation.right, orientation_mode=OrientationMode.z)
print(c.magnebot.dynamic.joints[c.magnebot.static.magnets[Arm.left]].position)
c.end()
