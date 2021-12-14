from typing import List
import numpy as np
from magnebot.action_status import ActionStatus
from magnebot.magnebot_dynamic import MagnebotDynamic
from magnebot.magnebot_static import MagnebotStatic
from magnebot.image_frequency import ImageFrequency
from magnebot.actions.camera_action import CameraAction


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

    """:class_var
    The camera roll, pitch, yaw constraints in degrees.
    """
    CAMERA_RPY_CONSTRAINTS: List[float] = [55, 70, 85]

    def __init__(self, roll: float, pitch: float, yaw: float, camera_rpy: np.array):
        """
        :param roll: The roll angle in degrees.
        :param pitch: The pitch angle in degrees.
        :param yaw: The yaw angle in degrees.
        :param camera_rpy: The current camera angles.
        """

        super().__init__()
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
        """:field
        The adjust camera roll, pitch, yaw angles.
        """
        self.camera_rpy: np.array = np.array(camera_rpy[:])
        for i in range(len(camera_rpy)):
            self.camera_rpy[i] += self.deltas[i]

    def get_initialization_commands(self, resp: List[bytes], static: MagnebotStatic, dynamic: MagnebotDynamic,
                                    image_frequency: ImageFrequency) -> List[dict]:
        commands = super().get_initialization_commands(resp=resp, static=static, dynamic=dynamic,
                                                       image_frequency=image_frequency)
        for angle, axis in zip(self.deltas, ["roll", "pitch", "yaw"]):
            commands.append({"$type": "rotate_sensor_container_by",
                             "axis": axis,
                             "angle": float(angle),
                             "avatar_id": static.avatar_id})
        return commands

    def set_status_after_initialization(self) -> None:
        if self.clamped:
            self.status = ActionStatus.clamped_camera_rotation
        else:
            self.status = ActionStatus.success
