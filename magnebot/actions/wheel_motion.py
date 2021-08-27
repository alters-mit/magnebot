from typing import List, Tuple
from abc import ABC, abstractmethod
from overrides import final
from magnebot.action_status import ActionStatus
from magnebot.actions.motion import Motion
from magnebot.actions.action import Action
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.collision_detection import CollisionDetection
from magnebot.constants import DEFAULT_WHEEL_FRICTION


class WheelMotion(Motion, ABC):
    """
    A motion action involving the Magnebot's wheels.
    """

    def __init__(self, static: MagnebotStatic, dynamic: MagnebotDynamic, collision_detection: CollisionDetection,
                 previous: Action = None):
        """
        :param static: [The static Magnebot data.](magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](magnebot_dynamic.md)
        :param collision_detection: [The collision detection rules.](collision_detection.md)
        :param previous: The previous action, if any.
        """

        super().__init__(static=static, dynamic=dynamic)
        # My collision detection rules.
        self._collision_detection: CollisionDetection = collision_detection
        # Immediately end the action if we're currently tipping.
        has_tipped, is_tipping = self._is_tipping()
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

    def get_initialization_commands(self, resp: List[bytes]) -> List[dict]:
        commands: List[dict] = list()
        # Make the robot moveable.
        if self.dynamic.immovable:
            commands.append({"$type": "set_immovable",
                             "id": self.static.robot_id,
                             "immovable": False})
        # Reset the drive values.
        for wheel_id in self.static.wheels.values():
            drive = self.static.joints[wheel_id].drives["x"]
            commands.extend([{"$type": "set_robot_joint_drive",
                              "joint_id": wheel_id,
                              "force_limit": drive.force_limit,
                              "stiffness": drive.stiffness,
                              "damping": drive.damping,
                              "id": self.static.robot_id},
                             {"$type": "set_robot_joint_friction",
                              "joint_id": wheel_id,
                              "friction": DEFAULT_WHEEL_FRICTION,
                              "id": self.static.robot_id}])
        return commands

    @final
    def _is_valid_ongoing(self) -> bool:
        """
        :return: True if the Magnebot isn't tipping over and didn't collide with something that should make it stop.
        """

        # Stop if the Magnebot is tipping.
        has_tipped, is_tipping = self._is_tipping()
        if has_tipped or is_tipping:
            self.status = ActionStatus.tipping
            return False
        # Stop if the Magnebot is colliding with something.
        elif self._is_collision():
            self.status = ActionStatus.collision
            return False
        else:
            return True

    @final
    def _is_collision(self) -> bool:
        """
        :return: True if there was a collision that according to the current detection rules means that the Magnebot needs to stop moving.
        """

        # Check environment collisions.
        if self._collision_detection.floor or self._collision_detection.walls:
            enters: List[int] = list()
            exits: List[int] = list()
            for object_id in self.dynamic.collisions_with_environment:
                for collision in self.dynamic.collisions_with_environment[object_id]:
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
            for object_ids in self.dynamic.collisions_with_objects:
                for collision in self.dynamic.collisions_with_objects[object_ids]:
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
    def _stop_wheels(self) -> List[dict]:
        """
        Stop wheel movement.

        :return: A list of commands to stop the wheels.
        """

        commands = []
        for wheel in self.static.wheels:
            # Set the target of each wheel to its current position.
            commands.append({"$type": "set_revolute_target",
                             "id": self.static.robot_id,
                             "target": float(self.dynamic.joints[self.static.wheels[wheel]].angles[0]),
                             "joint_id": self.static.wheels[wheel]})
        return commands

    @final
    def _set_brake_wheel_drives(self) -> List[dict]:
        """
        :return: A list of commands to set the wheel drives while braking.
        """

        commands = []
        for wheel_id in self.static.wheels.values():
            drive = self.static.joints[wheel_id].drives["x"]
            commands.append({"$type": "set_robot_joint_drive",
                             "joint_id": wheel_id,
                             "force_limit": drive.force_limit * 0.9,
                             "stiffness": drive.stiffness,
                             "damping": drive.damping,
                             "id": self.static.robot_id})
        return commands

    @abstractmethod
    def _previous_was_same(self, previous: Action) -> bool:
        """
        :param previous: The previous action.

        :return: True if the previous action was the "same" as this action for the purposes of collision detection.
        """

        raise Exception()
