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
    # Destroy the old data.
    p = Path("data/turn_constants.csv")
    if p.exists():
        p.unlink()
    # Write the header of the spreadsheet to disk.
    header = "time,magic_number,outer_track,front,drift\n"
    p.write_text(header)
    path = str(p.resolve())

    origin = np.array([0, 0, 0])
    # Iterate through many combinations of the turn constants.
    for magic_number in np.arange(start=2.4, stop=3.4, step=0.1):
        for outer_track in np.arange(start=1, stop=2.1, step=0.1):
            for front in np.arange(start=0.5, stop=1.5, step=0.1):
                # Set the turn constants.
                Magnebot._TURN_MAGIC_NUMBER = magic_number
                Magnebot._TURN_OUTER_TRACK = outer_track
                Magnebot._TURN_FRONT = front
                m.init_scene()
                # Turn the Magnebot.
                t0 = time()
                status = m.turn_by(120)
                # Ignore the result if the action failed.
                if status != ActionStatus.success:
                    continue
                else:
                    magnebot_position = m.state.magnebot_transform.position
                    magnebot_position[1] = 0
                    # Ignore the result if the Magnebot drifted too far away from the origin.
                    drift = np.linalg.norm(magnebot_position - origin)
                    if drift > 0.025:
                        continue
                    # Success!
                    else:
                        # Get the time elapsed.
                        t1 = time() - t0
                        # Write the result to disk.
                        line = f"{t1},{round(magic_number, 3)},{round(outer_track, 3)},{round(front, 3)}," \
                               f"{round(drift, 3)}"
                        print(line)
                        with open(path, "at") as f:
                            f.write(line + "\n")
    m.end()

    # Print the shortest time.
    txt = p.read_text()
    lines = txt.split("\n")[1:]
    min_time = 100000
    min_line = ""
    for line in lines:
        q = line.split(",")[0]
        if q == "":
            continue
        t = float(q)
        if t < min_time:
            min_time = t
            min_line = line
    print(min_line)

