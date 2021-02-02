from io import BytesIO
from PIL import Image
from pathlib import Path
from typing import List, Dict, Optional, Union
import numpy as np
from tdw.output_data import OutputData, Robot, Transforms, CameraMatrices, Images, Magnebot
from tdw.tdw_utils import TDWUtils
from magnebot.arm import Arm
from magnebot.transform import Transform
from magnebot.util import get_data


class SceneState:
    """
    Data for the current state of the scene.
    This is used internally to monitor the status of the scene and Magnebot during an action.
    This is cached in the controller at the end an action as the most-recent state.

    ```python
    from magnebot import Magnebot

    m = Magnebot()
    m.init_scene(scene="2a", layout=1, room=1)
    m.move_by(1)

    # m.state is the SceneState of the most-recent frame.
    # Save the image.
    m.state.save_images(output_directory="dist")

    m.end()
    ```
    """

    """:class_var
    The current frame count. This updates every time the scene is reset (see `Magnebot.init_scene()`) or when an action (such as `Magnebot.move_by()`) ends.
    """
    FRAME_COUNT: int = 0

    def __init__(self, resp: List[bytes]):
        """
        :param resp: The response from the build.
        """

        r = get_data(resp=resp, d_type=Robot)
        # Get data for the robot.
        """:field
        The [transform data](transform.md) of the Magnebot.

        ```python
        from magnebot import Magnebot

        m = Magnebot()
        m.init_scene(scene="2a", layout=1, room=1)
        print(m.state.magnebot_transform.position)
        ```
        """
        self.magnebot_transform: Transform = Transform(position=np.array(r.get_position()),
                                                       rotation=np.array(r.get_rotation()),
                                                       forward=np.array(r.get_forward()))
        """:field
        The `[x, y, z]` coordinates of the Magnebot's joints as numpy arrays. Key = The ID of the joint.

        ```python
        from magnebot import Magnebot
    
        m = Magnebot()
        m.init_scene(scene="2a", layout=1, room=1)
        for j_id in m.state.joint_positions:
            position = m.state.joint_positions[j_id]
            name = m.magnebot_static.joints[j_id].name
            print(position, name)
        ```
        """
        self.joint_positions: Dict[int, np.array] = dict()
        """:field
        The angles of each Magnebot joint. Key = The ID of the joint. Value = The angles of the joint in degrees as a numpy array. This is mainly useful for the backend code.
        """
        self.joint_angles: Dict[int, np.array] = dict()
        # Get data for the robot body parts.
        for i in range(r.get_num_joints()):
            j_id = r.get_joint_id(i)
            self.joint_positions[j_id] = r.get_joint_position(i)
            self.joint_angles[j_id] = r.get_joint_positions(i)

        m = get_data(resp=resp, d_type=Magnebot)
        """:field
        A dictionary of object IDs currently held by the Magnebot. Key = The arm. Value = a numpy array of object IDs.

        ```python
        from magnebot import Magnebot, Arm
    
        m = Magnebot()
        m.init_scene(scene="2a", layout=1, room=1)
        print(m.state.held[Arm.left]) # []
        ```
        """
        self.held: Dict[Arm, np.array] = {Arm.left: m.get_held_left(),
                                          Arm.right: m.get_held_right()}

        # Get object data.
        transforms = get_data(resp=resp, d_type=Transforms)
        """:field
        A dictionary of object [transform data](transform.md). Key = the object ID. 
        The `position` is always the rotated bottom-center of the object.

        ```python
        from magnebot import Magnebot

        m = Magnebot()
        m.init_scene(scene="2a", layout=1, room=1)
        
        # Print the position of each object.
        for object_id in m.state.object_transforms:
            print(m.state.object_transforms[object_id].position)
        ```
        """
        self.object_transforms: Dict[int, Transform] = dict()
        for i in range(transforms.get_num()):
            self.object_transforms[transforms.get_id(i)] = Transform(position=np.array(transforms.get_position(i)),
                                                                     forward=np.array(transforms.get_forward(i)),
                                                                     rotation=np.array(transforms.get_rotation(i)))

        # Get camera matrix data.
        matrices = get_data(resp=resp, d_type=CameraMatrices)
        """:field
        The [camera projection matrix](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/output_data.md#cameramatrices) of the Magnebot's camera as a numpy array.
        """
        self.projection_matrix: Optional[np.array] = None
        """:field
        The [camera matrix](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/output_data.md#cameramatrices) of the Magnebot's camera as a numpy array.
        """
        self.camera_matrix: Optional[np.array] = None
        if matrices is not None:
            self.projection_matrix = matrices.get_projection_matrix()
            self.camera_matrix = matrices.get_camera_matrix()

        # Get the image data.
        """:field
        The images rendered by the robot as dictionary. Key = the name of the pass. Value = the pass as a numpy array.
        
        When a `SceneState` is created during an action, this is often empty. `Magnebot.state.images` always contains images.
        
        ```python
        from magnebot import Magnebot

        m = Magnebot(id_pass=True)
        m.init_scene(scene="2a", layout=1, room=1)

        # Get the ID pass.
        id_pass = m.state.images["id"]
        ```
        
        | Pass | Image | Description |
        | --- | --- | --- |
        | `"img"` | ![](images/pass_masks/img_0.jpg) | The rendered image. |
        | `"id"` | ![](images/pass_masks/id_0.png) | The object color segmentation pass. See `Magnebot.segmentation_color_to_id` and `Magnebot.objects_static` to map segmentation colors to object IDs. |
        | `"depth"` | ![](images/pass_masks/depth_0.png) | The depth values per pixel as a numpy array. Depth values are encoded into the RGB image; see `SceneState.get_depth_values()`. Use the camera matrices to interpret this data. |

        """
        self.images: Dict[str, np.array] = dict()

        # File extensions per pass.
        self.__image_extensions: Dict[str, str] = dict()

        """:field
        Images rendered by third-person cameras as dictionary. Key = The camera ID. Value: A dictionary of image passes, structured exactly like `images` (see above).
        """
        self.third_person_images: Dict[str: Dict[str, np.array]] = dict()

        got_magnebot_images = False
        for i in range(0, len(resp) - 1):
            if OutputData.get_data_type_id(resp[i]) == "imag":
                images = Images(resp[i])
                avatar_id = images.get_avatar_id()
                # Save third-person camera images.
                if avatar_id != "a":
                    if avatar_id not in self.third_person_images:
                        self.third_person_images[avatar_id] = dict()
                    for j in range(images.get_num_passes()):
                        image_data = images.get_image(j)
                        pass_mask = images.get_pass_mask(j)
                        if pass_mask == "_depth":
                            image_data = TDWUtils.get_shaped_depth_pass(images=images, index=j)
                        self.third_person_images[avatar_id][pass_mask[1:]] = image_data
                # Save robot images.
                else:
                    got_magnebot_images = True
                    for j in range(images.get_num_passes()):
                        image_data = images.get_image(j)
                        pass_mask = images.get_pass_mask(j)
                        if pass_mask == "_depth":
                            image_data = TDWUtils.get_shaped_depth_pass(images=images, index=j)
                        # Remove the underscore from the pass mask such as: _img -> img
                        pass_name = pass_mask[1:]
                        # Save the image data.
                        self.images[pass_name] = image_data
                        # Record the file extension.
                        self.__image_extensions[pass_name] = images.get_extension(j)
        # Update the frame count.
        if got_magnebot_images:
            SceneState.FRAME_COUNT += 1

    def save_images(self, output_directory: Union[str, Path]) -> None:
        """
        Save the ID pass (segmentation colors) and the depth pass to disk.
        Images will be named: `[frame_number]_[pass_name].[extension]`
        For example, the depth pass on the first frame will be named: `00000000_depth.png`

        The `img` pass is either a .jpg or a .png file (see [the `img_is_png` parameter in the Magnebot constructor](magnebot_controller.md)). The `id` and `depth` passes are .png files.

        :param output_directory: The directory that the images will be saved to.
        """

        if isinstance(output_directory, str):
            output_directory = Path(output_directory)
        if not output_directory.exists():
            output_directory.mkdir(parents=True)
        # The prefix is a zero-padded integer to ensure sequential images.
        prefix = TDWUtils.zero_padding(SceneState.FRAME_COUNT, 8)
        # Save each image.
        for pass_name in self.images:
            if self.images[pass_name] is None:
                continue
            # Get the filename, such as: `00000000_img.png`
            p = output_directory.joinpath(f"{prefix}_{pass_name}.{self.__image_extensions[pass_name]}")
            if pass_name == "depth":
                Image.fromarray(self.images[pass_name]).save(str(p.resolve()))
            else:
                with p.open("wb") as f:
                    f.write(self.images[pass_name])

    def get_pil_images(self) -> dict:
        """
        Convert each image pass from the robot camera to PIL images.

        :return: A dictionary of PIL images. Key = the pass name (img, id, depth); Value = The PIL image (can be None)
        """

        images = dict()
        for pass_name in self.images:
            if pass_name == "depth":
                images[pass_name] = Image.fromarray(self.images[pass_name])
            else:
                images[pass_name] = Image.open(BytesIO(self.images[pass_name]))
        return images

    def get_depth_values(self) -> np.array:
        """
        Convert the depth pass to depth values. Can be None if there is no depth image data.

        :return: A decoded depth pass as a numpy array of floats.
        """

        if "depth" in self.images:
            return TDWUtils.get_depth_values(self.images["depth"])
        else:
            return None

    def get_point_cloud(self) -> np.array:
        """
        Returns a point cloud from the depth pass. Can be None if there is no depth image data.

        :return: A decoded depth pass as a numpy array of floats.
        """

        if "depth" in self.images:
            return TDWUtils.get_point_cloud(depth=TDWUtils.get_depth_values(self.images["depth"]),
                                            camera_matrix=self.camera_matrix, far_plane=100, near_plane=1)
        else:
            return None
