from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.backend.paths import EXAMPLE_CONTROLLER_OUTPUT_PATH
from magnebot import Magnebot, ActionStatus

"""
Minimal example of the `look_at(target)` action.
"""

d = EXAMPLE_CONTROLLER_OUTPUT_PATH.joinpath("magnebot_look_at")
if not d.exists():
    d.mkdir(parents=True)
print(f"Images will be saved to: {d}")
c = Controller()
m = Magnebot()
c.add_ons.append(m)
object_id = Controller.get_unique_id()
c.communicate([TDWUtils.create_empty_room(12, 12),
               Controller.get_add_object(model_name="rh10",
                                         position={"x": -1, "y": 0, "z": 2},
                                         object_id=object_id)])
m.look_at(target=object_id)
while m.action.status == ActionStatus.ongoing:
    c.communicate([])
# Add one more `communicate([])` call to let the action end and generate images.
c.communicate([])
# Save the images.
m.dynamic.save_images(output_directory=d)
c.communicate({"$type": "terminate"})
