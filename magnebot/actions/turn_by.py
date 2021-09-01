from magnebot.actions.action import Action
from magnebot.actions.turn import Turn
from magnebot.actions.image_frequency import ImageFrequency
from magnebot.magnebot_static import MagnebotStatic
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.collision_detection import CollisionDetection


class TurnBy(Turn):
    def __init__(self, angle: float, static: MagnebotStatic, dynamic: MagnebotDynamic, image_frequency: ImageFrequency,
                 collision_detection: CollisionDetection, aligned_at: float = 1, previous: Action = None):
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
                "brake_angle": Turn._BRAKE_ANGLE}
