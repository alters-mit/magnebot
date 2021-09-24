from pathlib import Path
from os import chdir
from pkg_resources import resource_filename
from py_md_doc import PyMdDoc
from md_link_tester import MdLinkTester


if __name__ == "__main__":
    chdir("..")
    metadata_file = "doc_metadata.json"
    # Add documentation for classes that inherit from tdw classes.
    for magnebot_class, tdw_class in zip(["magnebot",
                                          "magnebot_controller",
                                          "magnebot_dynamic",
                                          "magnebot_static"],
                                         ["add_ons/robot_base.py",
                                          "controller.py",
                                          "robot_data/robot_dynamic.py",
                                          "robot_data/robot_static.py",
                                          "add_ons/add_on.py"]):
        # Generate the document.
        md = PyMdDoc(input_directory="magnebot", files=[f"{magnebot_class}.py"], metadata_path=metadata_file)
        docs = md.get_docs_with_inheritance(abstract_class_path=resource_filename("tdw", tdw_class),
                                            child_class_paths=[f"magnebot/{magnebot_class}.py"])
        Path(f"doc/api/{magnebot_class}.md").write_text(docs[magnebot_class])

    md = PyMdDoc(input_directory="magnebot", files=["action_status.py",
                                                    "arm.py",
                                                    "arm_joint.py",
                                                    "collision_detection.py",
                                                    "image_frequency.py",
                                                    "wheel.py",
                                                    "turn_constants.py"], metadata_path="doc_metadata.json")
    md.get_docs(output_directory="doc/api")
    # Add IK documents.
    md = PyMdDoc(input_directory="magnebot", files=["ik/orientation.py",
                                                    "ik/orientation_mode.py",
                                                    "ik/target_orientation.py"])
    md.get_docs(output_directory="doc/api/ik")
    child_class_paths = ["arm_motion.py", "camera_action.py", "drop.py", "grasp.py", "ik_motion.py", "move_by.py",
                         "move_to.py", "reach_for.py", "reset_arm.py", "reset_position.py", "rotate_camera.py",
                         "stop.py", "turn.py", "turn_to.py", "wait.py", "wheel_motion.py"]
    docs = md.get_docs_with_inheritance(abstract_class_path="magnebot/actions/action.py",
                                        child_class_paths=[f"magnebot/actions/{c}" for c in child_class_paths])
    paths = child_class_paths[:]
    paths.append("action.py")
    for class_name, child_class_path in zip(docs.keys(), paths):
        Path(f"doc/api/actions/{child_class_path[:-3]}.md").write_text(docs[class_name])

    # Fix inherited links.
    for magnebot_class in ["magnebot_dynamic", "magnebot_static"]:
        doc_path = Path(f"doc/api/{magnebot_class}.md")
        doc = doc_path.read_text(encoding="utf-8")
        for tdw_class in ["joint_dynamic", "joint_static", "robot_static", "non_moving"]:
            doc = doc.replace(f"{tdw_class}.md",
                              f"https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/robot_data/{tdw_class}.md")
        doc_path.write_text(doc)

    # Test links.
    files_with_bad_links = MdLinkTester.test_directory(path="doc", ignore_files=["changelog.md"])
    for fi in files_with_bad_links:
        print(fi)
        for link in files_with_bad_links[fi]:
            print("\t", link)
