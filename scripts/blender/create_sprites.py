# Copyright 2017-2018 the openage authors. See copying.md for legal info.
#
# Usage:
#  blender --background <filename> --python create_sprites.py -- \
#          -m <mesh-name> \
#          -n <number-of-sprites> \
#          --legacy \
#

"""
Script for creating sprites from a blender model.
"""

from math import radians
import sys
import argparse
import bpy

# This part is necessary to pass arguments to the python script.
# Blender ignores every argument after "--".
argv = sys.argv

if "--" not in argv:
    argv = []
else:
    argv = argv[argv.index("--") + 1:]

# Parsing arguments
parser = argparse.ArgumentParser()
parser.add_argument("-n", default=8, type=int,
                    help="number of sprites per model; default = 8")
parser.add_argument("--legacy", default=False, action='store_true',
                    help=("only creates 5 sprites of the model (180 degrees); "
                          "used in Genie Engine"))
parser.add_argument("-m", "--model", type=str, default="Model",
                    help=("name of the model in blender;"
                          "default = Model"))
args = parser.parse_args(argv)

sprites = args.n
legacy_mode = args.legacy
model_name = args.model

# Get the model we want to render
try:
    model = bpy.data.objects[model_name]
except KeyError:
    print("No model with name \"{:s}\" found".format(model_name))
    bpy.ops.wm.quit_blender()

model_location = model.matrix_world.to_translation()

# Create a pivot point for our model
bpy.ops.object.empty_add(location=model_location)
center = bpy.context.object

# Create the Camera with rotation (60 deg, 0 deg, 45 deg)
bpy.ops.object.camera_add(rotation=(radians(60), 0, radians(45)))
camera = bpy.context.object
camera.data.type = 'ORTHO'

# Move vcamera with pivot point
camera.parent = center

# Set the created camera as active for the scene
bpy.context.scene.camera = camera

# Align the camera to the model
model.select = True
bpy.ops.view3d.camera_to_view_selected()
model.select = False
camera.select = False

# Create start and end of animation
bpy.context.scene.frame_start = 0
bpy.context.scene.frame_end = sprites - 1

# Add keyframes for pivot point
center.rotation_euler = (0, 0, radians(-45))
center.keyframe_insert(data_path="rotation_euler", frame=0)

center.rotation_euler = (0, 0, radians(360-45))
center.keyframe_insert(data_path="rotation_euler", frame=sprites)

# Set interpolation to linear to transition by a constant
# angle between frames
fcurves = center.animation_data.action.fcurves

for fc in fcurves:
    for keyframe in fc.keyframe_points:
        keyframe.interpolation = 'LINEAR'

# Set output format
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.render.alpha_mode = 'TRANSPARENT'
bpy.context.scene.render.image_settings.color_mode = 'RGBA'

filename = bpy.path.basename(bpy.data.filepath)
filename = filename.split('.')[0]

angle = 360 / sprites

frames_to_render = sprites

# Only render 180 degrees in legacy mode
if legacy_mode:
    frames_to_render = (sprites // 2) + 1

for frame in range(0, frames_to_render):

    bpy.context.scene.frame_set(frame)

    # File is put in a folder with the initial name
    # of the processed blender file
    path = '//' + filename + '/' + filename + '_' + str(int(frame * angle))
    bpy.context.scene.render.filepath = path

    # Render the result
    bpy.ops.render.render(write_still=True)
