import numpy as np
from json import loads
from magnebot.paths import OBJECT_CATEGORIES_PATH


class ObjectStatic:
    """
    Info for an object that doesn't change between frames, such as its ID and mass.

    ```python
    from magnebot import Magnebot

    m = Magnebot()
    m.init_scene(scene="2a", layout=1)

    # Print each object ID and segmentation color.
    for object_id in m.objects_static:
        o = m.objects_static[object_id]
        print(object_id, o.segmentation_color)
    ```

    ***

    ## Fields

    - `object_id`: The unique ID of the object.
    - `mass`: The mass of the object.
    - `segmentation_color`: The RGB segmentation color for the object as a numpy array: `[r, g, b]`
    - `name`: [The name of the model.](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/librarian/model_librarian.md)
    - `category`: The semantic category of the object.
    - `kinematic`: If True, this object is kinematic, and won't respond to physics. Example: a painting hung on a wall.
    - `size`: The size of the object as a numpy array: `[width, height, length]`

    ***

    ## Functions

    """

    # Objects that we can assume are kinematic.
    __KINEMATIC = ['24_in_wall_cabinet_white_wood', '24_in_wall_cabinet_wood_beach_honey',
                   '36_in_wall_cabinet_white_wood', '36_in_wall_cabinet_wood_beach_honey', 'blue_rug',
                   'cabinet_24_door_drawer_wood_beach_honey', 'cabinet_24_singledoor_wood_beach_honey',
                   'cabinet_24_two_drawer_white_wood', 'cabinet_24_two_drawer_wood_beach_honey',
                   'cabinet_24_white_wood', 'cabinet_24_wood_beach_honey', 'cabinet_36_white_wood',
                   'cabinet_36_wood_beach_honey', 'cabinet_full_height_white_wood',
                   'cabinet_full_height_wood_beach_honey', 'carpet_rug', 'elf_painting', 'flat_woven_rug',
                   'framed_painting', 'fruit_basket', 'its_about_time_painting', 'purple_woven_rug',
                   'silver_frame_painting']
    # A dictionary of object categories. Key = object name. Value = category.
    __CATEGORIES = loads(OBJECT_CATEGORIES_PATH.read_text(encoding="utf-8"))

    def __init__(self, name: str, object_id: int, mass: float, segmentation_color: np.array, size: np.array):
        """
        :param name: The name of the object.
        :param object_id: The unique ID of the object.
        :param mass: The mass of the object.
        :param segmentation_color: The segmentation color of the object.
        :param size: The size of the object.
        """

        self.object_id = object_id
        self.name = name.lower()
        self.kinematic = self.name in ObjectStatic.__KINEMATIC
        self.segmentation_color = segmentation_color
        self.mass = mass
        self.size = size
        self.category = ObjectStatic.__CATEGORIES[self.name]
