from enum import Enum
from typing import List, Dict, Optional
import numpy as np
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.object_manager import ObjectManager
from tdw.add_ons.step_physics import StepPhysics
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from tdw.output_data import OutputData, Transforms
from magnebot import Magnebot, Arm, ImageFrequency, ActionStatus
from magnebot.magnebot_dynamic import MagnebotDynamic


class MetaState(Enum):
    """
    The meta-state of a Magnebot i.e. which state machine it's currently evaluating.
    """

    initializing = 1
    navigation = 2
    arm_articulation = 4
    avoidance = 8
    reorienting = 16


class NavigationState(Enum):
    """
    The navigation states for a Magnebot.
    """

    moving_to_target = 1
    moving_to_center = 2
    dropping = 4
    moving_from_center = 8


class AvoidanceState(Enum):
    """
    The states for when a Magnebot is avoiding another Magnebot.
    """

    stopping = 1
    turning = 2
    moving = 4


class ArticulationState(Enum):
    """
    The states for when a Magnebot is articulating its arm.
    """

    grasping = 1
    resetting = 2


RNG = np.random.RandomState(0)


class Navigator(Magnebot):
    """
    This is a sub-class of Magnebot that uses "state machines" for basic navigation.

    The state machine flags are evaluated per frame via `on_send(resp)`.

    Note that this is a VERY primitive navigation system!
    Image capture has been totally disabled.
    The Magnebots rely on scene-state data to navigate.
    """

    ORIGIN: np.array = np.array([0, 0, 0])

    def __init__(self, robot_id: int = 0, position: Dict[str, float] = None, rotation: Dict[str, float] = None):
        # We're not using images in this simulation.
        super().__init__(robot_id=robot_id, position=position, rotation=rotation, image_frequency=ImageFrequency.never)
        # This will be set within self.update()
        self.target_id: int = -1
        # If True, the Magnebot is done and won't update its state.
        self.done: bool = False

        # These are state machine flags.
        self.meta_state: MetaState = MetaState.initializing
        self.navigation_state: NavigationState = NavigationState.moving_to_target
        self.avoidance_state: AvoidanceState = AvoidanceState.turning
        self.articulation_state: ArticulationState = ArticulationState.grasping
        # The other Magnebot. We need this to get the other Magenbot's position.
        self.other_magnebot: Optional[Magnebot] = None

    def on_send(self, resp: List[bytes]) -> None:
        super().on_send(resp=resp)
        if self.done:
            return
        # Get the position of the other Magnebot and the positions of the objects.
        if self.other_magnebot is None:
            other_magnebot_position = np.zeros(shape=3)
        else:
            other_magnebot_dynamic = MagnebotDynamic(static=self.other_magnebot.static, resp=resp, frame_count=0)
            other_magnebot_position = other_magnebot_dynamic.transform.position
        object_positions: Dict[int, np.array] = dict()
        for i in range(len(resp) - 1):
            r_id = OutputData.get_data_type_id(resp[i])
            if r_id == "tran":
                transforms = Transforms(resp[i])
                for j in range(transforms.get_num()):
                    object_positions[transforms.get_id(j)] = np.array(transforms.get_position(j))
        # Finish initializing the Magnebot.
        if self.meta_state == MetaState.initializing:
            # The Magnebot is done initializing. Go to the target object.
            if self.action.done:
                # Set the target.
                farthest_distance = -np.inf
                farthest_id = -1
                for object_id in object_positions:
                    d = np.linalg.norm(self.dynamic.transform.position - object_positions[object_id])
                    if d > farthest_distance:
                        farthest_distance = d
                        farthest_id = object_id
                self.target_id = farthest_id
                self.move_to(self.target_id)
                self.meta_state = MetaState.navigation
                self.navigation_state = NavigationState.moving_to_target
                # Ignore collisions with the objects.
                self.collision_detection.exclude_objects = list(object_positions.keys())
        # Try to navigate somewhere.
        elif self.meta_state == MetaState.navigation:
            # Check if we need to avoid the other Magnebot.
            if self.action.status == ActionStatus.collision or np.linalg.norm(self.dynamic.transform.position - other_magnebot_position) < 0.7:
                self.meta_state = MetaState.avoidance
                self.avoidance_state = AvoidanceState.stopping
                # Set collision detection.
                self.collision_detection.previous_was_same = False
                self.collision_detection.objects = False
                # Stop moving.
                self.stop()
            # Finished moving and arrived at the destination.
            elif self.action.status == ActionStatus.success:
                # Start trying to grasp the target.
                if self.navigation_state == NavigationState.moving_to_target:
                    self.meta_state = MetaState.arm_articulation
                    self.articulation_state = ArticulationState.grasping
                    self.grasp(target=self.target_id, arm=Arm.left)
                # Drop the object.
                elif self.navigation_state == NavigationState.moving_to_center:
                    self.navigation_state = NavigationState.dropping
                    self.drop(target=self.target_id, arm=Arm.left, wait_for_object=False)
                # Move away from the center.
                elif self.navigation_state == NavigationState.dropping:
                    self.navigation_state = NavigationState.moving_from_center
                    self.move_by(-2)
                # Done!
                elif self.navigation_state == NavigationState.moving_from_center:
                    self.done = True
                else:
                    raise Exception(f"Navigation state {self.navigation_state} not defined.")
            # The move action failed for some reason.
            elif self.action.status != ActionStatus.ongoing:
                self.move_to(self.target_id, arrived_offset=0.3)
        elif self.meta_state == MetaState.avoidance:
            # Done stopping. Start turning.
            if self.avoidance_state == AvoidanceState.stopping:
                self.avoidance_state = AvoidanceState.turning
                # Pick a random direction to turn.
                if RNG.random() < 0.5:
                    self.turn_by(60)
                else:
                    self.turn_by(-60)
            # Done turning. Start moving.
            if self.avoidance_state == AvoidanceState.turning:
                if self.action.status != ActionStatus.ongoing:
                    self.avoidance_state = AvoidanceState.moving
                    # Find a direction of movement that moves this Magnebot further away from the other Magnebot.
                    positive_vector = self.dynamic.transform.position + self.dynamic.transform.forward
                    negative_vector = self.dynamic.transform.position - self.dynamic.transform.forward
                    if np.linalg.norm(positive_vector - other_magnebot_position) < np.linalg.norm(
                            negative_vector - other_magnebot_position):
                        distance = -1.5
                    else:
                        distance = 1.5
                    self.move_by(distance)
            # Done moving. Resume navigation.
            elif self.avoidance_state == AvoidanceState.moving:
                if self.action.status != ActionStatus.ongoing:
                    # Set collision detection.
                    self.collision_detection.previous_was_same = True
                    self.collision_detection.objects = True
                    self.meta_state = MetaState.navigation
                    if self.navigation_state == NavigationState.moving_to_target:
                        self.move_to(self.target_id, arrived_offset=0.3)
                    elif self.navigation_state == NavigationState.moving_to_center:
                        self.move_to(Navigator.ORIGIN)
                    elif self.navigation_state == NavigationState.moving_from_center:
                        self.move_by(-2)
                    else:
                        raise Exception(f"Navigation state {self.navigation_state} not defined.")
            else:
                raise Exception(f"Avoidance state {self.avoidance_state} not defined.")
        elif self.meta_state == MetaState.arm_articulation:
            if self.articulation_state == ArticulationState.grasping:
                # Grasped the object. Reset the arm.
                if self.action.status == ActionStatus.success:
                    self.articulation_state = ArticulationState.resetting
                    self.reset_arm(arm=Arm.left)
                # Reorient and try again.
                elif self.action.status != ActionStatus.ongoing:
                    self.meta_state = MetaState.reorienting
                    self.turn_to(self.target_id)
            elif self.articulation_state == ArticulationState.resetting:
                # Done resetting. Start moving to the center.
                if self.action.status != ActionStatus.ongoing:
                    self.meta_state = MetaState.navigation
                    self.navigation_state = NavigationState.moving_to_center
                    self.move_to(target=Navigator.ORIGIN)
            else:
                raise Exception(f"Articulation state {self.articulation_state} not defined.")
        elif self.meta_state == MetaState.reorienting:
            if self.action.status != ActionStatus.ongoing:
                self.meta_state = MetaState.arm_articulation
                self.articulation_state = ArticulationState.grasping
                self.grasp(target=self.target_id, arm=Arm.left)
        else:
            raise Exception(f"Meta state {self.meta_state} not defined.")


class MultiMagnebot(Controller):
    """
    This is a basic example of a multi-agent Magnebot simulation.
    In the scene, there are two Mangebots and two objects.
    Each Magnebot needs to go to an object, pick it up, and bring it to the center of the room.

    Magnebot agents are handled in a new class, "Navigator", which navigates using a basic state machine system.
    This is commonly used in video games to yield basic agent behavior.
    It is inflexible and unsophisticated; robust Magnebot AI requires true navigation planning.
    This controller isn't an example of how to train multiple Magnebot agents.
    Rather, it's an example of how to structure your controller code for a multi-agent Magnebot simulation.
    """

    TARGET_OBJECTS: List[str] = ["vase_02", "jug04", "jug05"]

    def __init__(self, port: int = 1071, check_version: bool = True, launch_build: bool = True, random_seed: int = 0):
        super().__init__(port=port, check_version=check_version, launch_build=launch_build)
        global RNG
        RNG = np.random.RandomState(random_seed)

        commands = [TDWUtils.create_empty_room(12, 12)]
        # Add the objects.
        commands.extend(self.get_add_physics_object(model_name=RNG.choice(self.TARGET_OBJECTS),
                                                    position={"x": RNG.uniform(-0.2, 0.2), "y": 0, "z": RNG.uniform(-3, -3.3)},
                                                    rotation={"x": 0, "y": RNG.uniform(-360, 360), "z": 0},
                                                    object_id=self.get_unique_id()))
        commands.extend(self.get_add_physics_object(model_name=RNG.choice(self.TARGET_OBJECTS),
                                                    position={"x": RNG.uniform(-0.2, 0.2), "y": 0, "z": RNG.uniform(3, 3.3)},
                                                    rotation={"x": 0, "y": RNG.uniform(-360, 360), "z": 0},
                                                    object_id=self.get_unique_id()))
        # Add an object manager.
        self.object_manager: ObjectManager = ObjectManager()
        # Skip physics frames.
        step_physics: StepPhysics = StepPhysics(num_frames=10)
        # Add the Magnebots.
        self.m0: Navigator = Navigator(position={"x": 0, "y": 0, "z": -1.5},
                                       robot_id=0)
        self.m1: Navigator = Navigator(position={"x": 0, "y": 0, "z": 1},
                                       rotation={"x": 0, "y": 180, "z": 0},
                                       robot_id=1)
        # Add a camera.
        camera: ThirdPersonCamera = ThirdPersonCamera(position={"x": -2, "y": 9, "z": -6},
                                                      avatar_id="a",
                                                      look_at=self.m1.robot_id)
        self.add_ons.extend([self.object_manager, step_physics, self.m0, self.m1, camera])
        self.communicate(commands)
        # Set the other Magnebot.
        self.m0.other_magnebot = self.m1
        self.m1.other_magnebot = self.m0

    def run(self) -> None:
        """
        Iterate through the simulation until the Magnebots are done.
        """

        while not self.m0.done or not self.m1.done:
            # Advance the simulation and update the Magnebots.
            self.communicate([])
        self.communicate({"$type": "terminate"})


if __name__ == "__main__":
    c = MultiMagnebot()
    c.run()
