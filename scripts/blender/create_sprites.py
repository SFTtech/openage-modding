# Copyright 2017-2018 the openage authors. See copying.md for legal info.
#
# Usage:
#  blender --background <filename> --python create_sprites.py -- \
#          -m <mesh-names> \
#          -n <number-of-sprites> \
#          --legacy \
#

"""
Script for creating sprites from a blender model.
"""

from math import radians, ceil
import sys
import argparse
import time
import bpy


def main():
    """
    Entry point for the script.
    """

    time_start = time.time()

    args = parse_args()

    sprite_count = args.n
    legacy_mode = args.legacy
    if args.models is None:
        model_names = list()
    else:
        model_names = str(args.models).split(",")

    models = get_models(model_names)

    model_collection = bpy.data.collections.new("render_models")
    bpy.context.scene.collection.children.link(model_collection)

    for model in models:
        model_collection.objects.link(model)

    nla_tracks = get_nla_tracks()

    pivot_point = find_centroid(model_collection)
    print(pivot_point)

    pivot = create_camera(pivot_point)

    scene_config()

    position_camera(model_collection, pivot, nla_tracks)

    render_animations(pivot, nla_tracks)

    print("Finished in %.4f seconds" % (time.time() - time_start))


def scene_config():
    """
    Sets up the basic parameters for rendering.8
    """

    scene = bpy.context.scene

    scene.render.image_settings.file_format = 'PNG'
    scene.render.alpha_mode = 'TRANSPARENT'
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720


def parse_args():
    """
    Parsing arguments.
    """
    # This part is necessary to pass arguments to the python script.
    # Blender ignores every argument after "--".

    argv = sys.argv

    if "--" not in argv:
        argv = []
    else:
        argv = argv[argv.index("--") + 1:]

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", default=8, type=int,
                        help="number of sprites per model; default = 8")
    parser.add_argument("--legacy", default=False, action='store_true',
                        help=("only creates 5 sprites of the model (180 degrees); "
                              "used in Genie Engine"))
    parser.add_argument("-m", "--models", type=str,
                        help=("only render Models with the specified name."
                              "separate with ,"))
    return parser.parse_args(argv)

def get_models(model_names):
    """
    Gets the meshes we want to render.
    """

    models = list()

    if len(model_names) == 0:
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                models.append(obj)
                print(obj)
    else:
        for name in model_names:
            try:
                model = bpy.data.object[name]
                if model.type == 'MESH':
                    models.append(model)
            except KeyError:
                print("No model with name \"{:s}\" found".format(name))
                bpy.ops.wm.quit_blender()

    return models


def get_nla_tracks():
    """
    Returns all non-stashed NLA tracks.
    """

    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            armature = obj

    tracks = list()

    for track in armature.animation_data.nla_tracks:

        # Mute all tracks for now
        track.mute = True

        # Skip temporary NLA tracks
        if not track.name.startswith("[Action Stash]"):
            tracks.append(track)
            print(track.name)

    return tracks


def find_centroid(collection):
    """
    Find the centre of all objects in a collection by
    calculating the average of the coordinates.
    """

    average_x = 0
    average_y = 0
    average_z = 0

    object_count = len(collection.objects)

    for obj in collection.objects:
        location = obj.location

        average_x += location[0]
        average_y += location[1]
        average_z += location[2]

    average_x = average_x / object_count
    average_y = average_y / object_count
    average_z = average_z / object_count

    centroid = (average_x, average_y, average_z)

    return centroid


def create_camera(pivot_point):
    """
    Creates the camera for rendering and makes
    it the active camera for the scene.

    The camera rotates around a pivot object (empty)
    returned by the function for later use.
    """

    bpy.ops.object.empty_add(location=pivot_point)
    pivot = bpy.context.object

    bpy.ops.object.camera_add(rotation=(radians(60), 0, radians(45)))
    camera = bpy.context.object
    camera.data.type = 'ORTHO'

    camera.parent = pivot

    bpy.context.scene.camera = camera

    for obj in bpy.context.scene.objects:
        if obj.type == 'LIGHT':
            obj.parent = pivot

    return pivot


def position_camera(models, pivot, nla_tracks):
    """
    Find the optimal position for the camera.

    The script iterates through all frames to find the closest
    position where all objects are still fully in view in every
    frame.
    """

    # We don't save the best position directly, since we are
    # also dependent on the pivot object. Therefore, we save
    # the frame and angle where it occured.
    best_track = None
    best_frame = -1
    best_angle = 0
    best_scale = 0.0

    # Select all models to fit the camera to them
    for model in models.all_objects:
        model.select_set(True)

    scene = bpy.context.scene
    camera = scene.camera

    for track in nla_tracks:

        # Activate the track
        track.mute = False

        print(track.name)

        start_frame = scene.frame_start
        end_frame = ceil(track.strips[-1].frame_end)

        # Test every frame
        for frame in range(start_frame, end_frame + 1):

            angle = 0
            angle_distance = 45
            index = 0

            scene.frame_set(frame)

            # Test every angle
            while angle < 315:

                angle = angle_distance * index
                pivot.rotation_euler = (0, 0, radians(angle))

                # Fits the view of the camera to all selected objects
                bpy.ops.view3d.camera_to_view_selected()

                # Since the angle is fixed, the camera scale should give indication of the
                # farthest position away from the objects.
                scale = camera.data.ortho_scale

                if scale > best_scale:

                    best_track = track
                    best_frame = frame
                    best_angle = angle
                    best_scale = scale
                    print(frame, angle, camera.location, scale)

                index += 1

        # Go back through the animation frame by frame. If we
        # don't do this, it can create problems with keyframe data.
        frame = end_frame

        while frame > start_frame - 1:

            scene.frame_set(frame)

            frame -= 1

        # Mute the track
        track.mute = True

    # Go to the frame and track where the best camera position
    # was found. Then adjust the camera again.
    best_track.mute = False

    frame = scene.frame_start

    while frame < best_frame:

        scene.frame_set(frame)

        frame += 1

    pivot.rotation_euler = (0, 0, radians(best_angle))
    bpy.ops.view3d.camera_to_view_selected()
    print(camera.location)

    # Return to the starting frame and rotate camera
    # back to default position.
    while frame > start_frame - 1:

        scene.frame_set(frame)

        frame -= 1

    pivot.rotation_euler = (0, 0, 0)
    print(camera.location)
    best_track.mute = True


def render_frame(frame_num, pivot, track_name):
    """
    Render one frame from all sides.
    """

    filename = bpy.path.basename(bpy.data.filepath).split('.')[0]

    path = "//%s/%s/%s_" % (filename, track_name, str(frame_num))

    scene = bpy.context.scene
    scene.frame_set(frame_num)

    angle = 0
    angle_distance = 45
    index = 0

    while angle < 315:

        angle = angle_distance * index
        pivot.rotation_euler = (0, 0, radians(angle))

        scene.render.filepath = "%s%s" % (path, str(angle))
        bpy.ops.render.render(write_still=True)

        index += 1


def render_animations(pivot, tracks):
    """
    Renders the animations given NLA tracks.
    """

    animation_frames = 10

    scene = bpy.context.scene

    for track in tracks:

        track.mute = False

        start_frame = scene.frame_start
        end_frame = ceil(track.strips[-1].frame_end)

        frame_distance = (end_frame - start_frame) / (animation_frames - 1)

        for index in range(animation_frames):

            rendered_frame = start_frame + int(index * frame_distance)

            # print(rendered_frame)

            render_frame(rendered_frame, pivot, track.name)

        frame = rendered_frame

        # Reset scene
        while frame > start_frame - 1:

            scene.frame_set(frame)

            frame -= 1

        track.mute = True

if __name__ == "__main__":
    main()
