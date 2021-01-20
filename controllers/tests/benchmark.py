from typing import List
from time import time
from magnebot.test_controller import TestController


class Benchmark(TestController):
    """
    Run simple benchmarks for the average speed of an action.

    In an actual use-case, the action will usually be somewhat slower because of the complexity of the scene.
    """

    def move_fps(self) -> float:
        """
        Benchmark the speed of `move_by()`.

        :return: The average time elapsed per action.
        """

        self._debug = False
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


if __name__ == "__main__":
    m = Benchmark()
    print(f"move_by(): {m.move_fps()}")
    m.end()
