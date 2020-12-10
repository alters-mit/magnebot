from tdw.tdw_utils import TDWUtils
from magnebot.magnebot_controller import Magnebot
from magnebot.action_status import ActionStatus


class TestController(Magnebot):
    """
    This controller will load an empty test room instead of a highly detailed scene.

    This can be useful for testing the Magnebot.
    """

    def __init__(self, port: int = 1071, screen_width: int = 256, screen_height: int = 256):
        super().__init__(port=port, launch_build=False, screen_height=screen_height, screen_width=screen_width,
                         debug=True)

    def init_scene(self, scene: str = None, layout: int = None, room: int = -1) -> ActionStatus:
        """
        Initialize an empty test room with a Magnebot. The simulation will advance through frames until the Magnebot's body is in its neutral position.

        This function must be called before any other API calls.

        ```python
        from magnebot import TestController

        m = TestController()
        m.init_scene()

        # Your code here.
        ```

        You can safely call `init_scene()` more than once to reset the simulation.

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_bend` (Technically this is _possible_, but it shouldn't ever happen.)
        """

        commands = [{"$type": "load_scene",
                     "scene_name": "ProcGenScene"},
                    TDWUtils.create_empty_room(12, 12)]
        commands.extend(self._get_scene_init_commands(magnebot_position={"x": 0, "y": 0, "z": 0}))
        resp = self.communicate(commands)
        self._cache_static_data(resp=resp)
        # Wait for the Magnebot to reset to its neutral position.
        status = self._do_arm_motion()
        self._end_action()
        return status
