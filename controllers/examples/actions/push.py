from enum import Enum
from typing import List
import numpy as np
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from tdw.output_data import OutputData, Transforms, Bounds
from magnebot import Magnebot, ActionStatus, Arm, ArmJoint, ImageFrequency
from magnebot.ik.orientation_mode import OrientationMode
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.actions.ik_motion import IKMotion
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.magnebot_static import MagnebotStatic


"""
Define a Push IK arm articulation action and implement it in a controller.
"""


class PushState(Enum):
    getting_bounds = 1
    sliding_torso = 2
    pushing = 4


class Push(IKMotion):
    def __init__(self, target: int, arm: Arm, dynamic: MagnebotDynamic):
        """
        :param target: The target object ID.
        :param arm: The arm used for this action.
        :param dynamic: The dynamic Magnebot data.
        """

        self.target: int = target
        self.push_state: PushState = PushState.getting_bounds

        # This will be set during get_ongoing_commands()
        self.ik_target_position: np.array = np.array([0, 0, 0])
        self.initial_object_centroid: np.array = np.array([0, 0, 0])
        self.initial_object_position: np.array = np.array([0, 0, 0])

        super().__init__(arm=arm,
                         orientation_mode=OrientationMode.x,
                         target_orientation=TargetOrientation.up,
                         dynamic=dynamic,
                         set_torso=True)

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp,
                                                       static=static,
                                                       dynamic=dynamic,
                                                       image_frequency=image_frequency)
        # Request bounds data.
        commands.append({"$type": "send_bounds",
                         "frequency": "once"})
        return commands

    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        # Use the bounds data to get the position of the object.
        if self.push_state == PushState.getting_bounds:
            # Get the initial centroid of the object and its initial position.
            for i in range(len(resp) - 1):
                r_id = OutputData.get_data_type_id(resp[i])
                if r_id == "boun":
                    bounds = Bounds(resp[i])
                    for j in range(bounds.get_num()):
                        if bounds.get_id(j) == self.target:
                            self.initial_object_centroid = bounds.get_center(j)
                            break
            self.initial_object_position = self._get_object_position(resp=resp)
            # Slide the torso up and above the target object.
            torso_position = self.initial_object_centroid[1] + 0.1
            # Convert the torso position from meters to prismatic joint position.
            torso_position = self._y_position_to_torso_position(torso_position)
            # Start sliding the torso.
            self.push_state = PushState.sliding_torso
            return [{"$type": "set_prismatic_target",
                     "id": static.robot_id,
                     "joint_id": static.arm_joints[ArmJoint.torso],
                     "target": torso_position}]
        # Slide the torso.
        elif self.push_state == PushState.sliding_torso:
            # Continue to slide the torso.
            if self._joints_are_moving(static=static, dynamic=dynamic):
                return []
            # Push the object.
            else:
                magnet_position = dynamic.joints[static.magnets[self.arm]].position
                # Get a position opposite the center of the object from the magnet.
                v = magnet_position - self.initial_object_centroid
                v = v / np.linalg.norm(v)
                target_position = self.initial_object_centroid - (v * 0.1)
                # Convert the position to relative coordinates.
                self.ik_target_position = self._absolute_to_relative(position=target_position, dynamic=dynamic)
                # Start the IK motion.
                self._set_start_arm_articulation_commands(static=static, dynamic=dynamic)
                self.push_state = PushState.pushing
                return self._evaluate_arm_articulation(resp=resp, static=static, dynamic=dynamic)
        # Continue to push.
        elif self.push_state == PushState.pushing:
            return self._evaluate_arm_articulation(resp=resp, static=static, dynamic=dynamic)
        else:
            raise Exception(f"Not defined: {self.push_state}")

    def _get_object_position(self, resp: List[bytes]) -> np.array:
        for i in range(len(resp) - 1):
            r_id = OutputData.get_data_type_id(resp[i])
            if r_id == "tran":
                transforms = Transforms(resp[i])
                for j in range(transforms.get_num()):
                    if transforms.get_id(j) == self.target:
                        return transforms.get_position(j)
        raise Exception()

    def _get_ik_target_position(self) -> np.array:
        return self.ik_target_position

    def _is_success(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> bool:
        target_position = self._get_object_position(resp=resp)
        return np.linalg.norm(self.initial_object_position - target_position) > 0.1

    def _get_fail_status(self) -> ActionStatus:
        return ActionStatus.failed_to_move


class PushController(Controller):
    def __init__(self, port: int = 1071, check_version: bool = True, launch_build: bool = True):
        super().__init__(port=port, check_version=check_version, launch_build=launch_build)
        self.magnebot: Magnebot = Magnebot()
        self.communicate({"$type": "set_screen_size",
                          "width": 1024,
                          "height": 1024})

    def run(self):
        magnebot = Magnebot(robot_id=0)
        camera = ThirdPersonCamera(position={"x": 1.03, "y": 2, "z": 2.34},
                                   look_at=0,
                                   follow_object=0)
        self.add_ons.extend([magnebot, camera])
        commands = [TDWUtils.create_empty_room(12, 12)]
        trunck_id = self.get_unique_id()
        vase_id = self.get_unique_id()
        commands.extend(self.get_add_physics_object(model_name="trunck",
                                                    position={"x": -2.133, "y": 0, "z": 2.471},
                                                    rotation={"x": 0, "y": -29, "z": 0},
                                                    scale_factor={"x": 1, "y": 0.8, "z": 1},
                                                    default_physics_values=False,
                                                    scale_mass=False,
                                                    kinematic=True,
                                                    object_id=trunck_id))
        commands.extend(self.get_add_physics_object(model_name="vase_02",
                                                    position={"x": -1.969, "y": 0.794254, "z": 2.336},
                                                    object_id=vase_id))
        self.communicate(commands)
        # Wait for the Magnebot to initialize.
        while magnebot.action.status == ActionStatus.ongoing:
            self.communicate([])
        # Move to the object.
        magnebot.move_to(target=trunck_id, arrived_offset=0.3)
        while magnebot.action.status == ActionStatus.ongoing:
            self.communicate([])

        # Push the vase.
        magnebot.action = Push(target=vase_id, arm=Arm.right, dynamic=magnebot.dynamic)
        while magnebot.action.status == ActionStatus.ongoing:
            self.communicate([])
        print(magnebot.action.status)

        # Back away. Stop moving the camera.
        camera.follow_object = None
        camera.look_at_target = None
        magnebot.move_by(-0.5)
        while magnebot.action.status == ActionStatus.ongoing:
            self.communicate([])
        # Reset the arms.
        for arm in [Arm.left, Arm.right]:
            magnebot.reset_arm(arm=arm)
            while magnebot.action.status == ActionStatus.ongoing:
                self.communicate([])
        self.communicate({"$type": "terminate"})


if __name__ == "__main__":
    c = PushController()
    c.run()
