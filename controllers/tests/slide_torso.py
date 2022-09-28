import numpy as np
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus
from magnebot.arm_joint import ArmJoint
from magnebot.constants import TORSO_MIN_Y, TORSO_MAX_Y

"""
Test the `SlideTorso` command.
"""

c = Controller()
m = Magnebot()
c.add_ons.append(m)
c.communicate(TDWUtils.create_empty_room(12, 12))
torso_id = m.static.arm_joints[ArmJoint.torso]
# Slide all the way down.
m.slide_torso(height=0)
while m.action.status == ActionStatus.ongoing:
    c.communicate([])
y = np.radians(m.dynamic.joints[torso_id].angles)[0]
d = np.linalg.norm(y - TORSO_MIN_Y)
assert d < 0.02, (y, d)
# Slide all the way up.
m.slide_torso(height=1)
while m.action.status == ActionStatus.ongoing:
    c.communicate([])
y = np.radians(m.dynamic.joints[torso_id].angles)[0]
d = np.linalg.norm(y - TORSO_MAX_Y)
assert d < 0.04, (y, d)
c.communicate({"$type": "terminate"})
