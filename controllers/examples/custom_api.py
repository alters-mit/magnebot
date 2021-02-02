from typing import Dict, List
import numpy as np
from tdw.output_data import Bounds
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus, Arm
from magnebot.util import get_data
from magnebot.scene_state import SceneState


class CustomAPI(Magnebot):
    """
    This is an example example of how to set up your own scene initialization recipe and add an action to the API.
    """

    def __init__(self, port: int = 1071, screen_width: int = 1024, screen_height: int = 1024):
        super().__init__(port=port, screen_height=screen_height, screen_width=screen_width, auto_save_images=True,
                         skip_frames=0)
        # The IDs of target objects.
        self.object_0: int = -1
        self.object_1: int = -1
        # The ID of a surface.
        self.surface_id: int = -1
        # The starting y positional coordinate for each object on the surface.
        self.object_y = 0.794254

    def init_scene(self, scene: str = None, layout: int = None, room: int = None,
                   width: int = 12, length: int = 12) -> ActionStatus:
        """
        Create a simple box-shaped room.

        :param scene: This parameter is ignored.
        :param layout: This parameter is ignored.
        :param room: This parameter is ignored.
        :param width: The width of the room.
        :param length: The length of the room.

        :return: An `ActionStatus` (always success).
        """

        self._clear_data()

        # Load the "ProcGenScene".
        # TDWUtils.create_empty_room() is a wrapper function for the `create_exterior_walls` command.
        # It's possible to create much more complicated scenes with this command.
        # See: `tdw/Python/example_controllers/proc_gen_room.py` for some examples.
        commands = [{"$type": "load_scene",
                     "scene_name": "ProcGenScene"},
                    TDWUtils.create_empty_room(width, length)]
        # Get the rest of the scene initialization commands.
        commands.extend(self._get_scene_init_commands(magnebot_position={"x": 0, "y": 0, "z": 0}))
        # Send all of the commands.
        resp = self.communicate(commands)
        self._cache_static_data(resp=resp)
        # Wait for the Magnebot to reset to its neutral position.
        self._do_arm_motion()
        self._end_action()

        return ActionStatus.success

    def push(self, target: int,  arm: Arm) -> ActionStatus:
        """
        This is an example custom API call.
        This will push a target object with a magnet.

        :param target: The target object.
        :param arm: The arm that the magnet is attached to.

        :return: An `ActionStatus` indicating if the arm motion was successful and if the object was pushed.
        """

        self._start_action()

        # Get the current position of the object.
        p_0 = self.state.object_transforms[target].position

        # Grasp the object.
        status = self.grasp(target=target, arm=arm)
        # We don't care if we actually grasped the object, so long as the magnet is nearby.
        if status == ActionStatus.success:
            # Immediately drop the object.
            self._append_drop_commands(object_id=target, arm=arm)

        # First, request bounds data for just the target object.
        resp = self.communicate([{"$type": "send_bounds",
                                  "ids": [target],
                                  "frequency": "once"}])
        # Get the bounds of the object. From the bounds, get the center of the object.
        bounds = get_data(resp=resp, d_type=Bounds)
        position = np.array(bounds.get_center(0))
        # Get an updated SceneState because `self.state` refers to the end of the `grasp()` action,
        # and the object might have moved.
        state = SceneState(resp=resp)

        # Get the ID of the magnet.
        magnet_id = self.magnebot_static.magnets[arm]

        # Get the position of the magnet. Note that we're using `state` (the current state),
        # not `self.state` (the state at the beginning of the action).
        magnet_position = state.joint_positions[magnet_id]

        # Get the directional vector from the magnet to the center of the object.
        direction = position - magnet_position
        direction = direction / np.linalg.norm(direction)
        # Get a position past the target object's position.
        target_position = position + (direction * 0.3)
        # Convert the target position to a Vector3 dictionary.
        target_position = TDWUtils.array_to_vector3(target_position)

        # Start the IK motion.
        # Note the `orientation_mode` and `target_orientation` parameters, which will make the arm slide laterally.
        # `do_prismatic_first` means that the torso will move up or down before the arm bends rather than the arm bends.
        # We also need to set the `state` parameter so that we're using the current state.
        status = self._start_ik(target=target_position, arm=arm, do_prismatic_first=True, orientation_mode="Z",
                                target_orientation=[1, 0, 0], state=state)
        # If the arm motion isn't possible, end the action here.
        if status != ActionStatus.success:
            self._end_action()
            return status

        # Wait for the arm to stop moving.
        # We don't need the action status returned by this function because we care about whether the object was pushed,
        # not whether the arm articulation was a "success".
        self._do_arm_motion()
        self._end_action()

        # Get the new position of the object.
        p_1 = self.state.object_transforms[target].position

        # If the object moved, then we pushed it.
        if np.linalg.norm(p_0 - p_1) > 0.1:
            return ActionStatus.success
        else:
            # This is normally used in movement actions but it's good enough for this action too.
            return ActionStatus.failed_to_move

    def run(self) -> None:
        """
        Run the example simulation.
        """

        # Initialize the scene.
        self.init_scene(width=12, length=12)

        print("Skipping 0 frames per `communicate()` call. This will slow down the simulation but is useful for "
              "debugging.")
        self.add_camera(position={"x": 1.03, "y": 2, "z": 2.34}, look_at=True, follow=True)
        print("Added a third-person camera to the scene. This will slow down the simulation but is for debugging.")

        # Go to the box.
        status = self.move_to(target=self.surface_id)
        # If we collided with the box, move back just a bit.
        if status == ActionStatus.collision:
            self.move_by(-0.1, arrived_at=0.05)
        print("Moved to the box.")
        # Pick up the first object.
        status = self.grasp(target=self.object_0, arm=Arm.right)
        print("Picked up the object.")
        # If we failed to pick up the object, turn the Magnebot a bit and try again.
        num_attempts = 0
        while status != ActionStatus.success and num_attempts < 4:
            num_attempts += 1
            self.reset_arm(arm=Arm.right, reset_torso=False)
            self.turn_by(-10)
            status = self.grasp(target=self.object_0, arm=Arm.right)
        if status != ActionStatus.success:
            print("Failed to pick up the object!")
            return
        # Reset the position of the arm but now the torso, which will slide the object away from the box.
        self.reset_arm(arm=Arm.right, reset_torso=False)
        # Push the other object.
        status = self.push(target=self.object_1, arm=Arm.left)
        print(f"Pushed the other object: {status}")
        if status != ActionStatus.success:
            return
        # Reset the arms.
        self.reset_arm(arm=Arm.left)
        self.reset_arm(arm=Arm.right)
        # Check if the object fell off the surface.
        object_y = self.state.object_transforms[self.object_1].position[1]
        if object_y < self.object_y:
            print("The object fell off the surface.")
            # Back away from the surface.
            self.move_by(-0.8)
            self.reset_arm(arm=Arm.right)
            # Go to the object.
            status = self.move_to(self.object_1)
            num_attempts = 0
            while status != ActionStatus.success and num_attempts < 4:
                num_attempts += 1
                self.turn_by(-15)
                self.move_by(-0.5)
                status = self.move_to(self.object_1)
            if status != ActionStatus.success:
                print("Failed to move to object.")
                return
            status = self.grasp(target=self.object_1, arm=Arm.left)
            self.reset_arm(arm=Arm.left)
            print(f"Grasped the object: {status}")

    def _get_scene_init_commands(self, magnebot_position: Dict[str, float] = None) -> List[dict]:
        """
        This is an example of how to add objects to a custom scene.
        """

        # Add a surface to the scene. Remember its object ID.
        self.surface_id = self._add_object(model_name="trunck",
                                           position={"x": -2.133, "y": 0, "z": 2.471},
                                           rotation={"x": 0, "y": -29, "z": 0},
                                           scale={"x": 1, "y": 0.8, "z": 1},
                                           mass=300)
        # Put two objects on top of the surface. Remember their object IDs.
        self.object_0 = self._add_object(model_name="vase_02",
                                         position={"x": -1.969, "y": 0.794254, "z": 2.336})
        self.object_1 = self._add_object(model_name="jug05",
                                         position={"x": -1.857, "y": 0.794254, "z": 2.54})

        # Get the rest of the commands (this adds the Magnebot, requests output data, etc.)
        commands = super()._get_scene_init_commands(magnebot_position=magnebot_position)
        return commands


if __name__ == "__main__":
    m = CustomAPI()
    m.run()
    m.end()
