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
    """

    # Objects that we can assume are kinematic.
    __KINEMATIC = ['24_in_wall_cabinet_white_wood', '24_in_wall_cabinet_wood_beach_honey', 'aquostv',
                   'cabinet_24_two_drawer_white_wood', 'cabinet_24_two_drawer_wood_beach_honey',
                   'cabinet_24_white_wood', 'cabinet_24_wood_beach_honey', 'cabinet_36_white_wood',
                   'cabinet_36_wood_beach_honey', 'cabinet_full_height_white_wood',
                 'cabinet_full_height_wood_beach_honey', 'elf_painting', 'framed_painting', 'fruit_basket',
                 'its_about_time_painting', 'silver_frame_painting', 'sink_base_white_wood',
                 'sink_base_wood_beach_honey']

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

        """:field
        The unique ID of the object.
        """
        self.object_id = object_id
        """:field
        [The name of the model.](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/librarian/model_librarian.md)
        """
        self.name = name.lower()
        """:field
        The semantic category of the object.
        """
        self.category = ObjectStatic.__CATEGORIES[self.name]
        """:field
        If True, this object is kinematic, and won't respond to physics. 
        Examples: a painting hung on a wall or built-in furniture like a countertop.
        """
        self.kinematic = self.name in ObjectStatic.__KINEMATIC
        """:field
        The RGB segmentation color for the object as a numpy array: `[r, g, b]`
        """
        self.segmentation_color = segmentation_color
        """:field
        The mass of the object.
        """
        self.mass = mass
        """:field
        The size of the object as a numpy array: `[width, height, length]`
        """
        self.size = size
