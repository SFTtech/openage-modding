# Copyright 2017-2017 the openage authors. See copying.md for legal info.
#
# Usage for this script:
#  blender --background --python create_sprites.py -- \
#          --cameras Camera0,Camera90,Camera180 \
#

import sys, bpy, argparse

# This part is necessary to pass arguments to the python script.
# Blender ignores every argument after "--".
argv = sys.argv

if "--" not in argv:
    argv = []
else:
    argv = argv[argv.index("--") + 1:]

# Parsing arguments
parser = argparse.ArgumentParser()
parser.add_argument("-c", "--cameras",
                    help=("only render cameras with these names; "
                        "separate by using ','"))
args = parser.parse_args(argv)

cameras = []

if args.cameras is not None:
    cameras = args.cameras.split(",")
    print(cameras)

index = 0

for obj in bpy.data.objects:
    
    if obj.type == 'CAMERA' and (not cameras
                                 or obj.name in cameras):
        print("Creating sprite for", obj.name)

        bpy.context.scene.camera = obj

        # Set camera to orthographic
        obj.data.type = 'ORTHO'
        
        # Set file format to PNG if that wasn't default
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        
        # Set background to alpha channel
        bpy.context.scene.render.alpha_mode = 'TRANSPARENT' 
        bpy.context.scene.render.image_settings.color_mode ='RGBA'
        
        # Save image file
        filename = bpy.path.basename(bpy.data.filepath)
        filename = filename.split('.')[0]
        path = '//' + filename + '/' + filename + '_' + str(index)
        bpy.context.scene.render.filepath = path 

        bpy.ops.render.render(write_still=True)

        index += 1
