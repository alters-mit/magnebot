from typing import List, Dict
from json import dumps, loads, JSONEncoder
import numpy as np
from tqdm import tqdm
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.librarian import ModelLibrarian
from tdw.output_data import Bounds, Raycast
from magnebot.paths import CONVEX_SIDES_PATH


class Encoder(JSONEncoder):
    """
    Source: https://stackoverflow.com/questions/16264515/json-dumps-custom-formatting
    """

    def __init__(self, *args, **kwargs):
        super(Encoder, self).__init__(*args, **kwargs)
        self.current_indent = 0
        self.current_indent_str = ""

    def encode(self, o):
        if isinstance(o, (list, tuple)):
            return "[" + ", ".join([dumps(item) for item in o]) + "]"
        elif isinstance(o, dict):
            output = []
            self.current_indent += self.indent
            self.current_indent_str = "".join([" " for x in range(self.current_indent)])
            for key, value in o.items():
                output.append(self.current_indent_str + dumps(key) + ": " + self.encode(value))
            self.current_indent -= self.indent
            self.current_indent_str = "".join([" " for x in range(self.current_indent)])
            return "{\n" + ",\n".join(output) + "\n" + self.current_indent_str + "}"
        else:
            return dumps(o)


class Convex(Controller):
    """
    For every object in the full model library, determine which sides of the bounds are convex.
    This data will be used by `Magnebot.grasp()` when choosing which sides to target.
    """

    def __init__(self, port: int = 1071, launch_build: bool = True):
        if not CONVEX_SIDES_PATH.exists():
            CONVEX_SIDES_PATH.write_text("{}")
            self.concave: Dict[str, List[int]] = dict()
        else:
            self.concave: Dict[str, List[int]] = loads(CONVEX_SIDES_PATH.read_text(encoding="utf-8"))
        super().__init__(port=port, launch_build=launch_build, check_version=False)
        self.model_librarian = ModelLibrarian("models_full.json")
        self.pbar = tqdm(total=len(self.model_librarian.records))

    def run(self) -> None:
        """
        For every model in the model library, get the bounds. Raycast from one side of the object to the other.
        If the raycast hit, and the hit point is closer to the farther side than the nearer side, the side is concave.
        Write all convex sides per object to disk.
        """

        self.communicate({"$type": "create_empty_environment"})

        for record in self.model_librarian.records:
            # Ignore bad models or models that we already checked.
            if record.name in self.concave or record.do_not_use:
                self.pbar.update(1)
                continue
            self.pbar.set_description(record.name)
            object_id = self.get_unique_id()
            scale = TDWUtils.get_unit_scale(record)
            # Create the object. Scale to unit size. Make the object kinematic so that it won't fall over.
            # Get the bounds. Raycast directly above the object.
            resp = self.communicate([self.get_add_object(model_name=record.name,
                                                         library="models_full.json",
                                                         object_id=object_id),
                                     {"$type": "set_kinematic_state",
                                      "id": object_id,
                                      "is_kinematic": True,
                                      "use_gravity": False},
                                     {"$type": "scale_object",
                                      "id": object_id,
                                      "scale_factor": {"x": scale, "y": scale, "z": scale}},
                                     {"$type": "send_bounds"}])
            bounds = Bounds(resp[0])
            # Convert the bounds sides to a dictionary.
            sides = {"left": np.array(bounds.get_left(0)),
                     "right": np.array(bounds.get_right(0)),
                     "front": np.array(bounds.get_front(0)),
                     "back": np.array(bounds.get_back(0)),
                     "top": np.array(bounds.get_top(0)),
                     "bottom": np.array(bounds.get_bottom(0))}
            # The origin points of each ray per direction.
            ray_origins = {"left": {"x": sides["left"][0] - 4, "y": sides["left"][1], "z": 0},
                           "right": {"x": sides["right"][0] + 4, "y": sides["right"][1], "z": 0},
                           "front": {"x": 0, "y": sides["front"][1], "z": sides["front"][2] + 4},
                           "back": {"x": 0, "y": sides["back"][1], "z": sides["back"][2] - 4},
                           "top": {"x": 0, "y": sides["top"][1] + 4, "z": 0},
                           "bottom": {"x": 0, "y": sides["bottom"][1] - 4, "z": 0}}
            # The destination of each ray (the opposite side of the bounds).
            ray_destinations = {"left": "right",
                                "right": "left",
                                "front": "back",
                                "back": "front",
                                "top": "bottom",
                                "bottom": "top"}
            # Get a raycast per side.
            good_sides: List[int] = list()
            for i, side, ray in zip(range(len(sides)), sides.keys(), ray_origins):
                resp = self.communicate({"$type": "send_raycast",
                                         "origin": ray_origins[ray],
                                         "destination": ray_origins[ray_destinations[ray]]})
                raycast = Raycast(resp[0])
                # Ignore raycasts that didn't hit the object.
                if not raycast.get_hit() or not raycast.get_hit_object():
                    continue
                side_origin: np.array = sides[side]
                side_destination: np.array = sides[ray_destinations[side]]
                point: np.array = np.array(raycast.get_point())
                # Ignore raycasts that hit a significant concavity.
                if np.linalg.norm(side_origin - point) - np.linalg.norm(side_destination - point) > 0.05:
                    continue
                good_sides.append(i)
            # Destroy the object and remove it from memory.
            self.communicate([{"$type": "destroy_object",
                               "id": object_id},
                              {"$type": "unload_asset_bundles"}])
            # Record the results.
            self.concave[record.name] = good_sides
            CONVEX_SIDES_PATH.write_text(dumps(self.concave, indent=2, cls=Encoder))
            self.pbar.update(1)
        self.communicate({"$type": "terminate"})


if __name__ == "__main__":
    c = Convex()
    c.run()
