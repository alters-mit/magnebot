from tdw.tdw_utils import TDWUtils
from magnebot.magnebot_controller import Magnebot
from magnebot.action_status import ActionStatus


class TestController(Magnebot):
    """
    This controller will load an empty test room instead of a highly detailed scene.

    This can be useful for testing the Magnebot.
    """

    def __init__(self, port: int = 1071, screen_width: int = 256, screen_height: int = 256, skip_frames: int = 10):
        super().__init__(port=port, launch_build=False, screen_height=screen_height, screen_width=screen_width,
                         debug=True, skip_frames=skip_frames)

    def init_scene(self, scene: str = None, layout: int = None, room: int = None) -> ActionStatus:
        """
        **Always call this function before any other API calls.** Initialize an empty test room with a Magnebot.

        You can safely call `init_scene()` more than once to reset the simulation.

        ```python
        from magnebot import TestController

        m = TestController()
        m.init_scene()

        # Your code here.
        ```

        Possible [return values](action_status.md):

        - `success`
        """

        self._clear_data()

        commands = [{"$type": "load_scene",
                     "scene_name": "ProcGenScene"},
                    TDWUtils.create_empty_room(12, 12)]
        commands.extend(self._get_scene_init_commands(magnebot_position={"x": 0, "y": 0, "z": 0}))
        resp = self.communicate(commands)
        self._cache_static_data(resp=resp)
        # Wait for the Magnebot to reset to its neutral position.
        self._do_arm_motion()
        self._end_action()
        return ActionStatus.success
