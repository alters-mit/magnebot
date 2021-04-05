from time import time
from typing import List
from magnebot import Magnebot


class FloorplanBenchmark(Magnebot):
    """
    Benchmark how global values affect speed.
    """

    def run(self, reflection_probe: bool = True, post_process: bool = True) -> float:
        """
        Run the benchmark.

        :return: The total time elapsed.
        """

        self.init_floorplan_scene(scene="5a", layout=0, room=2)

        # Set global values.
        self.communicate([{"$type": "enable_reflection_probes",
                           "enable": reflection_probe},
                          {"$type": "set_post_process",
                           "value": post_process}])
        self._end_action()

        times: List[float] = list()
        direction = 1
        for i in range(20):
            if i > 0 and i % 5 == 0:
                direction *= -1
            t0 = time()
            self.move_by(0.5 * direction)
            times.append(time() - t0)
        return sum(times) / len(times)


if __name__ == "__main__":
    m = FloorplanBenchmark()
    print("| Test | Time elapsed |\n| --- | --- |")
    t = m.run()
    print(f"| Default | {t} |")
    t = m.run(reflection_probe=False)
    print(f"| Without reflection probes | {t} |")
    t = m.run(post_process=False)
    print(f"| Without post-process | {t} |")
    t = m.run(post_process=False, reflection_probe=False)
    print(f"| Without post-process and without reflection probes | {t} |")
    m.end()
