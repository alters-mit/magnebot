from typing import List
import numpy as np
from magnebot import MagnebotController, Arm, ActionStatus
from magnebot.actions.rotate_camera import RotateCamera


class PickUp(MagnebotController):
    """
    This is an example of how to move the Magnebot around a room and pick up an object.
    """

    def set_collision_detection(self, is_on: bool) -> None:
        self.magnebot.collision_detection.objects = is_on
        self.magnebot.collision_detection.walls = is_on
        self.magnebot.collision_detection.previous_was_same = is_on

    def run(self) -> None:
        print("Loading the scene...")

        # Load scene 4a, layout 0, and spawn the avatar in room 5.
        # See documentation for images of the floorplans and rooms.
        self.init_floorplan_scene(scene="4a", layout=2, room=4)
        # Get all of the nearby objects.
        nearby: List[int] = list()

        print("Rotating the Magnebot to get a 360 view of nearby objects.")
        d_turn: int = 90
        turn: int = 0
        while turn < 270:
            # Look around you.
            d_cam_theta = 45
            status = self.rotate_camera(yaw=-RotateCamera.CAMERA_RPY_CONSTRAINTS[2])
            # Rotate the camera until we get an ActionStatus that the angle has been clamped to the RPY constraints.
            # That means that we've rotated the camera as far as it will go.
            while status == ActionStatus.success:
                # Get all visible objects in this frame.
                nearby.extend(self.get_visible_objects())
                # Keep rotating the camera.
                status = self.rotate_camera(yaw=d_cam_theta)
            # Turn the Magnebot.
            self.set_collision_detection(is_on=False)
            self.turn_by(d_turn)
            self.set_collision_detection(is_on=True)
            turn += d_turn
        nearby = list(set(nearby))
        print(f"Nearby objects:")
        for object_id in nearby:
            print("\t", object_id, self.objects.objects_static[object_id].name)
        # Get small physics-enabled objects.
        small_objects = [o for o in nearby if not self.objects.objects_static[o].kinematic and
                         self.objects.objects_static[o].mass < 6]
        # Sort the objects by distance from the Magnebot.
        # This is a very naive solution!
        # If there aren't any small objects in the room, this script will crash.
        # Sometimes, small objects will be too high up for the Magnebot to reach.
        # Sometimes, there will be another object in the way.
        # And so on.
        small_objects = list(sorted(small_objects, key=lambda o: np.linalg.norm(
            self.magnebot.dynamic.transform.position - self.objects.transforms[o].position)))
        # Set the target object as the closest small object.
        target_object = small_objects[0]
        print(f"Target object: {target_object}\t{self.objects.objects_static[target_object].name}")

        # Move to the target object.
        self.set_collision_detection(is_on=False)
        status = self.move_to(target=target_object, arrived_offset=0.3)
        self.set_collision_detection(is_on=True)
        print(f"Move to target object: {status}")
        # Grasp the object.
        status = self.grasp(target_object, arm=Arm.left)
        print(f"Grasped target object: {status}")
        print(f"Currently held objects: {self.magnebot.dynamic.held}")
        # Reset the arm.
        status = self.reset_arm(arm=Arm.left)
        print(f"Reset arm: {status}")
        # Move backwards.
        status = self.move_by(-1)
        print(f"Moved backwards: {status}")
        status = self.turn_by(45)
        print(f"Turned: {status}")

        # This is an example of VERY basic navigation.
        status = self.move_by(1.5)
        while status == ActionStatus.collision:
            print(f"Tried moving but got status: {status}")
            # If we collided with something, back up, re-orient, and try again.
            self.set_collision_detection(is_on=False)
            self.move_by(-0.5)
            self.set_collision_detection(is_on=True)
            self.turn_by(15)
            status = self.move_by(1)
        print(f"Moved: {status}")

        status = self.drop(target=target_object, arm=Arm.left)
        print(f"Dropped the target object: {status}")
        print(f"Currently held objects: {self.magnebot.dynamic.held}")
        status = self.move_by(-1)
        print(f"Moved backwards: {status}")
        self.end()


if __name__ == "__main__":
    PickUp().run()
