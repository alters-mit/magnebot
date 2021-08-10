from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
from magnebot import Magnebot


class MagnebotColorSegmentation(Magnebot):
    """
    Test whether the Magnebot body parts receive segmentation colors.
    """

    def get_id_pass(self) -> None:
        """
        Use a third person camera to generate a segmentation color image that includes the Magnebot.
        """

        self._start_action()
        self._next_frame_commands.append({"$type": "set_pass_masks",
                                          "pass_masks": ["_id"],
                                          "avatar_id": "c"})
        self._end_action()
        img = Image.open(BytesIO(self.state.third_person_images["c"]["id"]))
        plt.imshow(img)
        plt.show()


if __name__ == "__main__":
    m = MagnebotColorSegmentation()
    m.init_scene()
    m.add_camera(position={"x": -1.73, "y": 1.94, "z": 1.87}, look_at=True)
    m.get_id_pass()
    m.end()
