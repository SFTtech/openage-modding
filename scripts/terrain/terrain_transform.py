#!/usr/bin/env python3

# Copyright 2018-2018 the openage authors. See copying.md for legal info.

"""
This script transforms an image from cartesian to dimetric projection. An
inverse operation is supported. Files for the Genie Engine can be created
by using a legacy mode that outputs BMP files.

Pillow is required for image manipulation. Install with pip:

    $ pip install pillow
"""

import math
import argparse
from PIL import Image

def main():
    """
    CLI entry point
    """

    args = get_args()

    inputfile = args.inputfile
    inverse = args.inverse
    legacy_mode = args.legacy_mode

    org_img = Image.open(inputfile)

    if inverse:
        tr_img = inverse_transform(org_img, legacy_mode)
    else:
        tr_img = transform(org_img, legacy_mode)

    output_name = inputfile.split(".")[0] + "_t"

    to_file(tr_img, legacy_mode, output_name)

    return 0

def get_args():
    """
    Get CLI arguments.
    """

    parser = argparse.ArgumentParser(description=("Transforms an image from cartesian "
                                                  "to dimetric projection."))
    parser.add_argument('inputfile')
    parser.add_argument('-i', '--inverse', default=False, action='store_true',
                        help='Transforms from dimetric to cartesian')
    parser.add_argument('-l', '--legacy-mode', default=False, action='store_true',
                        dest='legacy_mode',
                        help=("Uses BMP instead of PNG as output format and the "
                              "color PINK (255,0,255) for background instead of the "
                              "ALPHA channel"))
    return parser.parse_args()

def transform(img, legacy_mode):
    """
    Flat to dimetric transformation.
    """

    res_x, res_y = img.size

    # The transformed image is 2 times the size of the original
    if legacy_mode:
        # We need the background to be pink in legacy mode
        tr_img = Image.new('RGB', (2 * res_x, res_y), (255, 0, 255))
    else:
        tr_img = Image.new('RGBA', (2 * res_x, res_y), (0, 0, 0, 0))

    # Get the pixels
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


    return tr_img

def inverse_transform(img, legacy_mode):
    """
    Dimetric to flat transformation.
    """

    res_x, res_y = img.size

    tr_res_x = (int)((1/2) * res_x)

    if legacy_mode:
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

    return tr_img

def to_file(img, legacy_mode, filename):
    """
    Writes the transformed result to file.
    """

    # Use this for debugging:
    # img.show()

    try:
        if legacy_mode:
            img.save(filename + ".bmp", "BMP")
        else:
            img.save(filename + ".png", "PNG")
    except IOError:
        print("File could not be written")

    return 0

if __name__ == "__main__":
    main()
