#!/usr/bin/python3
#
# Copyright 2019-2019 the openage authors. See copying.md for legal info.
"""
Create a spritesheet from multiple frames and angles.
"""

import argparse
import os
import sys
from PIL import Image

VERSION_NO = 0

def main():
    """
    Main entry point function.
    """

    args = parse()
    if args.folders is None:
        sys.exit("No animations specfied")
    else:
        animations = args.folders.split(",")

    if args.alpha_threshold is None:
        print("Transparency threshold: 0")
        transparency_threshold = 0
    else:
        print("Transparency threshold: %i" % args.alpha_threshold)
        transparency_threshold = args.alpha_threshold

    for anim in animations:

        # List of individual sprites
        im_list = list()
        
        # Sprite meta information (angle, frame number, hotspot)
        im_meta_list = list()

        directory = os.fsencode(anim)
        for file in sorted(os.listdir(directory)):
            filename = os.fsdecode(file)

            if filename.endswith(".png"):
                current_im = Image.open("%s/%s" % (anim, filename))

                if transparency_threshold > 0:
                    current_im = correct_alpha(current_im, transparency_threshold)

                cut_out_im, offset_hotspot = cut_out(current_im, find_hotspot(current_im))
                im_list.append(cut_out_im)
                file_info = parse_filename(filename)
                meta_info = [file_info[0], file_info[1], offset_hotspot[0], offset_hotspot[1]]
                im_meta_list.append(meta_info)

        spritesheet, frame_infos = merge_sprites(im_list, im_meta_list)
        spritesheet_filename = "%s_animation.png" % anim
        spritesheet.save(spritesheet_filename)

        # Sprite meta information and location inside the spritesheet
        sprite_meta_list = list()

        for index in range(len(im_meta_list)):
            sprite_meta_list.append([im_meta_list[index][0],
                                     im_meta_list[index][1],
                                     frame_infos[index][0],
                                     frame_infos[index][1],
                                     frame_infos[index][2],
                                     frame_infos[index][3],
                                     frame_infos[index][4],
                                     frame_infos[index][5]])

        sprite_meta_list = sorted(sprite_meta_list)

        print_sprite_definition(spritesheet_filename, sprite_meta_list)


def parse():
    """
    Parse user parameters.
    """

    parser = argparse.ArgumentParser(description="Crop images to proper size.")
    parser.add_argument("--folders", type=str, help="Folders with frames.")
    parser.add_argument("-a", "--alpha-threshold", type=int, help="Threshold for alpha channel.")
    args = parser.parse_args()

    return args


def parse_filename(filename):
    """
    Read frame number and angle from filename.
    """

    frame_angle = int(filename[8:11])
    frame_num = int(filename[0:3])

    return (frame_angle, frame_num)


def merge_sprites(im_list, im_meta_list):
    """
    Order single sprites into grid.
    """

    current_x = 0
    current_y = 0

    # The width of the widest sprite in the current column
    highest_width = 0

    # Dimensions of the resulting spritesheet
    result_height = 0
    result_width = 0

    # Saves the offsets of sprite as 2-tuples
    offset_coord_list = list()

    # Saves the offests, dimensions and hotspots of sprite as 6-tuples
    frame_info_list = list()

    index = 0
    for image in im_list:
        if im_meta_list[index][0] == 0:
            current_x += highest_width
            result_width += highest_width
            current_y = 0
            highest_width = 0

        width, height = image.size

        if width > highest_width:
            highest_width = width

        offset_coord_list.append((current_x, current_y))
        new_hotspot_x = current_x + im_meta_list[index][2]
        new_hotspot_y = current_y + im_meta_list[index][3]
        frame_info_list.append((current_x,
                                current_y,
                                width,
                                height,
                                new_hotspot_x,
                                new_hotspot_y))

        current_y += height

        if current_y > result_height:
            result_height = current_y

        index += 1

    result_width += highest_width

    result = Image.new('RGBA', (result_width, result_height))

    index = 0
    for image in im_list:

        result.paste(image, offset_coord_list[index])

        index += 1

    return (result, frame_info_list)


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

    bounding_box = list(image.getbbox())

    if hotspot[0] < bounding_box[0]:
        bounding_box[0] = hotspot[0]
    if hotspot[1] < bounding_box[1]:
        bounding_box[1] = hotspot[1]
    if hotspot[0] > bounding_box[2]:
        bounding_box[2] = hotspot[0]
    if hotspot[1] > bounding_box[3]:
        bounding_box[3] = hotspot[1]

    crop_im = image.crop(bounding_box)
    offset_hotspot = (hotspot[0] - bounding_box[0], hotspot[1] - bounding_box[1])

    return (crop_im, offset_hotspot)


def correct_alpha(image, threshold):
    """
    Set pixels transparency values smaller then the threshold
    to completely transparent (alpha = 0).
    """

    im_pixels = image.load()

    res_x, res_y = image.size

    for x_coord in range(res_x):
        for y_coord in range(res_y):
            cur_pixel = im_pixels[x_coord, y_coord]
            cur_alpha_value = cur_pixel[3]

            if cur_alpha_value < threshold:
                im_pixels[x_coord, y_coord] = (cur_pixel[0], cur_pixel[1], cur_pixel[2], 0)

    return image


def print_sprite_definition(spritesheet_filename, meta_info):
    """
    Prints the .sprite definition file.
    """

    file_content = ""

    # Header definition
    file_content += "# This file was automatically generated\n"
    file_content += "version %s\n\n" % VERSION_NO

    # Image file reference
    file_content += "# Image file reference\n"
    # TODO: Store image definition for multiple images somewhere
    file_content += "imagefile 0 %s\n" % spritesheet_filename
    file_content += "\n"

    # Layer definition
    file_content += "# Layer definitions\n"
    # TODO: Store layer definition for multiple layers somewhere
    file_content += "layer 0 mode=off position=default\n"
    file_content += "\n"

    # Angle definitions
    file_content += "# Angle definitions\n"

    current_angle = -1

    for index in range(len(meta_info)):

        frame_angle = meta_info[index][0]

        if current_angle != frame_angle:
            file_content += "angle %s\n" % frame_angle
            current_angle = frame_angle

        file_content += "frame 0 0 %i %i %i %i %i %i\n" % (meta_info[index][2],
                                                           meta_info[index][3],
                                                           meta_info[index][4],
                                                           meta_info[index][5],
                                                           meta_info[index][6],
                                                           meta_info[index][7])

    sprite_definition_filename = spritesheet_filename[:-4] + ".sprite"
    sprite_file = open(sprite_definition_filename, "w")
    sprite_file.write(file_content)


if __name__ == "__main__":
    main()
