from typing import List
from pathlib import Path
from time import time
import numpy as np
from magnebot.test_controller import TestController, Magnebot
from magnebot.action_status import ActionStatus

"""
Calculate the time elapsed for a single turn action given a range of combinations of turn constants.
"""


class Result:
    def __init__(self, t: float, magic_number: float, outer_track: float, front: float, drift: float):
        self.t = t
        self.magic_number = magic_number
        self.outer_track = outer_track
        self.front = front
        self.drift = drift

    def get_line(self) -> str:
        return f"{self.t},{round(self.magic_number, 3)},{round(self.outer_track, 3)},{round(self.front, 3)}," \
               f"{round(self.drift, 3)}"


class TurnConstants(TestController):
    def run(self, angle: float):
        self._debug = False
        # Destroy the old data.
        p = Path(f"turn_constants/turn_constants_{angle}.csv")
        if p.exists():
            p.unlink()
        # Write the header of the spreadsheet to disk.
        header = "time,magic_number,outer_track,front,drift\n"
        p.write_text(header)
        print(f"Angle: {angle}")
        origin = np.array([0, 0, 0])
        results: List[Result] = list()
        best_index: int = -1
        # Iterate through many combinations of the turn constants.
        for magic_number in np.arange(start=2.1, stop=3.4, step=0.1):
            for outer_track in np.arange(start=1, stop=2.1, step=0.1):
                for front in np.arange(start=0.5, stop=1.5, step=0.1):
                    # Set the turn constants.
                    Magnebot._TURN_MAGIC_NUMBER = magic_number
                    Magnebot._TURN_OUTER_TRACK = outer_track
                    Magnebot._TURN_FRONT = front
                    self.init_scene()
                    # Turn the Magnebot.
                    t0 = time()
                    status = self.turn_by(angle)
                    # Ignore the result if the action failed.
                    if status != ActionStatus.success:
                        continue
                    else:
                        magnebot_position = self.state.magnebot_transform.position
                        magnebot_position[1] = 0
                        # Ignore the result if the Magnebot drifted too far away from the origin.
                        drift = np.linalg.norm(magnebot_position - origin)
                        # Get the time elapsed.
                        t1 = time() - t0
                        r = Result(t=t1,
                                   magic_number=round(magic_number, 3),
                                   outer_track=round(outer_track, 3),
                                   front=round(front, 3),
                                   drift=drift)
                        if best_index < 0:
                            best_index = 0
                        # Update the best known result.
                        else:
                            best = results[best_index]
                            if r.drift <= best.drift and r.t <= best.t:
                                best_index = len(results)
                                print(r.get_line())
                        results.append(r)
        best_result: Result = results[best_index]
        print("Best result: ")
        print(best_result.get_line())
        with open(str(p.resolve()), "at") as f:
            f.write(best_result.get_line() + "\n")


if __name__ == "__main__":
    m = TurnConstants()

    for a in np.arange(10, 180, step=10):
        m.run(angle=a)
    m.end()

