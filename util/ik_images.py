from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from magnebot import Arm
from magnebot.paths import IK_ORIENTATIONS_RIGHT_PATH, IK_ORIENTATIONS_LEFT_PATH, IK_POSITIONS_PATH
from magnebot.ik.orientation import ORIENTATIONS

"""
Visualize the pre-calculated IK orientation solutions as colorized vertical slices.
Each position is a circle on the image. Each image is a region at a given y value.
Each position is colorized to indicate the orientation mode + target orientation solution.
These images are saved to: `doc/images/ik`
"""


if __name__ == "__main__":
    ik_images_directory = Path("../doc/images/ik")
    # This color palette is used to colorize each orientation.
    # Source: https://github.com/onivim/oni/blob/master/extensions/theme-onedark/colors/onedark.vim
    colors = [(171, 178, 191), (224, 108, 117), (190, 80, 70), (152, 195, 121), (229, 192, 123), (209, 154, 102),
              (97, 175, 239), (198, 120, 221), (86, 182, 194), (99, 109, 131)]
    # Draw a colorized legend for the orientation images.
    font_path = "fonts/inconsolata/Inconsolata_Expanded-Regular.ttf"
    legend_font = ImageFont.truetype(font_path, 14)
    legend = Image.new('RGB', (128, 220))
    draw = ImageDraw.Draw(legend)
    y = 8
    x = 8
    draw.text((x, y), "Key:", font=legend_font, anchor="mg", fill=(171, 178, 191))
    y += 24
    x += 8
    for color, o in zip(colors, ORIENTATIONS):
        draw.text((x, y), str(o), font=legend_font, anchor="mb", fill=color)
        y += 18
    # Save the color legend.
    legend.save(str(ik_images_directory.joinpath("legend.jpg")))

    # Load the positions.
    positions = np.load(str(IK_POSITIONS_PATH.resolve()))
    # The width of the image in pixels.
    d = 256
    # The radius of each circle.
    r = 12
    # Make images for each arm.
    for arm, path in zip([Arm.left, Arm.right], [IK_ORIENTATIONS_LEFT_PATH, IK_ORIENTATIONS_RIGHT_PATH]):
        orientations = np.load(str(path.resolve()))
        directory = ik_images_directory.joinpath(arm.name)
        # Get vertical slices of the point cloud.
        for y in np.arange(0, 1.6, step=0.1):
            image = Image.new('RGB', (d, 300))
            draw = ImageDraw.Draw(image)
            x = 0
            # Draw the title text.
            header_font = ImageFont.truetype(font_path, 18)
            header = f"y = {round(y, 1)}"
            header_size = header_font.getsize(header)
            header_x = int((d / 2) - (header_size[0] / 2))
            header_y = 8
            draw.text((header_x, header_y), header, font=header_font, anchor="mg", fill=(171, 178, 191))
            for p, o in zip(positions, orientations):
                # Only include positions with the correct y value.
                if o < -0.01 or np.abs(y - p[1]) > 0.01:
                    continue
                # Convert the position to image coordinates.
                x = d * (1 - ((1 - p[0]) / 2)) - 6
                # Add a little padding to position this below the header text.
                z = d * (1 - ((1 - p[2]) / 2)) + 30
                # Draw a circle to mark the position. Colorize the orientation.
                draw.rectangle((x, z, x + r, z + r), fill=colors[o], outline=colors[o])
            # Save the image.
            image.save(str(directory.joinpath(f"{round(y, 1)}.jpg").resolve()))
