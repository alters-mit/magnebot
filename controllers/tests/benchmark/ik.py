import numpy as np
from tqdm import tqdm
from tdw.tdw_utils import TDWUtils
from magnebot import MagnebotController, ActionStatus, Arm
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.ik.orientation_mode import OrientationMode


class IK(MagnebotController):
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

    def run(self, target_orientation: TargetOrientation, orientation_mode: OrientationMode) -> float:
        """
        `reach_for()` an array of positions. Record if we correctly guessed the result.
        A correct guess is either a `success` or `cannot_reach`.
        If the `reach_for()` action returns `failed_to_bend` or `failed_to_reach`, we guessed incorrectly because
        we thought the action would succeed and it didn't.

        :param target_orientation: The target orientation used per `reach_for()` action.
        :param orientation_mode: The orientation mode used per `reach_for()` action.

        :return:  The percentage of `reach_for()` actions that were successful.
        """

        pbar = tqdm(total=len(self.positions) * 2)
        successes: int = 0
        for arm in [Arm.left, Arm.right]:
            for i in range(len(self.positions)):
                self.init_scene()
                # Reach for the target.
                status = self.reach_for(target=TDWUtils.array_to_vector3(self.positions[i]),
                                        arm=arm,
                                        target_orientation=target_orientation,
                                        orientation_mode=orientation_mode,
                                        arrived_at=self.arrived_at)
                # Record a successful action or an action that was unsuccessful that we guessed would be.
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

    m.end()
