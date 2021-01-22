from typing import List
from time import time
from magnebot.test_controller import TestController


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
        for i in range(100):
            if i > 0 and i % 5 == 0:
                direction *= -1
            t0 = time()
            self.move_by(1 * direction)
            times.append(time() - t0)
        return sum(times) / len(times)

    def turn_fps(self) -> float:
        self.init_scene()
        times: List[float] = list()
        for i in range(100):
            t0 = time()
            self.turn_by(45)
            times.append(time() - t0)
        return sum(times) / len(times)


if __name__ == "__main__":
    m = Benchmark()
    print(f"turn_by(): {m.turn_fps()}")
    print(f"move_by(): {m.move_fps()}")

    m.end()
