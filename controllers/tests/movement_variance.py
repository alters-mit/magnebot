from typing import List
import numpy as np
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus


class MovementVariance(Magnebot):
    """
    Calculate how much the Magnebot's path differs from the "canonical" path.
    Set `write=True` in the `run()` function to overwrite the canonical path.
    This controller can be used to determine how much the Magnebot API varies between machines.
    """

    # This is a pre-calculated path that the Magnebot will use to move between rooms.
    PATH: np.array = np.array([[6.396355, 0, -2.465405],
                               [5.41636, 0, -1.4854207],
                               [4.615, 0, -0.9954208],
                               [3.946356, 0, 0.66],
                               [0.4, 0, 0.66],
                               [0.02635, 0, -1.975]])

    def init_scene(self) -> ActionStatus:
        return self._init_scene(scene=[{"$type": "load_scene", "scene_name": "ProcGenScene"},
                                       TDWUtils.create_empty_room(20, 20)])

    def run(self, write: bool = False) -> None:
        self.init_scene()
        positions: List[np.array] = [self.state.magnebot_transform.position]
        for waypoint in MovementVariance.PATH:
            self._next_frame_commands.append({"$type": "add_position_marker",
                                              "position": TDWUtils.array_to_vector3(waypoint)})
            self.move_to(TDWUtils.array_to_vector3(waypoint))
            positions.append(self.state.magnebot_transform.position)
        self.end()
        # Write the canonical positions to disk.
        if write:
            np.save("movement_variance", np.array(positions))
        else:
            canonical_positions = np.load("movement_variance.npy")
            diffs = []
            for position, canonical_position in zip(positions, canonical_positions):
                diff = np.linalg.norm(position - canonical_position)
                diffs.append(diff)
                print(diff)
            print("AVERAGE:", sum(diffs) / len(diffs))


if __name__ == "__main__":
    m = MovementVariance()
    m.run(write=False)
