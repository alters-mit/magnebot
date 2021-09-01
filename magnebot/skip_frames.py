from typing import List
from tdw.add_ons.add_on import AddOn


class SkipFrames(AddOn):
    """
    Skip n frames per communciate() call.
    """

    def __init__(self, num_frames: int):
        """
        :param num_frames: Skip this many frames per communicate() call.
        """

        super().__init__()
        self._commands: List[dict] = [{"$type": "step_physics",
                                       "frames": num_frames}]

    def get_initialization_commands(self) -> List[dict]:
        return []

    def on_send(self, resp: List[bytes]) -> None:
        self.commands.extend(self._commands)
