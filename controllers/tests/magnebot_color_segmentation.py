import matplotlib.pyplot as plt
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from tdw.add_ons.image_capture import ImageCapture
from tdw.backend.paths import EXAMPLE_CONTROLLER_OUTPUT_PATH
from magnebot import MagnebotController


class MagnebotColorSegmentation(MagnebotController):
    """
    Test whether the Magnebot body parts receive segmentation colors.
    """

    def get_id_pass(self) -> None:
        """
        Use a third person camera to generate a segmentation color image that includes the Magnebot.
        """

        camera = ThirdPersonCamera(position={"x": -1.73, "y": 1.94, "z": 1.87}, look_at=self.magnebot.robot_id)
        path = EXAMPLE_CONTROLLER_OUTPUT_PATH.joinpath("magnebot_segmentation_colors")
        capture = ImageCapture(avatar_ids=[camera.avatar_id], pass_masks=["_id"], path=path)
        self.add_ons.extend([camera, capture])
        self.communicate([])
        img = capture.get_pil_images()[camera.avatar_id]["_id"]
        plt.imshow(img)
        plt.show()


if __name__ == "__main__":
    m = MagnebotColorSegmentation()
    m.init_scene()
    m.get_id_pass()
    m.end()
