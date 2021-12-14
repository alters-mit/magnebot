from typing import List, Tuple
from abc import ABC, abstractmethod
from overrides import final
from tdw.output_data import OutputData, MagnebotWheels
from magnebot.action_status import ActionStatus
from magnebot.arm_joint import ArmJoint
from magnebot.actions.action import Action
from magnebot.image_frequency import ImageFrequency
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.collision_detection import CollisionDetection
from magnebot.constants import DEFAULT_WHEEL_FRICTION


class WheelMotion(Action, ABC):
    """
    Abstract base class for a motion action involving the Magnebot's wheels.
    """

    def __init__(self, dynamic: MagnebotDynamic, collision_detection: CollisionDetection, previous: Action = None):
        """
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        :param collision_detection: [The collision detection rules.](../collision_detection.md)
        :param previous: The previous action, if any.
        """

        super().__init__()
        # My collision detection rules.
        self._collision_detection: CollisionDetection = collision_detection
        self._resetting: bool = False
        # Immediately end the action if we're currently tipping.
        has_tipped, is_tipping = self._is_tipping(dynamic=dynamic)
        if has_tipped:
            self.status = ActionStatus.tipping
        # Immediately end the action if the previous action was the same motion and it ended with a collision or with tipping.
        elif self._collision_detection.previous_was_same and previous is not None and \
                previous.status != ActionStatus.success and previous.status != ActionStatus.ongoing and \
                self._previous_was_same(previous=previous):
            if previous.status == ActionStatus.collision:
                self.status = ActionStatus.collision
            elif previous.status == ActionStatus.tipping:
                self.status = ActionStatus.tipping

    @final
    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        """
        :param resp: The response from the build.
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        :param image_frequency: [How image data will be captured during the image.](../image_frequency.md)

        :return: A list of commands to initialize this action.
        """

        commands: List[dict] = super().get_initialization_commands(resp=resp, image_frequency=image_frequency,
                                                                   static=static, dynamic=dynamic)
        # Make the robot moveable.
        if dynamic.immovable:
            self._resetting = True
            commands.extend([{"$type": "set_immovable",
                              "id": static.robot_id,
                              "immovable": False},
                             {"$type": "set_prismatic_target",
                              "joint_id": static.arm_joints[ArmJoint.torso],
                              "target": 1,
                              "id": static.robot_id},
                             {"$type": "set_revolute_target",
                              "joint_id": static.arm_joints[ArmJoint.column],
                              "target": 0,
                              "id": static.robot_id}])
        # Reset the drive values.
        for wheel_id in static.wheels.values():
            drive = static.joints[wheel_id].drives["x"]
            commands.extend([{"$type": "set_robot_joint_drive",
                              "joint_id": wheel_id,
                              "force_limit": drive.force_limit,
                              "stiffness": drive.stiffness,
                              "damping": drive.damping,
                              "id": static.robot_id},
                             {"$type": "set_robot_joint_friction",
                              "joint_id": wheel_id,
                              "friction": DEFAULT_WHEEL_FRICTION,
                              "id": static.robot_id}])
        return commands

    @final
    def get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        """
        Evaluate an action per-frame to determine whether it's done.

        :param resp: The response from the build.
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)

        :return: A list of commands to send to the build if the action is ongoing.
        """

        if self._resetting:
            self._resetting = dynamic.joints[static.arm_joints[ArmJoint.torso]].moving and \
                              dynamic.joints[static.arm_joints[ArmJoint.column]].moving
            if self._resetting:
                return []
            else:
                return self._get_start_wheels_commands(static=static, dynamic=dynamic)
        else:
            return self._get_ongoing_commands(resp=resp, static=static, dynamic=dynamic)

    @final
    def get_end_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                         image_frequency: ImageFrequency) -> List[dict]:
        """
        :param resp: The response from the build.
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        :param image_frequency: [How image data will be captured during the image.](../image_frequency.md)

        :return: A list of commands that must be sent to end any action.
        """

        commands = self._get_stop_wheels_commands(static=static, dynamic=dynamic)
        commands.extend(super().get_end_commands(resp=resp, static=static, dynamic=dynamic,
                                                 image_frequency=image_frequency))
        return commands

    @abstractmethod
    def _get_start_wheels_commands(self, static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        """
        Evaluate an action per-frame to determine whether it's done.

        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)

        :return: A list of commands to send to the build if the action is ongoing.
        """

        raise Exception()

    @final
    def _is_valid_ongoing(self, dynamic: MagnebotDynamic) -> bool:
        """
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)

        :return: True if the Magnebot isn't tipping over and didn't collide with something that should make it stop.
        """

        # Stop if the Magnebot is tipping.
        has_tipped, is_tipping = self._is_tipping(dynamic=dynamic)
        if has_tipped or is_tipping:
            self.status = ActionStatus.tipping
            return False
        # Stop if the Magnebot is colliding with something.
        elif self._is_collision(dynamic=dynamic):
            self.status = ActionStatus.collision
            return False
        else:
            return True

    @final
    def _is_collision(self, dynamic: MagnebotDynamic) -> bool:
        """
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)

        :return: True if there was a collision that according to the current detection rules means that the Magnebot needs to stop moving.
        """

        # Check environment collisions.
        if self._collision_detection.floor or self._collision_detection.walls:
            enters: List[int] = list()
            exits: List[int] = list()
            for object_id in dynamic.collisions_with_environment:
                for collision in dynamic.collisions_with_environment[object_id]:
                    if (self._collision_detection.floor and collision.floor) or \
                            (self._collision_detection.walls and not collision.floor):
                        if collision.state == "enter":
                            enters.append(object_id)
                        elif collision.state == "exit":
                            exits.append(object_id)
            # Ignore exit events.
            enters = [e for e in enters if e not in exits]
            if len(enters) > 0:
                return True
        # Check object collisions.
        if self._collision_detection.objects or len(self._collision_detection.include_objects) > 0:
            enters: List[Tuple[int, int]] = list()
            exits: List[Tuple[int, int]] = list()
            for object_ids in dynamic.collisions_with_objects:
                for collision in dynamic.collisions_with_objects[object_ids]:
                    object_id = object_ids[1]
                    # Accept the collision if the object is in the includes list or if it's not in the excludes list.
                    if object_id in self._collision_detection.include_objects or \
                            (self._collision_detection.objects and object_id not in
                             self._collision_detection.exclude_objects):
                        if collision.state == "enter":
                            enters.append(object_ids)
                        elif collision.state == "exit":
                            exits.append(object_ids)
            # Ignore exit events.
            enters: List[Tuple[int, int]] = [e for e in enters if e not in exits]
            if len(enters) > 0:
                return True
        return False

    @final
    def _set_brake_wheel_drives(self, static: MagnebotStatic) -> List[dict]:
        """
        :param static: [The static Magnebot data.](../magnebot_static.md)

        :return: A list of commands to set the wheel drives while braking.
        """

        commands = []
        for wheel_id in static.wheels.values():
            drive = static.joints[wheel_id].drives["x"]
            commands.append({"$type": "set_robot_joint_drive",
                             "joint_id": wheel_id,
                             "force_limit": drive.force_limit * 0.9,
                             "stiffness": drive.stiffness,
                             "damping": drive.damping,
                             "id": static.robot_id})
        return commands

    @final
    def _wheel_motion_complete(self, static: MagnebotStatic, resp: List[bytes]) -> bool:
        """
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param resp: The response from the build.

        :return: True if we received MagnebotWheels output data for this Magnebot.
        """

        # If the output data indicates the action was done, decide if it was a success.
        for i in range(len(resp) - 1):
            if OutputData.get_data_type_id(resp[i]) == "mwhe":
                mwhe = MagnebotWheels(resp[i])
                if mwhe.get_id() == static.robot_id:
                    if mwhe.get_success():
                        self.status = ActionStatus.success
                    return True
        return False

    @final
    def _wheels_are_turning(self, static: MagnebotStatic, dynamic: MagnebotDynamic) -> bool:
        """
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)

        :return: True if any of the wheels are turning.
        """

        for wheel in static.wheels:
            if dynamic.joints[static.wheels[wheel]].moving:
                return True
        return False

    @abstractmethod
    def _previous_was_same(self, previous: Action) -> bool:
        """
        :param previous: The previous action.

        :return: True if the previous action was the "same" as this action for the purposes of collision detection.
        """

        raise Exception()

    @abstractmethod
    def _get_ongoing_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic) -> List[dict]:
        """
        Get ongoing commands assuming that the body isn't being reset.

        :param resp: The response from the build.
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)

        :return: A list of ongoing commands.
        """

        raise Exception()
