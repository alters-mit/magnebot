from typing import Tuple
from time import time
import numpy as np
from tqdm import tqdm
from tdw.tdw_utils import TDWUtils
from magnebot import TestController, ActionStatus, Arm
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.ik.orientation_mode import OrientationMode


class ReachFor(TestController):
    """
    Reach for random targets using the automated IK orientation system.
    If the action succeeds OR if the action fails but we expected it to fail, record the trial as a "correct guess".
    A high the percentage of correct guesses indicates that the automated IK orientation system tends to work.
    """

    def __init__(self, port: int = 1071, generate_new_positions: bool = False, arrived_at: float = 0.125):
        super().__init__(port=port)
        self._debug = False
        # Load the positions.
        if generate_new_positions:
            self.positions: np.array = ReachFor.get_positions()
        else:
            self.positions: np.array = np.load("ik_positions.npy")
        self.arrived_at: float = arrived_at

    @staticmethod
    def get_positions(num: int = 100, random_seed: int = 0, write: bool = True) -> np.array:
        """
        :param num: The number of positions.
        :param random_seed: The random seed used to generate the positions.
        :param write: If True, write the array to disk.

        :return: A numpy array of random positions within the pre-calculated range of the Magnebot.
        """

        rng = np.random.RandomState(random_seed)
        positions = np.zeros(shape=(num, 3))
        for i in range(num):
            positions[i] = np.array([rng.uniform(-1.05, 1.05),
                                     rng.uniform(0, 1.5),
                                     rng.uniform(-1.05, 1.05)])
        if write:
            np.save("ik_positions", positions)
        return positions

    def run_none(self) -> float:
        """
        Reach for every random position using (none, none) as `target_orientation` and `orientation_mode` parameters.
        Compare this to the results of `run_auto` to determine how effective the IK orientation solver is.

        :return: The percentage of `reach_for()` actions that were successful.
        """

        pbar = tqdm(total=len(self.positions) * 2)
        successes: int = 0
        for arm in [Arm.left, Arm.right]:
            for i in range(len(self.positions)):
                # Reload the scene.
                self.init_scene()
                # Reach for the target, using (none, none).
                status = self.reach_for(target=TDWUtils.array_to_vector3(self.positions[i]),
                                        arm=arm,
                                        target_orientation=TargetOrientation.none,
                                        orientation_mode=OrientationMode.none,
                                        arrived_at=self.arrived_at)
                # We guessed the IK solution correctly if the action was successful.
                if status == ActionStatus.success or status == ActionStatus.cannot_reach:
                    successes += 1
                pbar.update(1)
        pbar.close()
        return successes / (len(self.positions) * 2)

    def get_ik_orientation_speed(self) -> float:
        """
        :return: The average speed of `_get_ik_orientation()`.
        """

        orientation_times = list()
        for arm in [Arm.left, Arm.right]:
            for i in range(len(self.positions)):
                # Get the orientation.
                t0 = time()
                self._get_ik_orientation(arm=arm,
                                         target=self.positions[i])
                orientation_times.append(time() - t0)
        return sum(orientation_times) / len(orientation_times)

    def no_orientation_guess(self) -> float:
        """
        Per arm, reach for targets and record whether the IK system correctly guessed the outcome.

        :return: The percentage of times where we guessed the action would fail and it did.
        """

        pbar = tqdm(total=len(self.positions) * 2)
        correct_no_orientation: int = 0
        total_no_orientation: int = 0
        for arm in [Arm.left, Arm.right]:
            for i in range(len(self.positions)):
                # Reload the scene.
                self.init_scene()
                orientation, got_orientation = self._get_ik_orientation(arm=arm, target=self.positions[i])
                # Reach for the target.
                status = self.reach_for(target=TDWUtils.array_to_vector3(self.positions[i]),
                                        arm=arm,
                                        arrived_at=self.arrived_at,
                                        target_orientation=orientation.target_orientation,
                                        orientation_mode=orientation.orientation_mode)
                # Record how often we correctly guess that there's no solution (the action should fail).
                if not got_orientation:
                    total_no_orientation += 1
                    if status != ActionStatus.success:
                        correct_no_orientation += 1
                pbar.update(1)
        pbar.close()
        if total_no_orientation > 0:
            no_orientation = correct_no_orientation / total_no_orientation
        else:
            no_orientation = "NaN"
        return no_orientation

    def run_auto(self, num_tries: int) -> float:
        """
        Benchmark whether the accuracy improves if the Magnebot tries more than once to reach the same position.

        :param num_tries: The number of consecutive tries to attempt before giving up.

        :return: The percentage of sequences of `reach_for()` actions (`num_tries` actions) that were successful.
        """
        pbar = tqdm(total=len(self.positions) * 2)
        successes: int = 0
        for arm in [Arm.left, Arm.right]:
            for i in range(len(self.positions)):
                # Reload the scene.
                self.init_scene()
                # Try multiple times to reach for the position.
                for j in range(5):
                    # Reach for the target.
                    status = self.reach_for(target=TDWUtils.array_to_vector3(self.positions[i]),
                                            arm=arm,
                                            arrived_at=self.arrived_at)
                    # Record a successful action or an action that was unsuccessful that we guessed would be.
                    if status == ActionStatus.success or status == ActionStatus.cannot_reach:
                        successes += 1
                        break
                pbar.update(1)
        pbar.close()
        return successes / (len(self.positions) * 2)


if __name__ == "__main__":
    m = ReachFor()
    successes_none = m.run_none()
    print("Success if orientation is (none, none):", successes_none)
    time_elapsed_auto = m.get_ik_orientation_speed()
    print("Average time elapsed per _get_ik_orientation() call:", time_elapsed_auto)
    no_orientation_speed = m.no_orientation_guess()
    print("Accuracy of no solution prediction:", no_orientation_speed)
    successes_auto = m.run_auto(1)
    print("Success if orientation is (auto, auto):", successes_auto)
    successes_multi = m.run_auto(5)
    print("Success if orientation is (auto, auto) (up to 5 consecutive attempts):", successes_multi)
    m.end()
