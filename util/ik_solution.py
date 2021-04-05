from typing import List
import numpy as np
from tqdm import tqdm
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus, Arm
from magnebot.paths import IK_POSITIONS_PATH, IK_ORIENTATIONS_LEFT_PATH, IK_ORIENTATIONS_RIGHT_PATH
from magnebot.ik.orientation import ORIENTATIONS
from magnebot.constants import MAGNEBOT_RADIUS


class IKSolution(Magnebot):
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

    @staticmethod
    def get_positions(radius: float = 1.05, step: float = 0.1) -> np.array:
        """
        Get all positions that the Magnebot should try to reach for.

        :param radius: The radius of the circle.
        :param step: The spacing between each point in the cloud.

        :return: A numpy array of `[x, y, z]` positions.
        """

        positions: List[np.array] = list()
        # Get circles at each y value.
        for y in np.arange(0, 1.6, step=step):
            # Get a circle of positions defined by the radius.
            # Source: https://stackoverflow.com/a/49575743
            arr_x = np.arange(-radius, radius, step=step)
            arr_z = np.arange(-radius, radius, step=step)
            x, z = np.where((arr_x[:, np.newaxis]) ** 2 + arr_z ** 2 <= radius ** 2)
            origin = np.array([0, y, 0])
            for x, z in zip(arr_x[x], arr_z[z]):
                p = np.array([x, y, z])
                if np.linalg.norm(origin - p) > MAGNEBOT_RADIUS:
                    positions.append(p)
        return np.array(positions)

    def run(self) -> None:
        """
        Create a cloud of positions, reach for them, and store the orientation solution (if any).
        Save the results to disk.
        """

        # Get the positions.
        positions = IKSolution.get_positions()
        np.save(str(IK_POSITIONS_PATH.resolve())[:-4], positions)
        pbar = tqdm(total=len(positions) * 2)

        # Get solutions for each arm and save them as separate files.
        for arm, path in zip([Arm.left, Arm.right], [IK_ORIENTATIONS_LEFT_PATH, IK_ORIENTATIONS_RIGHT_PATH]):
            # Generate new orientation data.
            # These are the indices of an IK solution in `ORIENTATIONS` that resulted successful `reach_for()` actions.
            if not path.exists():
                orientations: np.array = np.full(len(positions), -2, dtype=int)
            # Load existing orientation data.
            else:
                orientations: np.array = np.load(str(path.resolve()))
            start_index: int = 0
            # Start at the next element in orientation that is -2.
            # This way, we can pause/resume data generation.
            # To generate new data, delete the orientation numpy files.
            got_start = False
            for i in range(len(orientations)):
                if orientations[i] == -2:
                    got_start = True
                    start_index = i
                    break
                pbar.update(1)
            # We already completed this file.
            if not got_start:
                continue
            # Reach for every position.
            for i in range(start_index, len(positions)):
                p = positions[i]
                # Ignore positions that are too far away.
                if np.linalg.norm(p - np.array([0, p[1], 0])) > 0.99:
                    orientations[i] = -1
                    np.save(str(path.resolve())[:-4], orientations)
                    pbar.update(1)
                    continue
                pbar.set_description(f"{p} {str(ORIENTATIONS[0])}")
                target = TDWUtils.array_to_vector3(p)
                # Always try (none, none) because it's the most-consistently "natural" motion and it's very fast.
                self.init_scene()
                # Iterate through each possible orientation.
                got_solution = False
                for j in range(len(ORIENTATIONS)):
                    pbar.set_description(f"{p} {str(ORIENTATIONS[j])}")
                    self.init_scene()
                    status = self.reach_for(target=target,
                                            arm=arm,
                                            orientation_mode=ORIENTATIONS[j].orientation_mode,
                                            target_orientation=ORIENTATIONS[j].target_orientation)
                    # Found a valid solution. Record it. Record this as the previous orientation.
                    if status == ActionStatus.success:
                        got_solution = True
                        orientations[i] = j
                        break
                # If we didn't find a solution, record this as -1.
                if not got_solution:
                    orientations[i] = -1
                    # Save the orientation data (don't do this for good solutions because it'll waste time).
                    np.save(str(path.resolve())[:-4], orientations)
                pbar.update(1)
            # Save the data.
            np.save(str(path.resolve())[:-4], orientations)
        # End the test.
        pbar.close()
        m.end()


if __name__ == "__main__":
    m = IKSolution()
    m.run()
