from py_md_doc import PyMdDoc


if __name__ == "__main__":
    files = ["action_status.py",
             "arm.py",
             "arm_joint.py",
             "body_part_static.py",
             "joint_angles.py",
             "magnebot_controller.py",
             "magnebot_static.py",
             "object_static.py",
             "scene_state.py",
             "transform.py",
             "wheel.py"]
    md = PyMdDoc(input_directory="magnebot", files=files, metadata_path="doc_metadata.json")
    md.get_docs(output_directory="doc")
