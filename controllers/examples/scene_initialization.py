from magnebot import MagnebotController

"""
This is a simple example of how to initialize an interior environment populated by furniture, objects, and a Magnebot.
"""

if __name__ == "__main__":
    # Instantiate the controller.
    m = MagnebotController()
    # Initialize the scene. Populate it with objects. Spawn the Magnebot in a room.
    m.init_floorplan_scene(scene="2a", layout=1, room=1)
    # Show the rendered image.
    pil_images = m.magnebot.get_pil_images()
    pil_images["img"].show()
    # End the simulation.
    m.end()
