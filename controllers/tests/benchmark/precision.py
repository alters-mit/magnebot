from typing import List
from time import time
from magnebot import Magnebot, ActionStatus


class Precision(Magnebot):
    """
    Test the precision of the Magnebot's moving and turning.
    """

    NUM_TRIALS: int = 20

    def turn(self):
        for aligned_at in [3, 1, 0.5, 0.2]:
            times: List[float] = list()
            for i in range(Precision.NUM_TRIALS):
                self.init_scene()
                t0 = time()
                status = self.turn_by(123, aligned_at=aligned_at)
                if status == ActionStatus.success:
                    times.append(time() - t0)
                else:
                    times.append(1000)
            print(f"| {aligned_at} | {sum(times) / len(times)} |")

    def move(self):
        for arrived_at in [0.3, 0.1, 0.02, 0.01]:
            times: List[float] = list()
            for i in range(Precision.NUM_TRIALS):
                self.init_scene()
                t0 = time()
                status = self.move_by(2, arrived_at=arrived_at)
                if status == ActionStatus.success:
                    times.append(time() - t0)
                else:
                    times.append(1000)
            print(f"| {arrived_at} | {sum(times) / len(times)} |")


if __name__ == "__main__":
    m = Precision()
    print("| `aligned_at` | Average time elapsed |\n| --- | --- |")
    m.turn()
    print("")
    print("| `arrived_at` | Average time elapsed |\n| --- | --- |")
    m.move()
    m.end()
