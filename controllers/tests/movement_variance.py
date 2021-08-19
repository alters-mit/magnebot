from typing import List, Union
import numpy as np
from magnebot import Magnebot, ActionStatus
from magnebot.collision_detection import CollisionDetection


class MovementVariance(Magnebot):
    """
    Calculate how much the Magnebot's path differs from the "canonical" path.
    Set `write=True` in the `run()` function to overwrite the canonical path.
    This controller can be used to determine how much the Magnebot API varies between machines.
    """

    def __init__(self, port: int = 1071):
        self.positions: List[np.array] = list()
        super().__init__(port=port)

    def move_by(self, distance: float, arrived_at: float = 0.1, stop_on_collision: Union[bool, CollisionDetection] = True) -> ActionStatus:
        status = super().move_by(distance=distance, arrived_at=arrived_at, stop_on_collision=stop_on_collision)
        self.positions.append(self.state.magnebot_transform.position)
        return status

    def run(self, write: bool = False) -> None:
        self.init_floorplan_scene(scene="1b", layout=1, room=4)
        self.move_to(target={"x": 9.976, "y": 0, "z": -0.97}, stop_on_collision=False, arrived_at=0.2)
        self.move_to(target={"x": 12.22, "y": 0, "z": -0.97}, stop_on_collision=False, aligned_at=1)
        self.move_to(target={"x": 11.46, "y": 0, "z": -1.11}, stop_on_collision=False)
        self.move_to(target={"x": 9.945, "y": 0, "z": -1.11}, stop_on_collision=False)
        self.move_by(2, stop_on_collision=False)
        self.move_by(-3, stop_on_collision=False)
        self.end()

        # Write the canonical positions to disk.
        if write:
            np.save("movement_variance", np.array(self.positions))
        else:
            canonical_positions = np.load("movement_variance.npy")
            diffs = []
            for position, canonical_position in zip(self.positions, canonical_positions):
                diff = np.linalg.norm(position - canonical_position)
                diffs.append(diff)
                print(diff)
            print("AVERAGE:", sum(diffs) / len(diffs))


if __name__ == "__main__":
    m = MovementVariance()
    m.run(write=False)
