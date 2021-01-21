import numpy as np
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, Arm, ActionStatus


class Tutorial(Magnebot):
    """
    In this tutorial, the Magnebot will find a small object, pick it up, and put on top of a kitchen counter.

    This controller is designed to give a new user a good understanding of how to use the Magnebot API.

    There are a few key differences between this and an actual use-case:

    1. There is some very logic to for navigation and adjusting arm movements if the action fails,
       but these approaches are very naive and won't be sufficient in most cases.
       That said, they are indicative of the sorts of algorithms you'll need to write.

    2. There is an overhead camera in this scene. While this is useful for a tutorial and for debugging,
       it will slow down an actual use-case.

    """
    def get_nearest_free_position(self, position: np.array) -> np.array:
        """
        Get the free occupancy map position closest to the given position.

        :param position: A position in worldspace coordinates.

        :return: The nearest free position on the occupancy map in worldspace coordinates.
        """

        distance = np.inf
        free_position = None
        for ix, iy in np.ndindex(self.occupancy_map.shape):
            if self.occupancy_map[ix, iy] != 0:
                continue
            x, z = self.get_occupancy_position(ix, iy)
            pos = np.array([x, 0, z])
            d = np.linalg.norm(pos - position)
            if d < distance:
                distance = d
                free_position = pos
        return free_position

    def run(self) -> None:
        """
        Find something small in the room, and a surface to put it on.

        Pick up the small object and put it on the surface.
        """

        # Load scene 2b, layout 2. See: https://github.com/alters-mit/magnebot/blob/main/doc/images/floorplans/2b_0.jpg
        # Spawn the Magnebot in room 4. See: https://github.com/alters-mit/magnebot/blob/main/doc/images/rooms/4.jpg
        self.init_scene(scene="2b", layout=2, room=4)

        # Turn the Magnebot around.
        self.turn_by(160)

        # Find something to pick up and something to put it on based on what is currently visible.
        visible_objects = self.get_visible_objects()
        small_objects = []
        target_surface = -1
        for object_id in visible_objects:
            # Get the mass of each object. If it is light enough, it's a potential target object.
            mass = self.objects_static[object_id].mass
            if mass <= 2:
                small_objects.append(object_id)
            # If an object is kinematic, it doesn't respond to physics. See: object_state.md
            # Usually, these objects are pictures hanging on the wall or built-in furniture like a countertop.
            kinematic = self.objects_static[object_id].kinematic
            if kinematic:
                target_surface = object_id
        # Sort the small objects by distance from the magnebot.
        magnebot_position = self.state.magnebot_transform.position
        small_objects = list(sorted(small_objects,
                                    key=lambda o: np.linalg.norm(magnebot_position -
                                                                 self.state.object_transforms[o].position)))
        # Set the target object to the closest of the small objects.
        target_object = small_objects[0]
        print(f"Target object is: {self.objects_static[target_object].name}\t{target_object}")
        print(f"Target surface is: {self.objects_static[target_surface].name}\t{target_surface}")

        # Go to the free position on the occupancy map closest to the target object.
        free_position = self.get_nearest_free_position(position=self.state.object_transforms[target_object].position)
        status = self.move_to(TDWUtils.array_to_vector3(free_position))
        print(f"Moved to {free_position}: {status}")
        self.turn_to(target=target_object)
        # Pick up the target object.
        status = self.grasp(target=target_object, arm=Arm.right)
        print(f"grasp(): {status}")
        # Reset the arm.
        self.reset_arm(arm=Arm.right)
        # Back up a little bit to give the Magnebot some room to turn.
        self.move_by(-0.5)

        # Get the nearest free position to the surface object.
        surface_position = self.state.object_transforms[target_surface].position
        free_position = self.get_nearest_free_position(position=surface_position)
        free_position = TDWUtils.array_to_vector3(free_position)

        # The Magnebot will collide the with the counter when it tries to go to the position.
        status = self.move_to(target=free_position)
        # Back up a bit and try again.
        num_attempts = 0
        while status == ActionStatus.collision and num_attempts < 10:
            print("Collision. Moving back a bit.")
            self.move_by(-0.4)
            self.turn_by(45)
            self.move_by(0.4)
            status = self.move_to(target=free_position)
            print(f"Attempt {num_attempts}: {status}")
            num_attempts += 1
        print("Moved to the counter.")

        # Get the position at the top of the surface and then reach slightly above that.
        top = self.objects_static[target_surface].size[1]
        reach_for_target = {"x": surface_position[0],
                            "y": top + 0.15,
                            "z": surface_position[2]}
        status = self.reach_for(target=reach_for_target, arm=Arm.right)
        # This will fail the first time. Back up just a little bit and try again.
        num_attempts = 0
        while status != ActionStatus.success and num_attempts < 10:
            # Reset the arm.
            self.reset_arm(arm=Arm.right)
            print("Failed to reach.")
            self.turn_by(-30)
            num_attempts += 1
            status = self.reach_for(target=reach_for_target, arm=Arm.right)
        print(f"Reached above the surface: {status}")
        # Drop all of the held objects (in this case, just the one object).
        for arm in self.state.held:
            for object_id in self.state.held[arm]:
                self.drop(target=object_id, arm=arm)
                print("Dropped the object.")
                # Reset the arm and back away.
                self.reset_arm(arm=arm)
        self.move_by(-1)

        # End the simulation.
        self.end()


if __name__ == "__main__":
    m = Tutorial(port=1071, screen_width=256, screen_height=256)
    m.run()
