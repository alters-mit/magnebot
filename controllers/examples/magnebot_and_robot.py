from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.robot import Robot
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from magnebot import Magnebot, ImageFrequency, ActionStatus


"""
Add two agents: A robot and a Magnebot. They will move concurrently.
"""


c = Controller()
robot: Robot = Robot(robot_id=c.get_unique_id(), name="ur5", position={"x": -0.4, "y": 0, "z": 2.6})
magnebot: Magnebot = Magnebot(robot_id=c.get_unique_id(), position={"x": 0, "y": 0, "z": -0.5},
                              image_frequency=ImageFrequency.never)
camera: ThirdPersonCamera = ThirdPersonCamera(position={"x": -6, "y": 4, "z": -2},
                                              avatar_id="a",
                                              look_at={"x": 0, "y": 0, "z": -0.25})
c.add_ons.extend([robot, magnebot, camera])
c.communicate(TDWUtils.create_empty_room(12, 12))

# Wait for the robots to initialize.
while robot.joints_are_moving() or magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])

robot.set_joint_targets(targets={robot.static.joint_ids_by_name["shoulder_link"]: 45,
                                 robot.static.joint_ids_by_name["forearm_link"]: -65})
magnebot.move_by(1)
while robot.joints_are_moving() or magnebot.action.status == ActionStatus.ongoing:
    c.communicate([])
c.communicate({"$type": "terminate"})
