from json import loads
from pkg_resources import get_distribution
from typing import Dict, Type, TypeVar, List, Optional
from requests import get
from tdw.output_data import OutputData, Transforms, Rigidbodies, Bounds, Images, SegmentationColors, Volumes, Raycast, \
    CameraMatrices, SceneRegions, Overlap, Version, StaticRobot, Magnebot, NavMeshPath, \
    ScreenPosition, AudioSources, AvatarKinematic, ImageSensors


T = TypeVar("T", bound=OutputData)
# Output data types mapped to their IDs.
__OUTPUT_IDS: Dict[Type[OutputData], str] = {Transforms: "tran",
                                             Rigidbodies: "rigi",
                                             Bounds: "boun",
                                             Images: "imag",
                                             SegmentationColors: "segm",
                                             Volumes: "volu",
                                             Raycast: "rayc",
                                             CameraMatrices: "cama",
                                             SceneRegions: "sreg",
                                             Overlap: "over",
                                             Version: "vers",
                                             StaticRobot: "srob",
                                             Magnebot: "magn",
                                             NavMeshPath: "path",
                                             ScreenPosition: "scre",
                                             AudioSources: "audi",
                                             AvatarKinematic: "avki",
                                             ImageSensors: "imse"}


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
        print(f"You have {module} v{v_local} but version v{v_remote} is available. "
              f"To upgrade:\npip3 install {module} -U")


def get_default_post_processing_commands() -> List[dict]:
    """
    :return: The default post-processing commands.
    """

    return [{"$type": "set_aperture",
             "aperture": 8.0},
            {"$type": "set_focus_distance",
             "focus_distance": 2.25},
            {"$type": "set_post_exposure",
             "post_exposure": 0.4},
            {"$type": "set_ambient_occlusion_intensity",
             "intensity": 0.175},
            {"$type": "set_ambient_occlusion_thickness_modifier",
             "thickness": 3.5},
            {"$type": "set_shadow_strength",
             "strength": 1.0}]
