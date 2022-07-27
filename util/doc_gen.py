from pathlib import Path
from os import chdir, remove
from shutil import copy
from pkg_resources import resource_filename
from py_md_doc import PyMdDoc, ClassInheritance
from md_link_tester import MdLinkTester
from tdw_dev.config import Config


if __name__ == "__main__":
    chdir("..")
    metadata_file = "doc_metadata.json"
    md = PyMdDoc(input_directory="magnebot", files=["magnebot.py",
                                                    "magnebot_controller.py"], metadata_path=metadata_file)
    md.get_docs(output_directory="doc/api")
    tdw_path = Config().tdw_path.joinpath("Python/tdw")
    # Add documentation for classes that inherit from tdw classes.
    for magnebot_class, tdw_class in zip(["magnebot_dynamic",
                                          "magnebot_static"],
                                         ["robot_data/robot_dynamic.py",
                                          "robot_data/robot_static.py"]):
        # Copy the TDW file.
        tdw_src = tdw_path.joinpath(tdw_class)
        tdw_class_split = tdw_class.split('/')
        if len(tdw_class_split) == 1:
            tdw_file = tdw_class_split[0]
        else:
            tdw_file = tdw_class_split[1]
        tdw_dst = f"magnebot/{tdw_file}"
        copy(src=tdw_src, dst=tdw_dst)
        # Generate the document.
        ClassInheritance.get_from_directory(input_directory="magnebot",
                                            output_directory="doc/api",
                                            import_path="magnebot",
                                            includes=[f"{magnebot_class}.py", tdw_file])
        # Remove the TDW file.
        remove(tdw_dst)
        # Remove the TDW document.
        remove(f"doc/api/{tdw_file[:-3]}.md")
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
    ClassInheritance.get_from_directory(input_directory="magnebot/actions",
                                        output_directory="doc/api/actions",
                                        import_path="magnebot.actions",
                                        import_prefix="from magnebot.actions",
                                        overrides={"IkMotion": "IKMotion",
                                                   "i_k_motion": "ik_motion"})
    # Fix inherited links.
    for magnebot_class in ["magnebot_dynamic", "magnebot_static"]:
        doc_path = Path(f"doc/api/{magnebot_class}.md")
        doc = doc_path.read_text(encoding="utf-8")
        for tdw_class in ["joint_dynamic", "joint_static", "robot_static", "non_moving"]:
            doc = doc.replace(f"{tdw_class}.md",
                              f"https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/robot_data/{tdw_class}.md")
        for tdw_class in ["transform"]:
            doc = doc.replace(f"../object_data/{tdw_class}.md",
                              f"https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/object_data/{tdw_class}.md")
        doc_path.write_text(doc)

    # Test links.
    files_with_bad_links = MdLinkTester.test_directory(path="doc", ignore_files=["changelog.md"])
    for fi in files_with_bad_links:
        print(fi)
        for link in files_with_bad_links[fi]:
            print("\t", link)
