from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot


if __name__ == "__main__":
    c = Magnebot(launch_build=False, debug=True)
    c.init_test_scene()
    expected_names = ["shoulder_left", "elbow_left", "magnet_left", "magnet_link_left",
                      "shoulder_right", "elbow_right", "magnet_right", "magnet_link_right",
                      "wheel_left_front", "wheel_left_back", "wheel_right_front", "wheel_right_back"]
    shoulders = []
    elbows = []
    magnets = []
    for j_id in c.robot_static:
        j = c.robot_static[j_id]
        assert j.name in expected_names, f"Unexpected name: {j.name}"
        if "shoulder" in j.name:
            shoulders.append(j.id)
        elif "elbow" in j.name:
            elbows.append(j.id)
        elif "magnet" in j.name and "link" not in j.name:
            magnets.append(j.id)

    commands = []
    for shoulder in shoulders:
        commands.append({"$type": "set_spherical_target",
                         "joint_id": shoulder,
                         "target": {"x": 45, "y": 50, "z": 120}})
    for elbow in elbows:
        commands.append({"$type": "set_revolute_target",
                         "joint_id": elbow,
                         "target": 50})
    for magnet in magnets:
        commands.append({"$type": "set_spherical_target",
                         "joint_id": magnet,
                         "target": {"x": 10, "y": 30, "z": -70}})
    c.communicate(commands)
    for i in range(150):
        c.communicate([])
    c.communicate(TDWUtils.create_avatar(position={"x": 0, "y": 0.8, "z": 1.75},
                                         look_at={"x": 0, "y": 0.8, "z": 0}))
