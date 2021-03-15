from py_md_doc import PyMdDoc
from os import chdir

if __name__ == "__main__":
    chdir("..")
    files = ["action_status.py",
             "arm.py",
             "arm_joint.py",
             "joint_static.py",
             "magnebot_controller.py",
             "magnebot_static.py",
             "object_static.py",
             "ik/orientation_mode.py",
             "scene_state.py",
             "ik/target_orientation.py",
             "transform.py",
             "wheel.py",
             "test_controller.py",
             "drive.py",
             "turn_constants.py"]
    md = PyMdDoc(input_directory="magnebot", files=files, metadata_path="doc_metadata.json")
    md.get_docs(output_directory="doc/api")
