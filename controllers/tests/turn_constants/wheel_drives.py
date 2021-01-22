from time import time
from pathlib import Path
import numpy as np
from magnebot.test_controller import TestController
from magnebot.action_status import ActionStatus


class WheelDrives(TestController):
    def set_drives(self, d: float, s: float) -> None:
        self._start_action()
        self._set_wheel_drive(stiffness=float(s), damping=float(d))
        self._end_action()


if __name__ == "__main__":
    m = WheelDrives()
    m._debug = False
    p = Path("../data/wheel_drives.csv")
    if p.exists():
        p.unlink()
    header = "time,damper,stiffness\n"
    p.write_text(header)
    path = str(p.resolve())
    for damping in np.arange(start=100, stop=300, step=10):
        for stiffness in np.arange(start=500, stop=2000, step=50):
            m.init_scene()
            m.set_drives(d=damping, s=stiffness)
            t0 = time()
            status = m.turn_by(45)
            if status == ActionStatus.success:
                t1 = time() - t0
            else:
                t1 = 1000
            line = f"{t1},{damping},{stiffness}"
            print(line)
            with open(path, "at") as f:
                f.write(line + "\n")

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
    print("")
    print(min_line)
