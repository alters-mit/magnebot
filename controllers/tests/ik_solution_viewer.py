from argparse import ArgumentParser
import numpy as np
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from magnebot.paths import IK_ORIENTATIONS_RIGHT_PATH, IK_ORIENTATIONS_LEFT_PATH
from magnebot.ik.orientation import ORIENTATIONS

"""
View the IK solutions per position as colors.
"""

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--arm", type=str, choices=["left", "right"], default="left")
    args = parser.parse_args()
    if args.arm == "left":
        path = IK_ORIENTATIONS_LEFT_PATH
    else:
        path = IK_ORIENTATIONS_RIGHT_PATH
    ik = np.load(str(path.resolve()))
    # Get some colors for the position markers
    colors_np = np.load("ik_palette.npy")
    # Convert to Unity colors.
    colors = [TDWUtils.array_to_color(c / 255.0) for c in colors_np]
    for o, c in zip(ORIENTATIONS, colors):
        print(o, c)
    no_orientation = {"r": 0, "g": 0, "b": 0, "a": 1}

    pos_commands = list()
    # Get the position and orientation from the array.
    # Express the orientation as a color.
    # Add a position marker.
    for i in ik:
        # Get the orientation. Add a position marker with the corresponding color.
        o = int(i[3])
        if o == -1:
            color = no_orientation
        else:
            color = colors[o]
        pos_commands.append({"$type": "add_position_marker",
                             "position": TDWUtils.array_to_vector3(np.array(i[0], i[1], i[2])),
                             "scale": 0.2,
                             "color": color})
    c = Controller(launch_build=False)
    c.start()
    # Create a room. Add an avatar. Add the position markers.
    commands = [TDWUtils.create_empty_room(12, 12)]
    commands.extend(TDWUtils.create_avatar(position={"x": 3, "y": 3, "z": 3},
                                           look_at=TDWUtils.VECTOR3_ZERO))
    commands.extend(pos_commands)
    c.communicate(commands)
