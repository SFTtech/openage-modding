#!/usr/bin/env python3

# Copyright 2018-2018 the openage authors. See copying.md for legal info.

"""

This script takes a flat AoC texture (481x481) and scales it to
HD texture size (512x512).

The way the developers did this was by taking specific
rows/columns and then "doubling" them, thereby enlarging the
image without the need for upscaling.

Example:

ABCD
EFGH
IJKL
MNOP

Let this be a 4x4 image where each letter represents a pixel. We
double the 2nd row like this:

ABCD
EFGH
EFGH
IJKL
MNOP

The same can be done for the 2nd column:

ABBCD
EFFGH
EFFGH
IJJKL
MNNOP

By doubling you get a 5x5 image.

Pillow is required for image manipulation. Install with pip:

    $ pip install pillow
"""

import argparse
import sys
from PIL import Image

def main():
    """
    CLI entry point
    """

    args = get_args()

    inputfile = args.inputfile

    aoc_texture = Image.open(inputfile)

    check_file(aoc_texture)

    hd_texture = upscale(aoc_texture)

    to_file(hd_texture, inputfile)

    return 0

def get_args():
    """
    Get CLI arguments.
    """

    parser = argparse.ArgumentParser(description=("Scale terrain texture from AoC to HD "
                                                  "format"))
    parser.add_argument('inputfile', help="The terrain texture from AoC")
    return parser.parse_args()

def upscale(aoc_texture):
    """
    Upscale from original texture size
    """

    hd_texture = Image.new('RGBA', (514, 514), (255, 255, 255, 0))

    aoc_pixels = aoc_texture.load()
    hd_pixels = hd_texture.load()

    # offsets for doubling
    offset_y = 0
    offset_x = 0

    # iterator for counting up until double_width_*
    # is reached. Starts at 7 because the first doubled
    # row/column appears at (7,y)/(x,7)
    offset_iterator_x = 7
    offset_iterator_y = 7

    # the width between two rows/columns which are supposed
    # to be doubled. It alternates between the values 15
    # and 16 (except for offset_* == 22)
    double_width_x = 15
    double_width_y = 15

    # Pixel by pixel assignment of the correct colors
    for x_coord in range(0, 514):

        # Reset offset_y and its iterator for every new column
        offset_y = 0
        offset_iterator_y = 7

        for y_coord in range(0, 514):

            # Copy pixels over. The offset makes up for the smaller size of
            # the AoC terrain texture.
            hd_pixels[x_coord, y_coord] = aoc_pixels[x_coord - offset_x, y_coord - offset_y]

            # Increase the offset when a new column that is supposed
            # to be doubled is reached. This causes the pixel from this step
            # to be read again in the next, thus doubling it.
            if offset_iterator_y == double_width_y:
                offset_y += 1
                offset_iterator_y = 0

                # Switch between a width of 15 and 16 between
                # the columns that are doubled, except when offset_y
                # is 22.
                if double_width_y == 16 and offset_y != 22:
                    double_width_y -= 1
                elif double_width_y == 15:
                    double_width_y += 1

            # Increase iterator value after every pixel
            offset_iterator_y += 1

        # Increase the offset when a new row that is supposed
        # to be doubled is reached. This causes the pixel from this step
        # to be read again in the next, thus doubling it.
        if offset_iterator_x == double_width_x:
            offset_x += 1
            offset_iterator_x = 0

            # Switch between a width of 15 and 16 between
            # the rows that are doubled, except when offset_y
            # is 22.
            if double_width_x == 16 and offset_x != 22:
                double_width_x -= 1
            elif double_width_x == 15:
                double_width_x += 1

        offset_iterator_x += 1

    # The final image is to large, therefore we have to
    # remove one pixel row at the top, one at the bottom
    # and one pixel column on the left plus one on the right
    hd_texture = hd_texture.crop((1, 1, 513, 513))

    return hd_texture

def check_file(img):
    """
    Check if texture has the correct resolution (481x481).
    """

    res_x, res_y = img.size

    if res_x != 481 or res_y != 481:
        print("Error: Image does not have AoC texture size (481x481)")
        sys.exit()

    return 0

def to_file(img, inputfile):
    """
    Writes the transformed result to file.
    """

    try:
        img.save("output_" + inputfile, "PNG")
    except IOError:
        print("File could not be written")

    return 0

if __name__ == "__main__":
    main()
