from typing import List
from tdw.output_data import Environments as Envs
from sticky_mitten_avatar.util import get_data


class Room:
    """
    Data for a room in a scene.
    """

    def __init__(self, env: Envs, i: int):
        """
        :param env: The environments output data.
        :param i: The index of this environment in env.get_num()
        """

        """:field
        The ID of the room.
        """
        self.room_id: int = env.get_id(i)
        """:field
        The center of the room.
        """
        self.center = env.get_center(i)
        """:field
        The bounds of the room.
        """
        self.bounds = env.get_bounds(i)
        """:field
        Minimum x positional coordinate of the room.
        """
        self.x_0: float = self.center[0] - (self.bounds[0] / 2)
        """:field
        Minimum z positional coordinate of the room.
        """
        self.z_0: float = self.center[2] - (self.bounds[2] / 2)
        """:field
        Maximum x positional coordinate of the room.
        """
        self.x_1: float = self.center[0] + (self.bounds[0] / 2)
        """:field
        Maximum z positional coordinate of the room.
        """
        self.z_1: float = self.center[2] + (self.bounds[2] / 2)

    def is_inside(self, x: float, z: float) -> bool:
        """
        :param x: The x coordinate.
        :param z: The z coordinate.

        :return: True if position (x, z) is in the environment.
        """

        return self.x_0 <= x <= self.x_1 and self.z_0 <= z <= self.z_1


class SceneEnvironment:
    """
    Data for the scene environment and its rooms.
    """

    def __init__(self, resp: List[bytes]):
        """
        :param resp: The response from the build.
        """

        env = get_data(resp=resp, d_type=Envs)

        # Get the overall size of the scene.
        """:field
        Minimum x positional coordinate of the scene.
        """
        self.x_min: float = 1000
        """:field
        Maximum x positional coordinate of the scene.
        """
        self.x_max: float = 0
        """:field
        Minimum z positional coordinate of the scene.
        """
        self.z_min: float = 1000
        """:field
        Maximum z positional coordinate of the scene.
        """
        self.z_max: float = 0
        """:field
        All of the rooms in the scene.
        """
        self.rooms: List[Room] = list()
        for i in range(env.get_num()):
            e = Room(env=env, i=i)
            if e.x_0 < self.x_min:
                self.x_min = e.x_0
            if e.z_0 < self.z_min:
                self.z_min = e.z_0
            if e.x_1 > self.x_max:
                self.x_max = e.x_1
            if e.z_1 > self.z_max:
                self.z_max = e.z_1
            self.rooms.append(e)
