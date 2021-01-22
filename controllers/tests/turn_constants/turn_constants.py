from pathlib import Path
from time import time
import numpy as np
from magnebot.test_controller import TestController, Magnebot
from magnebot.action_status import ActionStatus

"""
Calculate the time elapsed for a single turn action given a range of combinations of turn constants.
"""

if __name__ == "__main__":
    m = TestController()
    m._debug = False
    p = Path("../data/turn_constants.csv")
    if p.exists():
        p.unlink()
    header = "time,magic_number,outer_track,front\n"
    p.write_text(header)
    p = str(p.resolve())
    for magic_number in np.arange(start=2.4, stop=3.4, step=0.1):
        for outer_track in np.arange(start=1, stop=1.6, step=0.1):
            for front in np.arange(start=0.5, stop=1.5, step=0.1):
                # Set the turn constants.
                Magnebot.TURN_MAGIC_NUMBER = magic_number
                Magnebot.TURN_OUTER_TRACK = outer_track
                Magnebot.TURN_FRONT = front
                m.init_scene()
                # Turn the Magnebot. Record how long the turn takes.
                t0 = time()
                status = m.turn_by(45)
                if status != ActionStatus.success:
                    t1 = 1000
                else:
                    t1 = time() - t0
                # Write the result to disk.
                line = f"{t1},{round(magic_number, 3)},{round(outer_track, 3)},{round(front, 3)}"
                print(line)
                with open(p, "at") as f:
                    f.write(line + "\n")
    m.end()
