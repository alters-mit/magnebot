import numpy as np
from tdw.tdw_utils import TDWUtils
from tdw.output_data import Bounds
from magnebot import Magnebot, ActionStatus, Arm, ArmJoint
from magnebot.scene_state import SceneState
from magnebot.util import get_data
from magnebot.ik.orientation_mode import OrientationMode
from magnebot.ik.target_orientation import TargetOrientation


class CustomAPI(Magnebot):
    """
    This is an example example of how to set up your own scene setup and arm articulation action to the API.
    """

    def __init__(self, port: int = 1071, screen_width: int = 1024, screen_height: int = 1024):
        super().__init__(port=port, screen_height=screen_height, screen_width=screen_width, auto_save_images=True,
                         skip_frames=0)
        # The IDs of target object.
        self.object_id: int = -1
        # The ID of a surface.
        self.surface_id: int = -1
        # The starting y positional coordinate for each object on the surface.
        self.object_y = 0.794254

    def init_scene(self, width: int = 12, length: int = 12) -> ActionStatus:
        """
        Create a simple box-shaped room.

        :param width: The width of the room.
        :param length: The length of the room.

        :return: An `ActionStatus` (always success).
        """

        # Load the "ProcGenScene".
        # TDWUtils.create_empty_room() is a wrapper function for the `create_exterior_walls` command.
        # It's possible to create much more complicated scenes with this command.
        # See: `tdw/Python/example_controllers/proc_gen_room.py` for some examples.
        scene = [{"$type": "load_scene",
                  "scene_name": "ProcGenScene"},
                 TDWUtils.create_empty_room(width, length)]
        # Add a surface to the scene. Remember its object ID.
        self.surface_id = self._add_object(model_name="trunck",
                                           position={"x": -2.133, "y": 0, "z": 2.471},
                                           rotation={"x": 0, "y": -29, "z": 0},
                                           scale={"x": 1, "y": 0.8, "z": 1},
                                           mass=300)
        # Put an object on top of the surface. Remember its ID.
        self.object_id = self._add_object(model_name="vase_02",
                                          position={"x": -1.969, "y": 0.794254, "z": 2.336})
        # Initialize the scene.
        return self._init_scene(scene=scene,
                                post_processing=self._get_post_processing_commands())

    def push(self, target: int,  arm: Arm) -> ActionStatus:
        """
        This is an example custom API call.
        This will push a target object with a magnet.

        :param target: The target object.
        :param arm: The arm that the magnet is attached to.

        :return: An `ActionStatus` indicating if the arm motion was successful and if the object was pushed.
        """

        self._start_action()

        # Slide the torso up and above the target object. We need to do this before calling `self._start_ik()` because
        # this action aims for the object using the position of the magnet relative to the object's position.
        torso_position = self.state.object_transforms[target].position[1] + 0.1
        # Convert the torso position from meters to prismatic joint position.
        torso_position = Magnebot._y_position_to_torso_position(torso_position)
        # Send a low-level TDW command to move the joint to the target.
        self._next_frame_commands.append({"$type": "set_prismatic_target",
                                          "joint_id": self.magnebot_static.arm_joints[ArmJoint.torso],
                                          "target": torso_position})
        # Wait for the torso to finish moving.
        self._do_arm_motion(joint_ids=[self.magnebot_static.arm_joints[ArmJoint.torso]])

        # Get center of the object.
        resp = self.communicate([{"$type": "send_bounds",
                                  "ids": [target],
                                  "frequency": "once"}])
        # Get the side on the bounds closet to the magnet.
        bounds = get_data(resp=resp, d_type=Bounds)
        center = np.array(bounds.get_center(0))
        state = SceneState(resp=resp)
        # Get the position of the magnet.
        magnet_position = state.joint_positions[self.magnebot_static.magnets[arm]]

        # Slide the torso upwards to the target height.

        # Get a position opposite the center of the object from the magnet.
        v = magnet_position - center
        v = v / np.linalg.norm(v)
        target_position = center - (v * 0.1)

        # Start the IK motion. Some notes regarding these parameters:
        #
        # - We need to explicitly set `state` because of the extra simulation step invoked by `communicate()`.
        # - `fixed_torso_prismatic` means that we'll use the position defined above rather than set it automatically.
        # - `do_prismatic_first` means that the torso will move before the rest of the arm movement.
        # - For more information re: `orientation_mode` and `target_orientation`, see `doc/arm_articulation.md`
        status = self._start_ik(target=TDWUtils.array_to_vector3(target_position),
                                arm=arm,
                                state=state,
                                fixed_torso_prismatic=torso_position,
                                do_prismatic_first=True,
                                orientation_mode=OrientationMode.x,
                                target_orientation=TargetOrientation.up)

        # If the arm motion isn't possible, end the action here.
        if status != ActionStatus.success:
            self._end_action()
            return status

        # Remember the original position of the object.
        p_0 = state.object_transforms[target].position
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
            self.move_by(-0.2, arrived_at=0.05, stop_on_collision=False)
        print("Moved to the box.")
        # Push the other object.
        status = self.push(target=self.object_id, arm=Arm.right)
        print(f"Pushed the object: {status}")
        # Reset the arms.
        self.move_by(-0.5, stop_on_collision=False)
        self.reset_arm(arm=Arm.left)
        self.reset_arm(arm=Arm.right)


if __name__ == "__main__":
    m = CustomAPI()
    m.run()
    m.end()
