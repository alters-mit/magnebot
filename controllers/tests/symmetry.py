from tdw.output_data import StaticRobot
from magnebot import TestController, Arm
from magnebot.action_status import ActionStatus
from magnebot.util import get_data
from magnebot.scene_state import SceneState


class Symmetry(TestController):
    """
    Test the symmetry of the Magnebot's parts before and after moving.
    """


if __name__ == "__main__":
    m = Symmetry(launch_build=False)
    m.init_scene()
    # Bend both arms to mirrored targets.
    for direction, arm in zip([1, -1], [Arm.left, Arm.right]):
        status = m.reach_for(target={"x": 0.2 * direction, "y": 0.4, "z": 0.5}, arm=arm)
        assert status == ActionStatus.success, f"{arm}, {status}"
    # Reset the arms.
    m.reset_arms()
    m.end()
