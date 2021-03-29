from typing import List, Dict
from time import time
import numpy as np
from tqdm import tqdm
from tdw.tdw_utils import TDWUtils
from tdw.object_init_data import AudioInitData
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

    def get_orientation_speed(self) -> float:
        """
        :return: The average speed of `_get_ik_orientation()`.
        """

        orientation_times = list()
        for arm in [Arm.left, Arm.right]:
            for i in range(len(self.positions)):
                # Get the orientation.
                t0 = time()
                self._get_ik_orientations(arm=arm, target=self.positions[i])
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
                orientations = self._get_ik_orientations(arm=arm, target=self.positions[i])
                if len(orientations) == 0:
                    target_orientation = TargetOrientation.none
                    orientation_mode = OrientationMode.none
                else:
                    target_orientation = orientations[0].target_orientation
                    orientation_mode = orientations[0].orientation_mode

                # Reach for the target.
                status = self.reach_for(target=TDWUtils.array_to_vector3(self.positions[i]),
                                        arm=arm,
                                        arrived_at=self.arrived_at,
                                        target_orientation=target_orientation,
                                        orientation_mode=orientation_mode)
                # Record how often we correctly guess that there's no solution (the action should fail).
                if len(orientations) == 0:
                    total_no_orientation += 1
                    if status != ActionStatus.success:
                        correct_no_orientation += 1
                pbar.update(1)
        pbar.close()
        if total_no_orientation > 0:
            return correct_no_orientation / total_no_orientation
        else:
            return -1

    def grasp_ik(self) -> float:
        """
        Test how often we correctly guess that a `grasp()` action will succeed.

        :return: The percentage of times where we guessed correctly.
        """

        pbar = tqdm(total=len(self.positions) * 2)
        successes: int = 0
        for arm in [Arm.left, Arm.right]:
            for i in range(len(self.positions)):
                a = AudioInitData(name="jug05",
                                  position=TDWUtils.array_to_vector3(self.positions[i]),
                                  kinematic=True,
                                  gravity=False)
                self.init_scene(a=a)
                # Reach for the target.
                status = self.grasp(target=list(self.objects_static.keys())[0], arm=arm)
                # Record a successful action or an action that was unsuccessful that we guessed would be.
                if status == ActionStatus.success or status == ActionStatus.cannot_reach:
                    successes += 1
                pbar.update(1)
        pbar.close()
        return successes / (len(self.positions) * 2)

    def init_scene(self, scene: str = None, layout: int = None, room: int = None, a: AudioInitData = None) -> ActionStatus:
        """
        Added optional parameter `a` to add an object to the scene.
        """

        self._clear_data()
        commands = [{"$type": "load_scene",
                     "scene_name": "ProcGenScene"},
                    TDWUtils.create_empty_room(12, 12)]
        commands.extend(self._get_scene_init_commands(magnebot_position={"x": 0, "y": 0, "z": 0}, a=a))
        resp = self.communicate(commands)
        self._cache_static_data(resp=resp)
        # Wait for the Magnebot to reset to its neutral position.
        self._do_arm_motion()
        self._end_action()
        return ActionStatus.success

    def _get_scene_init_commands(self, magnebot_position: Dict[str, float] = None, a: AudioInitData = None) -> List[dict]:
        if a is not None:
            o_id, o_commands = a.get_commands()
            self._object_init_commands[o_id] = o_commands
        return super()._get_scene_init_commands(magnebot_position=magnebot_position)


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

    grasp = m.grasp_ik()
    print("Accuracy of grasp():", grasp)

    m.end()
