from typing import List
from time import time
from magnebot.test_controller import TestController
from magnebot import Arm


class Benchmark(TestController):
    """
    Run simple benchmarks for the average speed of an action.

    In an actual use-case, the action will usually be somewhat slower because of the complexity of the scene.
    """

    def __init__(self, port: int = 1071, screen_width: int = 256, screen_height: int = 256):
        super().__init__(port=port, screen_height=screen_height, screen_width=screen_width)
        self._debug = False

    def move_fps(self) -> float:
        """
        Benchmark the speed of `move_by()`.

        :return: The average time elapsed per action.
        """

        self.init_scene()
        times: List[float] = list()
        direction = 1
        for i in range(20):
            if i > 0 and i % 5 == 0:
                direction *= -1
            t0 = time()
            self.move_by(1 * direction)
            times.append(time() - t0)
        return sum(times) / len(times)

    def turn_fps(self) -> float:
        """
        Benchmark the speed of `turn_by()`.

        :return: The average time elapsed per action.
        """

        self.init_scene()
        times: List[float] = list()
        for i in range(20):
            t0 = time()
            self.turn_by(45)
            t1 = time() - t0
            print(t1)
            times.append(t1)
        return sum(times) / len(times)

    def step_fps(self) -> None:
        print("| Skipped frames | FPS |\n| --- | --- |")
        for frames in [0, 5, 10, 15, 20]:
            self.init_scene()
            self._skip_frames = frames
            times: List[float] = list()
            direction = 1
            arm = Arm.left
            for i in range(20):
                if i > 0 and i % 5 == 0:
                    direction *= -1
                t0 = time()
                self.move_by(0.5 * direction)
                self.reach_for(target={"x": 0.2 * direction, "y": 0.4, "z": 0.5}, arm=arm, absolute=False)
                self.reset_arm(arm=arm)
                times.append(time() - t0)
            print(f"| {frames} | {sum(times) / len(times)} |")


if __name__ == "__main__":
    m = Benchmark()
    print(f"turn_by(): {m.turn_fps()}")
    print(f"move_by(): {m.move_fps()}")
    m.step_fps()


    m.end()
