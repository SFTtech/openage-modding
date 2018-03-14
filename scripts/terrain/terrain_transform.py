#!/usr/bin/env python3

# Copyright 2018-2018 the openage authors. See copying.md for legal info.

#
# Pillow is required for image manipulation. Install with pip:
#
#     $ pip install pillow
#
# This script transforms an image from cartesian to dimetric projection. An
# inverse operation is supported. Files for the Genie Engine can be created
# by using a legacy mode that outputs BMP files.

import argparse
from PIL import Image

parser = argparse.ArgumentParser(description='Transforms an image from cartesian to dimetric projection.')
parser.add_argument('inputfile')
parser.add_argument('-i', '--inverse', default=False, action='store_true', help='Transforms from dimetric to cartesian')
parser.add_argument('-l', '--legacy-mode', default=False, action='store_true', dest='legacy_mode', help='Uses BMP instead of PNG as output format and the color PINK (255,0,255) for background instead of the ALPHA channel')
args = parser.parse_args()

inputfile = args.inputfile
inverse = args.inverse
legacy_mode = args.legacy_mode

org_img = Image.open(inputfile)

def main():

    if (inverse):
        inverse_transform(org_img)
    else:
        transform(org_img)

    return 0

# Flat to dimetric transformation
def transform(org_img):

    res_x, res_y = org_img.size

    # The transformed image is 2 times the size of the original
    if (legacy_mode):
        # We need the background to be pink in legacy mode
        tr_img = Image.new( 'RGB', (2 * res_x, res_y), (255,0,255))
    else:
        tr_img = Image.new( 'RGBA', (2 * res_x, res_y), (0,0,0,0))

    # Get the pixels
    org_pixels = org_img.load()
    tr_pixels = tr_img.load()

    # Transform the image
    for x in range(0, res_x):
        for y in range(0, res_y):

            # Every pixel is transformed with simple matrix
            # multiplication. The projection matrix is
            #
            # | 1   -1   |
            # | 0.5  0.5 |
            #
            # The x result has to be offset by the x value of
            # the original image.
            c1 = (1 * x + res_x) - 1 * y
            c2 = 0.5 * x + 0.5 * y

            tr_pixels[c1,c2] = org_pixels[x,y]

    to_file(tr_img)

    return 0

# Dimetric to flat transformation
def inverse_transform(org_img):

    res_x, res_y = org_img.size

    tr_res_x = (int)((1/2) * res_x)

    if (legacy_mode):
        tr_img = Image.new( 'RGB', (tr_res_x, res_y), (255,0,255))
    else:
        tr_img = Image.new( 'RGBA', (tr_res_x, res_y), (0,0,0,0))

    # Get the pixels
    org_pixels = org_img.load()
    tr_pixels = tr_img.load()

    # Transform the image
    for x in range(0, tr_res_x):
        for y in range(0, res_y):

            # This uses the exact calculation as in transform()
            c1 = (1 * x + tr_res_x) - 1 * y
            c2 = 0.5 * x + 0.5 * y

            # We just need to swap (c1,c2) and (x,y) from the other
            # function to revert the projection
            tr_pixels[x,y] = org_pixels[c1,c2]

    to_file(tr_img)

    return 0

# Writes the transformed result to file
def to_file(img):

    # Use this for debugging:
    # img.show()

    output_name = inputfile.split(".")[0] + "_t"

    try:
       if (legacy_mode):
           img.save(output_name + ".bmp", "BMP")
       else:
           img.save(output_name + ".png", "PNG")
    except:
       print("File could not be written")

    return 0

if __name__ == "__main__":
    main()
