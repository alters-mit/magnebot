# ObjectStatic

`from magnebot.object_static import ObjectStatic`

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

- `object_id` The unique ID of the object.

- `name` [The name of the model.](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/librarian/model_librarian.md)

- `category` The semantic category of the object.

- `kinematic` If True, this object is kinematic, and won't respond to physics. Example: a painting hung on a wall.

- `segmentation_color` The RGB segmentation color for the object as a numpy array: `[r, g, b]`

- `mass` The mass of the object.

- `size` The size of the object as a numpy array: `[width, height, length]`

***

## Functions

#### \_\_init\_\_

**`def __init__(self, name: str, object_id: int, mass: float, segmentation_color: np.array, size: np.array)`**

| Parameter | Description |
| --- | --- |
| name | The name of the object. |
| object_id | The unique ID of the object. |
| mass | The mass of the object. |
| segmentation_color | The segmentation color of the object. |
| size | The size of the object. |

