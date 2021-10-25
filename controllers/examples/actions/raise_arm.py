from typing import List
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from tdw.add_ons.image_capture import ImageCapture
from tdw.backend.paths import EXAMPLE_CONTROLLER_OUTPUT_PATH
from magnebot.magnebot import Magnebot
from magnebot.magnebot_controller import MagnebotController
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.arm import Arm
from magnebot.arm_joint import ArmJoint
from magnebot.image_frequency import ImageFrequency
from magnebot.action_status import ActionStatus
from magnebot.actions.arm_motion import ArmMotion

"""
An example RaiseArm arm articulation action.
"""

class RaiseArm(ArmMotion):
    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        if self._arm == Arm.left:
            shoulder_id = static.arm_joints[ArmJoint.shoulder_left]
            elbow_id = static.arm_joints[ArmJoint.elbow_left]
            wrist_id = static.arm_joints[ArmJoint.wrist_left]
        else:
            shoulder_id = static.arm_joints[ArmJoint.shoulder_right]
            elbow_id = static.arm_joints[ArmJoint.elbow_right]
            wrist_id = static.arm_joints[ArmJoint.wrist_right]
        commands.extend([{"$type": "set_spherical_target",
                          "joint_id": shoulder_id,
                          "target": {"x": -179, "y": 0, "z": 0},
                          "id": static.robot_id},
                         {"$type": "set_revolute_target",
                          "joint_id": elbow_id,
                          "target": 0,
                          "id": static.robot_id},
                         {"$type": "set_spherical_target",
                          "joint_id": wrist_id,
                          "target": {"x": 0, "y": 0, "z": 0},
                          "id": static.robot_id}])
        return commands

    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        if not self._joints_are_moving(static=static, dynamic=dynamic):
            self.status = ActionStatus.success
        return []


class MyMagnebot(Magnebot):
    def raise_arm(self, arm: Arm) -> None:
        self.action = RaiseArm(arm=arm)


if __name__ == "__main__":
    c = Controller()
    magnebot = MyMagnebot()
    camera = ThirdPersonCamera(position={"x": -1.1, "y": 1.7, "z": 1.2},
                               look_at=magnebot.robot_id,
                               avatar_id="a")
    path = EXAMPLE_CONTROLLER_OUTPUT_PATH.joinpath("raise_arm")
    print(f"Images will be saved to: {path}")
    capture = ImageCapture(avatar_ids=["a"], path=path)
    c.add_ons.extend([magnebot, camera, capture])
    commands = [{"$type": "load_scene",
                 "scene_name": "ProcGenScene"},
                TDWUtils.create_empty_room(12, 12)]
    commands.extend(MagnebotController.get_default_post_processing_commands())
    c.communicate(commands)
    magnebot.raise_arm(arm=Arm.right)
    while magnebot.action.status == ActionStatus.ongoing:
        c.communicate([])
    c.communicate([])
    c.communicate({"$type": "terminate"})