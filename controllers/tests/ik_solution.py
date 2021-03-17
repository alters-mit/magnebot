import numpy as np
from tqdm import tqdm
from tdw.tdw_utils import TDWUtils
from magnebot import TestController, ActionStatus, Arm
from magnebot.paths import IK_ORIENTATIONS_LEFT_PATH, IK_ORIENTATIONS_RIGHT_PATH
from magnebot.ik.orientation import ORIENTATIONS


class IKSolution(TestController):
    """
    Create a cloud of positions as cylinders of increasing radius around the Magnebot.
    For every position, try to `reach_for()` the target with every `Orientation`.
    When `reach_for()` returns success, store the index of the successful `Orientation`.
    If no `Orientation` resulted in success, store -1.
    These values will be used by all IK Magnebot actions to get a best-guess target orientation and orientation mode.
    """

    def __init__(self, port: int = 1071):
        # Start the controller. Turn off debug mode.
        super().__init__(port=port, screen_width=128, screen_height=128)
        self._debug = False

    def get_positions(self):
        # Source: https://stackoverflow.com/a/49575743
        x_ = np.arange(-radius - 1, radius + 1, dtype=int)
        y_ = np.arange(-radius - 1, radius + 1, dtype=int)
        x, y = np.where((x_[:, np.newaxis]) ** 2 + (y_) ** 2 <= radius ** 2)

    def run(self) -> None:
        """
        Create a cloud of positions, reach for them, and store the orientation solution (if any).
        Save the results to disk.
        """

        # Get positions around the Magnebot.
        positions = list()
        origin = np.array([0, 0, 0])
        # Get a range of radii from the Magnebot.
        for r in np.arange(0.3, 1.2, step=0.1):
            # Get the number of positions per ring. The constant is derived from: 10 objects if r == 0.7
            num_positions = int(14.285714285714286 * r)
            d_theta = 360 / num_positions
            # Get each ring at increasing y values.
            for y in np.arange(0, 1.6, step=0.1):
                # Get a ring of positions.
                theta = 0
                pos = np.array([r, 0, 0])
                for j in range(num_positions):
                    position = TDWUtils.rotate_position_around(origin=origin, position=pos, angle=theta)
                    position[1] = y
                    positions.append(position)
                    theta += d_theta
        positions: np.array = np.array(positions)
        pbar = tqdm(total=len(positions) * 2)

        # Get solutions for each arm and save them as separate files.
        for arm, path in zip([Arm.left, Arm.right], [IK_ORIENTATIONS_LEFT_PATH, IK_ORIENTATIONS_RIGHT_PATH]):
            # The indices of an IK solution in `ORIENTATIONS` that resulted successful `reach_for()` actions.
            orientations: np.array = np.zeros(len(positions))
            # Always try the previous orientation that worked first.
            previous_orientation: int = -1
            # Reach for every position.
            for i, p in enumerate(positions):
                target = TDWUtils.array_to_vector3(p)
                # Try the previous orientation. If it works, record it and continue to the next position.
                if previous_orientation != -1:
                    self.init_scene()
                    status = self.reach_for(target=target,
                                            arm=arm,
                                            orientation_mode=ORIENTATIONS[previous_orientation].orientation_mode,
                                            target_orientation=ORIENTATIONS[previous_orientation].target_orientation)
                    if status == ActionStatus.success:
                        orientations[i] = previous_orientation
                        pbar.update(1)
                        continue
                # Iterate through each possible orientation.
                got_solution = False
                for j in range(len(ORIENTATIONS)):
                    self.init_scene()
                    status = self.reach_for(target=target,
                                            arm=arm,
                                            orientation_mode=ORIENTATIONS[j].orientation_mode,
                                            target_orientation=ORIENTATIONS[j].target_orientation)
                    # Found a valid solution. Record it. Record this as the previous orientation.
                    if status == ActionStatus.success:
                        got_solution = True
                        previous_orientation = j
                        orientations[i] = j
                        break
                # If we didn't find a solution, record this as -1.
                # Either way, continue to the next position.
                if not got_solution:
                    previous_orientation = -1
                    orientations[i] = -1
                pbar.update(1)
            # Store the data.
            ik = np.zeros(shape=(len(positions), 4))
            for i, p, o in zip(range(len(positions)), positions, orientations):
                # Values are: x, y, z, orientation
                ik[i] = np.array([p[0], p[1], p[2], o])
            # Save the data.
            np.save(str(path.resolve())[:-4], ik)
        # End the test.
        pbar.close()
        m.end()


if __name__ == "__main__":
    m = IKSolution()
    m.run()
