#!/usr/bin/python3

"""
Create a single sprite from multiple frames and angles.
"""

import argparse
import os
from PIL import Image

def main():
    """
    Main entry point function.
    """
    args = parse()
    if args.folders is not None:
        animations = args.folders.split(",")
    print(animations)
    im_list = list()
    im_meta_list = list()

    for anim in animations:
        directory = os.fsencode(anim)
        for file in os.listdir(directory):
            filename = os.fsdecode(file)
            if filename.endswith(".png"):
                current_im = Image.open("%s/%s" % (anim, filename))
                print(find_hotspot(current_im))
                im_list.append(cut_out(current_im, find_hotspot(current_im)))
                im_meta_list.append(parse_filename(filename))
    merge_sprites(im_list, im_meta_list).save("result.png")

def parse():
    """
    Parse user parameters.
    """
    parser = argparse.ArgumentParser(description="Crop images to proper size.")
    parser.add_argument("--folders", type=str, help="Folders with frames.")
    args = parser.parse_args()
    return args

def parse_filename(filename):
    """
    Read frame and angle from filename.
    """
    frame_num = int(filename[0:2])
    frame_angle = int(filename[8:11])
    return (frame_num, frame_angle)

def merge_sprites(im_list, im_meta_list):
    """
    Order single images into grid.
    """
    result = Image.new('RGBA', (1000, 1000))
    current_x = 0
    current_y = 0
    highest_width = 0
    for image in im_list:
        if im_meta_list[1] == 0:
            current_x += highest_width
            highest_width = 0
            current_y = 0
        width, height = image.size
        if width > highest_width:
            highest_width = width
        result.paste(image, box=(current_x, current_y))
        current_y += height
    return result


def find_hotspot(image):
    """
    Return center point of the image.
    """
    width, height = image.size
    hotspot_x = -1
    hotspot_y = -1
    if width % 2 == 0:
        hotspot_x = width//2 - 1
    else:
        hotspot_x = (width-1)//2
    if height % 2 == 0:
        hotspot_y = height//2 - 1
    else:
        hotspot_y = (height-1)//2
    return (hotspot_x, hotspot_y)

def cut_out(image, hotspot):
    """
    Remove surrounding alpha pixels.
    """
    bounding_box = image.getbbox()
    print(bounding_box)
    if hotspot[0] < bounding_box[0]:
        bounding_box[0] = hotspot[0]
    if hotspot[1] < bounding_box[1]:
        bounding_box[1] = hotspot[1]
    if hotspot[0] > bounding_box[2]:
        bounding_box[2] = hotspot[0]
    if hotspot[1] > bounding_box[3]:
        bounding_box[3] = hotspot[1]

    crop_im = image.crop(bounding_box)
    return crop_im

if __name__ == "__main__":
    main()
