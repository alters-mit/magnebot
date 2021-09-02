from magnebot.actions.action import Action
from magnebot.actions.turn import Turn
from magnebot.image_frequency import ImageFrequency
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.collision_detection import CollisionDetection


class TurnBy(Turn):
    """
    Turn the Magnebot by an angle.

    While turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.
    """

    def __init__(self, angle: float, static: MagnebotStatic, dynamic: MagnebotDynamic, image_frequency: ImageFrequency,
                 collision_detection: CollisionDetection, aligned_at: float = 1, previous: Action = None):
        """
        :param angle: The target angle in degrees. Positive value = clockwise turn.
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        :param image_frequency: [How image data will be captured during the image.](../image_frequency.md)
        :param collision_detection: [The collision detection rules.](../collision_detection.md)
        :param aligned_at: If the difference between the current angle and the target angle is less than this value, then the action is successful.
        :param previous: The previous action, if any.
        """

        self.__angle: float = angle
        super().__init__(aligned_at=aligned_at, static=static, dynamic=dynamic, collision_detection=collision_detection,
                         previous=previous, image_frequency=image_frequency)

    def _get_angle(self) -> float:
        return self.__angle

    def _get_turn_command(self) -> dict:
        return {"$type": "set_magnebot_wheels_during_turn_by",
                "angle": self._angle,
                "origin": self._initial_forward_vector,
                "arrived_at": self._aligned_at,
                "minimum_friction": self._minimum_friction,
                "brake_angle": Turn._BRAKE_ANGLE,
                "id": self.static.robot_id}
