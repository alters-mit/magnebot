import numpy as np
from magnebot import MagnebotController, ActionStatus

"""
Test Magnebot camera rotation.
"""

if __name__ == "__main__":
    m = MagnebotController()
    m.init_scene()
    status = m.rotate_camera(roll=0, pitch=0, yaw=0)
    # No rotation.
    assert np.linalg.norm(m.magnebot.camera_rpy) == 0
    assert status == ActionStatus.success, status
    # Pitch.
    status = m.rotate_camera(roll=0, pitch=45, yaw=0)
    assert status == ActionStatus.success, status
    # Clamped pitch.
    status = m.rotate_camera(pitch=90)
    assert status == ActionStatus.clamped_camera_rotation, status
    assert m.magnebot.camera_rpy[0] == 0 and m.magnebot.camera_rpy[1] == 70 and m.magnebot.camera_rpy[2] == 0, m.magnebot.camera_rpy
    # Yaw.
    status = m.rotate_camera(yaw=-50)
    assert status == ActionStatus.success, status
    assert m.magnebot.camera_rpy[0] == 0 and m.magnebot.camera_rpy[1] == 70 and m.magnebot.camera_rpy[2] == -50, m.magnebot.camera_rpy
    # Clamp.
    status = m.rotate_camera(yaw=-50)
    assert status == ActionStatus.clamped_camera_rotation, status
    assert m.magnebot.camera_rpy[0] == 0 and m.magnebot.camera_rpy[1] == 70 and m.magnebot.camera_rpy[2] == -85, m.magnebot.camera_rpy
    # Reset.
    status = m.reset_camera()
    assert status == ActionStatus.success, status
    assert np.linalg.norm(m.magnebot.camera_rpy) == 0
    # Multiaxis.
    status = m.rotate_camera(roll=90, pitch=-30, yaw=87)
    assert status == ActionStatus.clamped_camera_rotation, status
    assert m.magnebot.camera_rpy[0] == 55 and m.magnebot.camera_rpy[1] == -30 and m.magnebot.camera_rpy[2] == 85, m.magnebot.camera_rpy
    m.end()
