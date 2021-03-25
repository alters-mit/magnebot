from time import time
import numpy as np
from tqdm import tqdm
from tdw.tdw_utils import TDWUtils
from magnebot import TestController, ActionStatus, Arm
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.ik.orientation_mode import OrientationMode


class IK(TestController):
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
            self.positions: np.array = IK.get_positions()
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

    def run(self, target_orientation: TargetOrientation, orientation_mode: OrientationMode, num_tries: int = 1,
            re_init_scene: bool = True) -> float:
        """
        Reach for each target with each arm and record whether the action was successful.
        A successful guess is either `ActionStatus.success` or `ActionStatus.cannot_reach`.
        An unsuccessful guess is `ActionStatus.failed_to_bend`.

        :param target_orientation: The target orientation used per `reach_for()` action.
        :param orientation_mode: The orientation mode used per `reach_for()` action.
        :param num_tries: The number of sequential tries to reach for the same target.
        :param re_init_scene: If True, call `init_scene()` per trial to reset the arms.

        :return:  The percentage of `reach_for()` actions that were successful.
        """

        if not re_init_scene:
            self.init_scene()

        pbar = tqdm(total=len(self.positions) * 2)
        successes: int = 0
        for arm in [Arm.left, Arm.right]:
            for i in range(len(self.positions)):
                # Reload the scene.
                if re_init_scene:
                    self.init_scene()
                # Try multiple times to reach for the position.
                for j in range(num_tries):
                    # Reach for the target.
                    status = self.reach_for(target=TDWUtils.array_to_vector3(self.positions[i]),
                                            arm=arm,
                                            target_orientation=target_orientation,
                                            orientation_mode=orientation_mode,
                                            arrived_at=self.arrived_at)
                    # Record a successful action or an action that was unsuccessful that we guessed would be.
                    if status == ActionStatus.success or status == ActionStatus.cannot_reach:
                        successes += 1
                        break
                pbar.update(1)
        pbar.close()
        return successes / (len(self.positions) * 2)

    def get_orientation_speed(self) -> float:
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

    def no_orientation(self) -> float:
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
            return correct_no_orientation / total_no_orientation
        else:
            return -1

    def mixed(self) -> float:
        """
        Benchmark whether the a very basic multi-attempt algorithm improves accuracy.

        :return: The percentage of `reach_for()` actions that were successful.
        """

        pbar = tqdm(total=len(self.positions) * 2)
        successes: int = 0
        for arm in [Arm.left, Arm.right]:
            for i in range(len(self.positions)):
                # Reload the scene.
                self.init_scene()
                # Reach for the target.
                status = self.reach_for(target=TDWUtils.array_to_vector3(self.positions[i]),
                                        arm=arm,
                                        arrived_at=self.arrived_at)
                if status == ActionStatus.success or status == ActionStatus.cannot_reach:
                    successes += 1
                # If the motion failed, try to reach with (none, none).
                else:
                    status = self.reach_for(target=TDWUtils.array_to_vector3(self.positions[i]),
                                            arm=arm,
                                            arrived_at=self.arrived_at,
                                            orientation_mode=OrientationMode.none,
                                            target_orientation=TargetOrientation.none)
                    if status == ActionStatus.success or status == ActionStatus.cannot_reach:
                        successes += 1
                pbar.update(1)
        pbar.close()
        return successes / (len(self.positions) * 2)


if __name__ == "__main__":
    m = IK()

    auto = m.run(target_orientation=TargetOrientation.auto, orientation_mode=OrientationMode.auto)
    print("Success if orientation is (auto, auto):", auto)

    none = m.run(target_orientation=TargetOrientation.none, orientation_mode=OrientationMode.none)
    print("Success if orientation is (none, none):", none)

    orientation_speed = m.get_orientation_speed()
    print("Average time elapsed per _get_ik_orientation() call:", orientation_speed)

    no_orientation = m.no_orientation()
    print("Accuracy of no solution prediction:", no_orientation)

    multi = m.run(target_orientation=TargetOrientation.auto, orientation_mode=OrientationMode.auto, num_tries=5)
    print("Success if orientation is (auto, auto):", multi)

    mixed = m.mixed()
    print("Success with mixed consecutive parameters:", mixed)

    sequential = m.run(target_orientation=TargetOrientation.auto, orientation_mode=OrientationMode.auto, re_init_scene=False)
    print("Success if state isn't reset:", sequential)

    m.end()
