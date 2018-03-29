#!/usr/bin/env python3

# Copyright 2018-2018 the openage authors. See copying.md for legal info.

"""
This script transforms an image from cartesian to dimetric projection. An
inverse operation is supported. Files for the Genie Engine can be created
by using a legacy mode that outputs BMP files.

Pillow is required for image manipulation. Install with pip:

    $ pip install pillow
"""

import argparse
import math
import sys
from PIL import Image

def main():
    """
    CLI entry point
    """

    args = get_args()

    inputfile = args.inputfile
    inverse = args.inverse
    palette = args.palette_file

    org_img = Image.open(inputfile)

    check_file(org_img, inverse)

    if inverse:
        tr_img = inverse_transform(org_img, palette)
    else:
        tr_img = transform(org_img, palette)

    output_name = inputfile.split(".")[0] + "_t"

    to_file(tr_img, palette, output_name)

    return 0

def get_args():
    """
    Get CLI arguments.
    """

    parser = argparse.ArgumentParser(description=("Transforms an image from cartesian "
                                                  "to dimetric projection."))
    parser.add_argument('inputfile', help='The image you want to transform')
    parser.add_argument('-i', '--inverse', default=False, action='store_true',
                        help='Transforms from dimetric to cartesian')
    parser.add_argument('--legacy-mode', dest='palette_file',
                        help=("Uses BMP instead of PNG as output format and the "
                              "color PINK (255,0,255) for background instead of the "
                              "ALPHA channel. Requires an image with the AoE2 palette."))
    return parser.parse_args()

def check_file(img, inverse):
    """
    Check if image has the correct ratio.
    """

    res_x, res_y = img.size

    if inverse:
        if res_x != 2 * res_y:
            print("Error: Image requires ratio of 2:1")
            sys.exit()
    else:
        if res_x != res_y:
            print("Error: Image requires ratio of 1:1")
            sys.exit()

    return 0

def transform(img, palette):
    """
    Flat to dimetric transformation.
    """

    res_x, res_y = img.size

    # The transformed image is 2 times the size of the original
    if palette:
        # We need the background to be pink in legacy mode
        tr_img = Image.new('RGB', (2 * res_x, res_y), (255, 0, 255))
    else:
        tr_img = Image.new('RGBA', (2 * res_x, res_y), (0, 0, 0, 0))

    # Get the pixels
    img = img.rotate(90)
    org_pixels = img.load()
    tr_pixels = tr_img.load()

    # Transform the image
    for x_coord in range(0, res_x):
        for y_coord in range(0, res_y):

            # Every pixel is transformed with simple matrix
            # multiplication. The projection matrix is
            #
            # | 1   -1   |
            # | 0.5  0.5 |
            #
            # The x result has to be offset by the x value of
            # the original image.
            tr_x = (1 * x_coord + res_x - 1) - 1 * y_coord
            if x_coord+y_coord < res_y:
                tr_y = math.ceil(0.5 * x_coord + 0.5 * y_coord)
            else:
                tr_y = math.floor(0.5 * x_coord + 0.5 * y_coord)

            tr_pixels[tr_x, tr_y] = org_pixels[x_coord, y_coord]

    if palette:
        tr_img = tr_img.quantize(colors=256, palette=Image.open(palette))

    return tr_img

def inverse_transform(img, palette):
    """
    Dimetric to flat transformation.
    """

    res_x, res_y = img.size

    tr_res_x = (int)((1/2) * res_x)

    if palette:
        # We need the background to be pink in legacy mode
        tr_img = Image.new('RGB', (tr_res_x, res_y), (255, 0, 255))
    else:
        tr_img = Image.new('RGBA', (tr_res_x, res_y), (0, 0, 0, 0))

    # Get the pixels
    org_pixels = img.load()
    tr_pixels = tr_img.load()

    # Transform the image
    for x_coord in range(0, tr_res_x):
        for y_coord in range(0, res_y):

            # This uses the exact calculation as in transform()
            tr_x = (1 * x_coord + tr_res_x - 1) - 1 * y_coord
            if x_coord+y_coord < res_y:
                tr_y = math.ceil(0.5 * x_coord + 0.5 * y_coord)
            else:
                tr_y = math.floor(0.5 * x_coord + 0.5 * y_coord)

            # We just need to swap (tr_x,tr_y) and (x,y) from the other
            # function to revert the projection
            tr_pixels[x_coord, y_coord] = org_pixels[tr_x, tr_y]

    tr_img = tr_img.rotate(270)

    if palette:
        tr_img = tr_img.quantize(colors=256, palette=Image.open(palette))

    return tr_img

def to_file(img, palette, filename):
    """
    Writes the transformed result to file.
    """

    # Use this for debugging:
    # img.show()

    try:
        if palette:
            img.save(filename + ".bmp", "BMP")
        else:
            img.save(filename + ".png", "PNG")
    except IOError:
        print("File could not be written")

    return 0

if __name__ == "__main__":
    main()
