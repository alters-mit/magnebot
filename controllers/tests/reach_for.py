from time import time
import numpy as np
from tqdm import tqdm
from tdw.tdw_utils import TDWUtils
from magnebot import TestController, ActionStatus, Arm


class ReachFor(TestController):
    """
    Reach for random targets using the automated IK orientation system.
    If the action succeeds OR if the action fails but we expected it to fail, record the trial as a "correct guess".
    A high the percentage of correct guesses indicates that the automated IK orientation system tends to work.
    """

    def __init__(self, port: int = 1071):
        super().__init__(port=port)
        self._debug = False
        self._rng = np.random.RandomState(0)

    def run(self, num_trials_per_arm: int = 1000, arrived_at: float = 0.125) -> None:
        """
        Per arm, reach for targets and record whether the IK system correctly guessed the outcome.

        :param num_trials_per_arm: The number of trials per arm (total number of trials is twice this).
        :param arrived_at: The distance at which the action is successful.
        """

        pbar = tqdm(total=num_trials_per_arm * 2)
        correct_guesses: int = 0
        correct_no_orientation: int = 0
        total_no_orientation: int = 0
        # The time elapsed per orientation look-up.
        orientation_times = list()
        for arm in [Arm.left, Arm.right]:
            for i in range(num_trials_per_arm):
                # Reload the scene.
                self.init_scene()
                # Get a random position within the pre-calculated range.
                target = np.array([self._rng.uniform(-1.05, 1.05),
                                   self._rng.uniform(0, 1.5),
                                   self._rng.uniform(-1.05, 1.05)])
                # Get the orientation. Use this to verify whether or not a solution was found.
                t0 = time()
                orientation, got_orientation = self._get_ik_orientation(arm=arm, target=target, arrived_at=arrived_at)
                orientation_times.append(time() - t0)
                # Reach for the target.
                status = self.reach_for(target=TDWUtils.array_to_vector3(target), arm=arm)
                # We guessed the IK solution correctly if:
                # - The action was successful.
                # - There was no solution and the action was unsuccessful.
                if status == ActionStatus.success or not got_orientation:
                    correct_guesses += 1
                # Record how often we correctly guess that there's no solution (the action should fail).
                if not got_orientation:
                    total_no_orientation += 1
                    if status != ActionStatus.success:
                        correct_no_orientation += 1
                pbar.update(1)
        pbar.close()
        print("Correct guesses:", correct_guesses / (num_trials_per_arm * 2))
        if total_no_orientation > 0:
            no_orientation = correct_no_orientation / total_no_orientation
        else:
            no_orientation = "NaN"
        print("Correct guesses when there was no orientation solution:", no_orientation)
        print("Averaged time elapsed per _get_ik_orientation() call:", sum(orientation_times) / len(orientation_times))
        self.end()


if __name__ == "__main__":
    m = ReachFor()
    m.run(num_trials_per_arm=100, arrived_at=0.125)
