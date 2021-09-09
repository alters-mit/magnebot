from pathlib import Path
from py_md_doc import PyMdDoc
from os import chdir
from md_link_tester import MdLinkTester

if __name__ == "__main__":
    chdir("..")
    md = PyMdDoc(input_directory="magnebot", files=["action_status.py",
                                                    "arm.py",
                                                    "arm_joint.py",
                                                    "collision_detection.py",
                                                    "image_frequency.py",
                                                    "magnebot.py",
                                                    "magnebot_controller.py",
                                                    "magnebot_dynamic.py",
                                                    "magnebot_static.py",
                                                    "skip_frames.py",
                                                    "wheel.py",
                                                    "turn_constants.py"], metadata_path="doc_metadata.json")
    md.get_docs(output_directory="doc/api")
    md = PyMdDoc(input_directory="magnebot", files=["ik/orientation.py",
                                                    "ik/orientation_mode.py",
                                                    "ik/target_orientation.py"])
    md.get_docs(output_directory="doc/api/ik")
    for abstract_class_path, child_class_paths in zip(["action.py",
                                                       "arm_motion.py",
                                                       "camera_action.py",
                                                       "ik_motion.py",
                                                       "turn.py",
                                                       "wheel_motion.py"],
                                                      [["wait.py",
                                                        "reset_position.py"],
                                                       ["drop.py",
                                                        "reset_arm.py"],
                                                       ["reset_camera.py",
                                                        "rotate_camera.py"],
                                                       ["grasp.py",
                                                        "reach_for.py"],
                                                       ["turn_by.py",
                                                        "turn_to.py"],
                                                       ["move_by.py",
                                                        "move_to.py"]]):
        docs = md.get_docs_with_inheritance(abstract_class_path=f"magnebot/actions/{abstract_class_path}",
                                            child_class_paths=[f"magnebot/actions/{c}" for c in child_class_paths])
        paths = child_class_paths[:]
        paths.append(abstract_class_path)
        for class_name, child_class_path in zip(docs.keys(), paths):
            Path(f"doc/api/actions/{child_class_path[:-3]}.md").write_text(docs[class_name])

    exit()
    files_with_bad_links = MdLinkTester.test_directory(path="doc", ignore_files=["changelog.md"])
    for fi in files_with_bad_links:
        print(fi)
        for link in files_with_bad_links[fi]:
            print("\t", link)
