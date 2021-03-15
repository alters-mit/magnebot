from typing import Dict, List
import numpy as np
from tdw.tdw_utils import TDWUtils
from tdw.output_data import Bounds
from magnebot import Magnebot, ActionStatus, Arm
from magnebot.scene_state import SceneState
from magnebot.util import get_data
from magnebot.ik.target_orientation import TargetOrientation
from magnebot.ik.orientation_mode import OrientationMode


class CustomAPI(Magnebot):
    """
    This is an example example of how to set up your own scene initialization recipe and add an action to the API.
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

        # Get a position opposite the center of the object from the magnet.
        v = magnet_position - center
        v = v / np.linalg.norm(v)
        target_position = center - (v * 0.1)
        # Slide the torso up and above the target object.
        torso_position = 0
        for k in Magnebot._TORSO_Y:
            torso_position = k
            if Magnebot._TORSO_Y[k] - 0.2 > target_position[1]:
                break

        # Remember the original position of the object.
        p_0 = state.object_transforms[target].position

        # Start the IK motion. Some notes regarding these parameters:
        # - We need to explicitly set `state` because of the extra simulation step invoked by `communicate()`.
        # - `fixed_torso_prismatic` means that we'll use the position defined above rather than set it automatically.
        # - `do_prismatic_first` means that the torso will move before the rest of the arm movement.
        # - See docstring for `self._start_ik()` regarding `orientation_mode` and `target_orientation`.
        status = self._start_ik(target=TDWUtils.array_to_vector3(target_position), arm=arm, state=state,
                                fixed_torso_prismatic=torso_position, do_prismatic_first=True,
                                target_orientation=TargetOrientation.up, orientation_mode=OrientationMode.z)
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
        # Push the other object.
        status = self.push(target=self.object_id, arm=Arm.right)
        print(f"Pushed the other object: {status}")
        if status != ActionStatus.success:
            print(f"Failed to push the other object: {status}")
            return
        print("Pushed the other object.")
        # Reset the arms.
        self.move_by(-0.5)
        self.reset_arm(arm=Arm.left)
        self.reset_arm(arm=Arm.right)

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
        # Put an object on top of the surface. Remember its ID.
        self.object_id = self._add_object(model_name="vase_02",
                                          position={"x": -1.969, "y": 0.794254, "z": 2.336})

        # Get the rest of the commands (this adds the Magnebot, requests output data, etc.)
        commands = super()._get_scene_init_commands(magnebot_position=magnebot_position)
        return commands


if __name__ == "__main__":
    m = CustomAPI()
    m.run()
    m.end()
