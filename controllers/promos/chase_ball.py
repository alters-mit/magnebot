from enum import Enum
import numpy as np
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.robot import Robot
from tdw.add_ons.collision_manager import CollisionManager
from tdw.add_ons.object_manager import ObjectManager
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from tdw.add_ons.image_capture import ImageCapture
from tdw.backend.paths import EXAMPLE_CONTROLLER_OUTPUT_PATH
from magnebot import Magnebot, Arm, ActionStatus, ImageFrequency, MagnebotController


class State(Enum):
    initializing = 1
    swinging = 2
    moving_to_ball = 3
    grasping = 4
    resetting_success = 5
    resetting_failure = 6
    moving_to_robot = 7
    dropping = 8
    backing_away = 9
    backing_away_from_wall = 10
    backing_away_from_wall_with_ball = 12


class ChaseBall(Controller):
    """
    Add a UR5 robot, a Magnebot and a ball.
    The robot will swing at the ball. The Magnebot will chase the ball and return it to the robot.

    This is a "promo" controller rather than an "example" controller for several reasons:

    - It uses a very state machine to manage behavior that is probably too simple for actual use-cases.
    - It includes per-frame image capture which is very slow.
    """

    def __init__(self, port: int = 1071, check_version: bool = True, launch_build: bool = True):
        super().__init__(port=port, check_version=check_version, launch_build=launch_build)

        # Add the robot, the Magnebot, and an object manager.
        self.robot: Robot = Robot(robot_id=self.get_unique_id(), name="ur5", position={"x": -1.4, "y": 0, "z": 2.6})
        self.magnebot: Magnebot = Magnebot(robot_id=self.get_unique_id(), position={"x": -1.4, "y": 0, "z": -1.1},
                                           image_frequency=ImageFrequency.never)
        self.object_manager: ObjectManager = ObjectManager()
        # Add a ball.
        self.ball_id: int = self.get_unique_id()
        # Add a camera and enable image capture.
        self.camera: ThirdPersonCamera = ThirdPersonCamera(position={"x": 0, "y": 10, "z": -1},
                                                           look_at={"x": 0, "y": 0, "z": 0},
                                                           avatar_id="a")
        images_path = EXAMPLE_CONTROLLER_OUTPUT_PATH.joinpath("chase_ball")
        print(f"Images will be saved to: {images_path}")
        image_capture = ImageCapture(avatar_ids=[self.camera.avatar_id], path=images_path)
        self.add_ons.extend([self.robot, self.magnebot, self.object_manager, self.camera, image_capture])

        # Don't add this just yet! The robot initializes at a position that intersects with the floor.
        # If you request collision data now, the build will crash.
        self.collision_manager = CollisionManager()

        # Create the scene.
        commands = [TDWUtils.create_empty_room(9, 9),
                    self.get_add_material("parquet_long_horizontal_clean",
                                          library="materials_high.json"),
                    {"$type": "set_proc_gen_floor_material",
                     "name": "parquet_long_horizontal_clean"},
                    {"$type": "set_proc_gen_floor_texture_scale",
                     "scale": {"x": 3, "y": 3}},
                    {"$type": "set_screen_size",
                     "width": 1024,
                     "height": 1024},
                    {"$type": "rotate_directional_light_by",
                     "angle": 30,
                     "axis": "pitch"}]
        # Add post-processing.
        commands.extend(MagnebotController.get_default_post_processing_commands())
        commands.extend(self.get_add_physics_object(model_name="prim_sphere",
                                                    library="models_special.json",
                                                    object_id=self.ball_id,
                                                    position={"x": -0.871, "y": 0.1, "z": 3.189},
                                                    scale_factor={"x": 0.2, "y": 0.2, "z": 0.2},
                                                    default_physics_values=False,
                                                    dynamic_friction=0.1,
                                                    static_friction=0.1,
                                                    bounciness=0.7,
                                                    mass=10))
        self.communicate(commands)
        self.state = State.initializing
        self._frame: int = 0

    def run(self):
        done = False
        while not done:
            self.communicate([])
            # Initialize the robots.
            if self.state == State.initializing:
                # Stop initializing and start swinging.
                if not self.robot.joints_are_moving() and self.magnebot.action.status != ActionStatus.ongoing:
                    # Now that the robot isn't intersecting with the floor, it is safe to request collision data.
                    self.add_ons.append(self.collision_manager)
                    # Rotate the shoulder to swing at the ball.
                    self.robot.set_joint_targets(targets={self.robot.static.joint_ids_by_name["shoulder_link"]: -70})
                    self.state = State.swinging
            elif self.state == State.swinging:
                for collision in self.collision_manager.obj_collisions:
                    # A robot joint collided with the ball.
                    if (collision.int1 in self.robot.static.joints and collision.int2 == self.ball_id) or \
                            (collision.int2 in self.robot.static.joints and collision.int1 == self.ball_id):
                        # Start moving the Magnebot towards the ball.
                        self.state = State.moving_to_ball
                        self.magnebot.move_to(target=self.ball_id, arrived_offset=0.3)
                        # Reset the robot.
                        self.robot.set_joint_targets(targets={self.robot.static.joint_ids_by_name["shoulder_link"]: 0})
            elif self.state == State.moving_to_ball:
                # Collided with a wall. Back away.
                if self.magnebot.action.status == ActionStatus.collision:
                    self.state = State.backing_away_from_wall
                    self.magnebot.move_by(-2)
                else:
                    self._frame += 1
                    # Every so often, course-correct the Magnebot.
                    if self._frame % 15 == 0:
                        # If the Magnebot is near the ball, try to pick it up.
                        if np.linalg.norm(self.object_manager.transforms[self.ball_id].position -
                                          self.magnebot.dynamic.transform.position) < 0.9:
                            self.state = State.grasping
                            self.magnebot.grasp(target=self.ball_id, arm=Arm.right)
                        # Course-correct.
                        else:
                            self.magnebot.move_to(target=self.ball_id, arrived_offset=0.3)
            elif self.state == State.backing_away_from_wall:
                # Finished backing away from the wall. Resume the chase.
                if self.magnebot.action.status != ActionStatus.ongoing:
                    self.magnebot.move_to(target=self.ball_id, arrived_offset=0.3)
                    self._frame = 0
                    self.state = State.moving_to_ball
            elif self.state == State.grasping:
                # Caught the object! Reset the arm.
                if self.magnebot.action.status == ActionStatus.success:
                    self.state = State.resetting_success
                    self.magnebot.reset_arm(arm=Arm.right)
                # Failed to grasp the object. Reset the arm.
                elif self.magnebot.action.status != ActionStatus.ongoing:
                    self.state = State.resetting_failure
                    self.magnebot.reset_arm(arm=Arm.right)
            elif self.state == State.resetting_failure:
                # Try moving to the object again.
                if self.magnebot.action.status != ActionStatus.ongoing:
                    self.state = State.moving_to_ball
                    self.magnebot.move_to(target=self.ball_id, arrived_offset=0.3)
                    self._frame = 0
            elif self.state == State.resetting_success:
                # The arm has been reset. Back away from the wall.
                if self.magnebot.action.status != ActionStatus.ongoing:
                    self.state = State.backing_away_from_wall_with_ball
                    self.magnebot.move_by(-3)
            elif self.state == State.backing_away_from_wall_with_ball:
                # The Magnebot has backed away from the wall. Move towards the robot.
                if self.magnebot.action.status != ActionStatus.ongoing:
                    self.state = State.moving_to_robot
                    self.magnebot.move_to(target={"x": -0.871, "y": 0, "z": 3}, arrived_offset=0.1)
            elif self.state == State.moving_to_robot:
                # The Magnebot has arrived at the robot. Drop the object.
                if self.magnebot.action.status != ActionStatus.ongoing:
                    self.state = State.dropping
                    self.magnebot.collision_detection.objects = False
                    self.magnebot.collision_detection.walls = False
                    self.magnebot.drop(target=self.ball_id, arm=Arm.right)
            elif self.state == State.dropping:
                # The Magnebot has dropped the object. Move away from the robot.
                if self.magnebot.action.status != ActionStatus.ongoing:
                    self.state = State.backing_away
                    self.magnebot.move_by(-2)
                    # Swing again.
                    self.robot.set_joint_targets(targets={self.robot.static.joint_ids_by_name["shoulder_link"]: -70})
            elif self.state == State.backing_away:
                # The Magnebot has moved away from the robot. We're done!
                if self.magnebot.action.status != ActionStatus.ongoing and not self.robot.joints_are_moving():
                    done = True
        self.communicate({"$type": "terminate"})

    def _get_midpoint(self) -> np.array:
        """
        :return: The midpoint between the Magenbot and the ball.
        """

        return np.array([(self.magnebot.dynamic.transform.position[0] +
                          self.object_manager.transforms[self.ball_id].position[0]) / 2,
                         0.5,
                         (self.magnebot.dynamic.transform.position[2] +
                          self.object_manager.transforms[self.ball_id].position[2]) / 2])


if __name__ == "__main__":
    c = ChaseBall()
    c.run()
