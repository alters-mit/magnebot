from typing import List, Tuple
import numpy as np
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus, Arm
from magnebot.collision_detection import CollisionDetection


class Convex(Magnebot):
    """
    Test how often the Magnebot can grasp a strangely-shaped object.
    """

    # A list of medium-sized objects that have at least one concave surface.
    MODELS = ['basket_18inx18inx12iin_bamboo', 'basket_18inx18inx12iin_plastic_lattice',
              'basket_18inx18inx12iin_wicker', 'basket_18inx18inx12iin_wood_mesh', 'black_lamp', 'bork_vacuum',
              'box_18inx18inx12in_cardboard', 'box_24inx18inx12in_cherry', 'box_tapered_beech',
              'box_tapered_white_mesh', 'brown_leather_dining_chair', 'chair_billiani_doll', 'desk_lamp',
              'duffle_bag_sm', 'elephant_bowl', 'glass2', 'jug03', 'lapalma_stil_chair', 'ligne_roset_armchair',
              'linbrazil_diz_armchair', 'monster_beats_studio', 'red_lamp', 'round_bowl_large_metal_perf',
              'round_bowl_large_padauk', 'round_bowl_large_thin', 'round_bowl_small_beech', 'round_bowl_small_walnut',
              'round_bowl_talll_wenge', 'satiro_sculpture', 'serving_bowl', 'shallow_basket_white_mesh',
              'shallow_basket_wicker', 'skillet_open', 'tan_lounger_chair', 'toaster_002', 'vase_05', 'vase_06',
              'vitra_meda_chair', 'white_lounger_chair', 'wood_chair']

    def init_scene(self) -> ActionStatus:
        origin = np.array([0, 0, 0])
        # Add random objects in a circle.
        num_objects = 10
        d_theta = 360 / num_objects
        theta = d_theta / 2
        pos = np.array([3, 0, 0])
        for j in range(num_objects):
            object_position = TDWUtils.rotate_position_around(origin=origin, position=pos, angle=theta)
            object_position[1] = 2
            name = self._rng.choice(Convex.MODELS)
            self._add_object(model_name=name,
                             position=TDWUtils.array_to_vector3(object_position),
                             rotation={"x": self._rng.uniform(-180, 180),
                                       "y": self._rng.uniform(-180, 180),
                                       "z": self._rng.uniform(-180, 180)})
            theta += d_theta
        return super().init_scene()

    def run(self, random_seed: int = None) -> Tuple[int, int, List[str]]:
        if random_seed is None:
            random_seed = self.get_unique_id()
        print("Random seed:", random_seed)
        self._rng = np.random.RandomState(random_seed)
        self.init_scene()
        successes = 0
        cannots = 0
        failures = list()
        for o_id in self.objects_static:
            status = self.move_to(target=o_id)
            if status == ActionStatus.collision:
                self.move_by(-0.2, arrived_at=0.05, stop_on_collision=CollisionDetection(exclude_objects=[o_id]))
            status = self.grasp(target=o_id, arm=Arm.right)
            if status == ActionStatus.success:
                self.drop(target=o_id, arm=Arm.right)
                successes += 1
            else:
                print(status)
                if status == ActionStatus.cannot_reach:
                    cannots += 1
                failures.append(self.objects_static[o_id].name)
            self.reset_arm(arm=Arm.right)
            self.reset_arm(arm=Arm.left)
            self.move_by(-0.5, stop_on_collision=CollisionDetection(exclude_objects=[o_id]))
            self.move_to(target={"x": 0, "y": 0, "z": 0})
        m.end()
        return successes, cannots, failures


if __name__ == "__main__":
    m = Convex(debug=True)
    s, c, f = m.run()
    print("Success:", s)
    print("Cannot grasp:", c)
    print("Failed to grasp:", f)
