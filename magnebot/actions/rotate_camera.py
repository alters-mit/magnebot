from typing import List
import numpy as np
from magnebot.action_status import ActionStatus
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.actions.camera_action import CameraAction
from magnebot.image_frequency import ImageFrequency


class RotateCamera(CameraAction):
    """
    Rotate the Magnebot's camera by the (roll, pitch, yaw) axes.

    Each axis of rotation is constrained (see `Magnebot.CAMERA_RPY_CONSTRAINTS`).

    | Axis | Minimum | Maximum |
    | --- | --- | --- |
    | roll | -55 | 55 |
    | pitch | -70 | 70 |
    | yaw | -85 | 85 |
    """

    def __init__(self, roll: float, pitch: float, yaw: float, camera_rpy: np.array,  static: MagnebotStatic, dynamic: MagnebotDynamic,
                 image_frequency: ImageFrequency):
        """
        :param roll: The roll angle in degrees.
        :param pitch: The pitch angle in degrees.
        :param yaw: The yaw angle in degrees.
        :param camera_rpy: The current camera angles.
        :param static: [The static Magnebot data.](../magnebot_static.md)
        :param dynamic: [The dynamic Magnebot data.](../magnebot_dynamic.md)
        :param image_frequency: [How image data will be captured during the image.](../image_frequency.md)
        """

        super().__init__(static=static, dynamic=dynamic, image_frequency=image_frequency)
        """:field
        Rotate the camera by these delta (roll, pitch, yaw). This will be clamped to the maximum RPY values.
        """
        self.deltas: List[float] = [roll, pitch, yaw]
        # Clamp the rotation.
        self.clamped: bool = False
        for i in range(len(camera_rpy)):
            a = camera_rpy[i] + self.deltas[i]
            if np.abs(a) > RotateCamera.CAMERA_RPY_CONSTRAINTS[i]:
                self.clamped = True
                # Clamp the angle to either the minimum or maximum bound.
                if a > 0:
                    self.deltas[i] = RotateCamera.CAMERA_RPY_CONSTRAINTS[i] - camera_rpy[i]
                else:
                    self.deltas[i] = -RotateCamera.CAMERA_RPY_CONSTRAINTS[i] - camera_rpy[i]
        for i in range(len(camera_rpy)):
            camera_rpy[i] += self.deltas[i]

    def get_initialization_commands(self, resp: List[bytes]) -> List[dict]:
        commands = []
        for angle, axis in zip(self.deltas, ["roll", "pitch", "yaw"]):
            commands.append({"$type": "rotate_sensor_container_by",
                             "axis": axis,
                             "angle": float(angle),
                             "avatar_id": self.static.avatar_id})
        return commands

    def set_status_after_initialization(self) -> None:
        if self.clamped:
            self.status = ActionStatus.clamped_camera_rotation
        else:
            self.status = ActionStatus.success


