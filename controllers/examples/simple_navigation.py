from enum import Enum
from tqdm import tqdm
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from magnebot import MagnebotController, ActionStatus


class MoveAction(Enum):
    none = 0
    move_positive = 1
    move_negative = 2
    turn_positive = 4
    turn_negative = 8


class SimpleNavigation(MagnebotController):
    """
    A VERY simple navigation algorithm.
    The Magnebot will choose a random move or turn action. If that action ends in failure, it won't choose it again.
    For example, if the previous action was `move_by(1)` and it ended in failure, the next action can't be `move_by(2)`.
    """

    def run(self) -> None:
        self.init_floorplan_scene(scene="1a", layout=1, room=1)
        # Add a camera for debugging.
        camera = ThirdPersonCamera(avatar_id="a",
                                   position={"x": 1.43, "y": 1.87, "z": 0.77},
                                   look_at=0,
                                   follow_object=0)
        self.add_ons.append(camera)
        previous_action: MoveAction = MoveAction.none
        num_actions: int = 1000
        pbar = tqdm(total=num_actions)
        status = ActionStatus.success
        for i in range(num_actions):
            possible_actions = [a for a in MoveAction if a != MoveAction.none]
            # If the previous action was a failure, don't try to do it again.
            if status != ActionStatus.success:
                possible_actions = [a for a in possible_actions if a != previous_action]
            # Pick a random action.
            action: MoveAction = self.rng.choice(possible_actions)
            if action == MoveAction.move_positive:
                status = self.move_by(1)
                previous_action = MoveAction.move_positive
            elif action == MoveAction.move_negative:
                status = self.move_by(-1)
                previous_action = MoveAction.move_negative
            elif action == MoveAction.turn_positive:
                previous_action = MoveAction.move_positive
                status = self.turn_by(30)
            elif action == MoveAction.turn_negative:
                status = self.turn_by(-30)
                previous_action = MoveAction.turn_negative
            else:
                raise Exception(f"Not defined: {action}")
            pbar.update(1)
        self.end()


if __name__ == "__main__":
    m = SimpleNavigation(random_seed=0)
    m.run()
