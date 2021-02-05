from json import loads
from pkg_resources import get_distribution
from typing import Dict, Type, TypeVar, List, Optional
from requests import get
from tdw.output_data import OutputData, Transforms, Rigidbodies, Bounds, Images, SegmentationColors, Volumes, Raycast, \
    CompositeObjects, CameraMatrices, Environments, Overlap, Version, StaticRobot, Robot, Magnebot, NavMeshPath


T = TypeVar("T", bound=OutputData)
# Output data types mapped to their IDs.
__OUTPUT_IDS: Dict[Type[OutputData], str] = {Transforms: "tran",
                                             Rigidbodies: "rigi",
                                             Bounds: "boun",
                                             Images: "imag",
                                             SegmentationColors: "segm",
                                             Volumes: "volu",
                                             Raycast: "rayc",
                                             CompositeObjects: "comp",
                                             CameraMatrices: "cama",
                                             Environments: "envi",
                                             Overlap: "over",
                                             Version: "vers",
                                             StaticRobot: "srob",
                                             Robot: "robo",
                                             Magnebot: "magn",
                                             NavMeshPath: "path"}


def get_data(resp: List[bytes], d_type: Type[T]) -> Optional[T]:
    """
    Parse the output data list of byte arrays to get a single type output data object.

    :param resp: The response from the build (a byte array).
    :param d_type: The desired type of output data.

    :return: An object of type `d_type` from `resp`. If there is no object, returns None.
    """

    if d_type not in __OUTPUT_IDS:
        raise Exception(f"Output data ID not defined: {d_type}")

    for i in range(len(resp) - 1):
        r_id = OutputData.get_data_type_id(resp[i])
        if r_id == __OUTPUT_IDS[d_type]:
            return d_type(resp[i])
    return None


def check_version(module: str = "magnebot") -> None:
    """
    Make sure that a Python module is up to date.

    :param module: The name of the module.
    """

    v_local = get_distribution(module).version
    v_remote = loads(get(f"https://pypi.org/pypi/{module}/json").content)["info"]["version"]

    if v_remote != v_local:
        print(f"You have {module} v{v_local} but version v{v_local} is available. "
              f"To upgrade:\npip3 install {module} -U")
