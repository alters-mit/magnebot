from tqdm import tqdm
from magnebot import Magnebot, ActionStatus
from magnebot.collision_action import CollisionAction


class SimpleNavigation(Magnebot):
    """
    A VERY simple navigation algorithm.
    The Magnebot will choose a random move or turn action. If that action ends in failure, it won't choose it again.
    For example, if the previous action was `move_by(1)` and it ended in failure, the next action can't be `move_by(2)`.
    """

    # A list of all possible actions. Remove the first element (none).
    ACTIONS = [a for a in CollisionAction][1:]

    def run(self) -> None:
        self.init_scene(scene="1a", layout=1, room=1)
        # Add a camera for debugging.
        self.add_camera(position={"x": 1.43, "y": 1.87, "z": 0.77}, look_at=True, follow=True)
        previous_action: int = 0
        num_actions: int = 1000
        pbar = tqdm(total=num_actions)
        for i in range(num_actions):
            # Convert all potential actions to an integer.
            actions: int = sum([a.value for a in CollisionAction]) - previous_action
            # Get a list of all possible options. If the previous action was a collision, disallow it.
            possible_actions = [a for a in SimpleNavigation.ACTIONS if actions - previous_action & a.value]
            # Pick a random action.
            action: CollisionAction = self._rng.choice(possible_actions)
            if action == CollisionAction.move_positive:
                status = self.move_by(1)
            elif action == CollisionAction.move_negative:
                status = self.move_by(-1)
            elif action == CollisionAction.turn_positive:
                status = self.turn_by(30)
            elif action == CollisionAction.turn_negative:
                status = self.turn_by(-30)
            else:
                raise Exception(f"Not defined: {action}")
            # The action succeeded so we're allowed to try it again.
            if status == ActionStatus.success:
                previous_action = 0
            # The action failed. Don't try it again.
            else:
                previous_action = action.value
            pbar.update(1)
        self.end()


if __name__ == "__main__":
    m = SimpleNavigation(random_seed=0)
    m.run()
