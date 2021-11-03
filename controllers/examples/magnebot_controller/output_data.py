from tdw.tdw_utils import TDWUtils
from magnebot import MagnebotController
from magnebot.util import get_default_post_processing_commands


class OutputData(MagnebotController):
    """
    Print static object data, static Magnebot data, dynamic object data, and dynamic Magnebot data.
    """

    def init_scene(self):
        scene = [{"$type": "load_scene",
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(12, 12)]
        objects = self.get_add_physics_object(model_name="cabinet_36_wood_beach_honey",
                                              position={"x": 0.04, "y": 0, "z": 1.081},
                                              kinematic=True,
                                              object_id=self.get_unique_id())
        objects.extend(self.get_add_physics_object(model_name="rh10",
                                                   position={"x": -2, "y": 0, "z": -1.5},
                                                   object_id=self.get_unique_id()))
        self._init_scene(scene=scene,
                         objects=objects,
                         position={"x": 1, "y": 0, "z": -3},
                         rotation={"x": 0, "y": 46, "z": 0},
                         post_processing=get_default_post_processing_commands())

    def print_static_data(self) -> None:
        print("STATIC DATA")
        print("Objects:")
        for object_id in self.objects.objects_static:
            print("\t", "Name:", self.objects.objects_static[object_id].name)
            print("\t\t", "ID:", object_id)
            print("\t\t", "Segmentation color:", self.objects.objects_static[object_id].segmentation_color)
            print("\t\t", "Category:", self.objects.objects_static[object_id].category)
            print("\t\t", "Kinematic:", self.objects.objects_static[object_id].name)
            print("\t\t", "Mass:", self.objects.objects_static[object_id].mass)
            print("\t\t", "Size:", self.objects.objects_static[object_id].size)
            print("\t\t", "Dynamic friction:", self.objects.objects_static[object_id].dynamic_friction)
            print("\t\t", "Static friction:", self.objects.objects_static[object_id].static_friction)
            print("\t\t", "Bounciness:", self.objects.objects_static[object_id].bounciness)
        print("Magnebot")
        print("\t", "ID:", self.magnebot.static.robot_id)
        print("\t", "Wheels:")
        for wheel in self.magnebot.static.wheels:
            self.print_joint_static(joint_id=self.magnebot.static.wheels[wheel])
        print("\t", "Arm joints:")
        for arm_joint in self.magnebot.static.arm_joints:
            self.print_joint_static(joint_id=self.magnebot.static.arm_joints[arm_joint])
        print("\t", "Magnets:")
        for arm in self.magnebot.static.magnets:
            self.print_joint_static(joint_id=self.magnebot.static.magnets[arm])
        print("\t", "Non-moving body parts")
        for part_id in self.magnebot.static.non_moving:
            print("\t\t", "ID:", part_id)
            print("\t\t", "Name:", self.magnebot.static.non_moving[part_id].name)
            print("\t\t", "Segmentation color:", self.magnebot.static.non_moving[part_id].segmentation_color)
        print("")

    def print_joint_static(self, joint_id: int) -> None:
        joint = self.magnebot.static.joints[joint_id]
        print("\t\t", "Name:", joint.name)
        print("\t\t\t", "ID:", joint.joint_id)
        print("\t\t\t", "Type:", joint.joint_type)
        print("\t\t\t", "Segmentation color:", joint.segmentation_color)
        print("\t\t\t", "Segmentation color:", joint.segmentation_color)
        print("\t\t\t", "Mass:", joint.mass)
        print("\t\t\t", "Immovable:", joint.immovable)
        print("\t\t\t", "Drives:")
        for axis in joint.drives:
            print("\t\t\t\t", "Axis:", axis)
            print("\t\t\t\t\t", "Limits:", joint.drives[axis].limits)
            print("\t\t\t\t\t", "Force limit:", joint.drives[axis].force_limit)
            print("\t\t\t\t\t", "Damping:", joint.drives[axis].damping)
            print("\t\t\t\t\t", "Stiffness:", joint.drives[axis].stiffness)

    def print_dynamic_data(self) -> None:
        print("DYNAMIC DATA")
        print("Objects:")
        for object_id in self.objects.transforms:
            print("\t", "ID:", object_id)
            print("\t\t", "Position:", self.objects.transforms[object_id].position)
            print("\t\t", "Forward:", self.objects.transforms[object_id].forward)
            print("\t\t", "Rotation:", self.objects.transforms[object_id].rotation)
        print("Magnebot")
        print("\t", "Position:", self.magnebot.dynamic.transform.position)
        print("\t", "Forward:", self.magnebot.dynamic.transform.forward)
        print("\t", "Rotation:", self.magnebot.dynamic.transform.rotation)
        print("\t", "Holding:")
        for arm in self.magnebot.dynamic.held:
            print("\t\t", arm.name, self.magnebot.dynamic.held[arm])
        print("\t", "Camera matrix:", self.magnebot.dynamic.camera_matrix)
        print("\t", "Projection matrix:", self.magnebot.dynamic.projection_matrix)
        print("\t", "Wheels:")
        for wheel in self.magnebot.static.wheels:
            self.print_joint_dynamic(joint_id=self.magnebot.static.wheels[wheel])
        print("\t", "Arm joints:")
        for arm_joint in self.magnebot.static.arm_joints:
            self.print_joint_dynamic(joint_id=self.magnebot.static.arm_joints[arm_joint])
        print("\t", "Magnets:")
        for arm in self.magnebot.static.magnets:
            self.print_joint_dynamic(joint_id=self.magnebot.static.magnets[arm])
        print("\t", "Images:")
        for image_pass in self.magnebot.dynamic.images:
            print("\t\t", image_pass)
        print("\t", "Point cloud:", self.magnebot.dynamic.get_point_cloud())
        print("")

    def print_joint_dynamic(self, joint_id: int) -> None:
        print("\t\t", "ID:", joint_id)
        print("\t\t\t", "Position:", self.magnebot.dynamic.joints[joint_id].position)
        print("\t\t\t", "Angles:", self.magnebot.dynamic.joints[joint_id].angles)
        print("\t\t\t", "Moving:", self.magnebot.dynamic.joints[joint_id].moving)


if __name__ == "__main__":
    c = OutputData()
    c.init_scene()
    c.print_static_data()
    c.print_dynamic_data()
    c.move_by(2)
    c.print_dynamic_data()
    c.end()
