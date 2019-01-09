# Copyright 2017-2019 the openage authors. See copying.md for legal info.
#
# Usage:
#  blender --background <filename> --python create_sprites.py -- \
#          -a <number-of-angles> \
#          -f <number-of-frames> \
#          -t <track-names> \
#          -m <mesh-names> \
#          --armature <armature-name> \
#          --resolution WIDTHxHEIGHT \
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

    angle_count = args.angles
    legacy_mode = args.legacy
    animation_frame_count = args.frames
    armature = args.armature
    if args.models is None:
        model_names = list()
    else:
        model_names = str(args.models).split(",")

    models = get_models(model_names)

    model_collection = bpy.data.collections.new("render_models")
    bpy.context.scene.collection.children.link(model_collection)

    for model in models:
        model_collection.objects.link(model)

    if args.tracks is None:
        track_names = list()
    else:
        track_names = str(args.tracks).split(",")

    raw_resolution = args.resolution.split("x")

    try:
        res_x = int(raw_resolution[0])
        res_y = int(raw_resolution[1])
    except ValueError:
        exit_blender("%s is not an accepted resolution." % (args.resolution))

    resolution = (res_x, res_y)

    selected_nla_tracks, all_nla_tracks = get_nla_tracks(track_names, armature)

    pivot_point = find_centroid(model_collection)
    print(pivot_point)

    pivot = create_camera(pivot_point)

    scene_config(resolution)

    position_camera(model_collection, pivot, all_nla_tracks, angle_count)

    render_animations(pivot, selected_nla_tracks, angle_count, animation_frame_count, legacy_mode)

    print("Finished in %.4f seconds" % (time.time() - time_start))


def scene_config(resolution):
    """
    Sets up the basic parameters for rendering.8
    """

    scene = bpy.context.scene

    scene.render.image_settings.file_format = 'PNG'
    scene.render.alpha_mode = 'TRANSPARENT'
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]


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
    parser.add_argument("-a", "--angles", default=8, type=int,
                        help="number of angles per frame; default = 8")
    parser.add_argument("--legacy", default=False, action='store_true',
                        help=("only creates 5 sprites of the model (180 degrees); "
                              "used in Genie Engine"))
    parser.add_argument("-m", "--models", type=str,
                        help=("only render models with the specified name."
                              "separate with ,"))
    parser.add_argument("-t", "--tracks", type=str,
                        help=("only render animations from the specified tracks."
                              "separate with ,"))
    parser.add_argument("-f", "--frames", default=10, type=int,
                        help=("number of frames per animation; default = 10"))
    parser.add_argument("--armature", default="Armature", type=str,
                        help=("name of the armature; default = \"Armature\""))
    parser.add_argument("--resolution", default="1280x720", type=str,
                        help=("target resolution for one rendered image;"
                              "inputs as WIDTHxHEIGHT ; default = 1280x720"))
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
                model = bpy.data.objects[name]
                models.append(model)
            except KeyError:
                exit_blender("No model with name \"%s\" found" % (name))

    return models


def get_nla_tracks(track_names, armature_name):
    """
    Returns all NLA tracks and all selected NLA tracks.
    """

    try:
        armature = bpy.data.objects[armature_name]
    except KeyError:
        exit_blender("No armature with name \"%s\" found" % (armature_name))

    all_tracks = list()
    selected_tracks = list()

    for track in armature.animation_data.nla_tracks:

        # Mute all tracks for now
        track.mute = True

        # If all tracks are rendered, select only non-stashed ones
        if not track.name.startswith("[Action Stash]"):

            all_tracks.append(track)

            # If track names were given, select all tracks that were specified
            if track.name in track_names:
                selected_tracks.append(track)

    print(selected_tracks, all_tracks)

    # If no track names were given, select all tracks
    if len(track_names) == 0:
        selected_tracks = all_tracks

    print(selected_tracks, all_tracks)

    if len(all_tracks) == 0 or len(selected_tracks) == 0:
        exit_blender("No matching tracks found. Exiting..")

    return selected_tracks, all_tracks


def find_centroid(collection):
    """
    Find the center of all objects in a collection by
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

    # Dimetric perspective rendering
    bpy.ops.object.camera_add(rotation=(radians(60), 0, radians(45)))
    camera = bpy.context.object
    camera.data.type = 'ORTHO'

    camera.parent = pivot

    bpy.context.scene.camera = camera

    # Parent lights from the scene so that they rotate
    # with the camera.
    for obj in bpy.context.scene.objects:
        if obj.type == 'LIGHT':
            obj.parent = pivot

    return pivot


def position_camera(models, pivot, nla_tracks, angle_count):
    """
    Find the optimal position for the camera.

    The script iterates through all animations to find
    a "bounding box" in that all models fit, regardless
    of frame and animation. The camera is positioned
    to center the bounding box at all times.
    """

    # Vertices of the bounding box
    vertices = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 0), (0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 1)]

    # Faces of the bounding box: bottom, top, x_left, x_right, y_left, y_right
    faces = [(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4), (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)]

    # Create bounding box in scene
    bb_mesh = bpy.data.meshes.new("Bounding Box")
    bounding_box = bpy.data.objects.new("Bounding Box", bb_mesh)
    bounding_box.location = (0, 0, 0)
    bpy.context.scene.collection.objects.link(bounding_box)
    bb_mesh.from_pydata(vertices, [], faces)
    bb_mesh.update(calc_edges=True)
    bounding_box.display_type = 'WIRE'

    scene = bpy.context.scene
    camera = scene.camera

    # Use these variables to save the most extreme coordinates
    # found for the animation.
    highest_x = 0.0
    highest_y = 0.0
    highest_z = 0.0

    lowest_x = 0.0
    lowest_y = 0.0
    lowest_z = 0.0

    # Deselect all objects
    for obj in bpy.data.objects:
        obj.select_set(False)

    for track in nla_tracks:

        # Activate the track
        track.mute = False

        start_frame = scene.frame_start
        end_frame = ceil(track.strips[-1].frame_end)

        # Test every frame
        for frame in range(start_frame, end_frame + 1):

            scene.frame_set(frame)
            scene.update()

            for model in models.all_objects:

                # Copy the mesh at the current position of the frame
                # and assign the copy to a new object.
                # By doing this, we can extract the current location
                # of the vertices in the meshes, which is otherwise
                # impossible.
                cur_mesh = model.to_mesh(bpy.context.depsgraph, True)
                cur_mesh.transform(model.matrix_world)
                pos_obj = bpy.data.objects.new("Test", cur_mesh)
                bpy.context.scene.collection.objects.link(pos_obj)

                # Search every vertex to find the most
                # extreme coordinates in the animations
                for vertex in pos_obj.data.vertices:

                    location = vertex.co

                    if location[0] > highest_x:
                        highest_x = location[0]
                    if location[1] > highest_y:
                        highest_y = location[1]
                    if location[2] > highest_z:
                        highest_z = location[2]

                    if location[0] < lowest_x:
                        lowest_x = location[0]
                    if location[1] < lowest_y:
                        lowest_y = location[1]
                    if location[2] < lowest_z:
                        lowest_z = location[2]

                # Delete the copied mesh
                pos_obj.select_set(True)
                bpy.ops.object.delete()

        # Go back through the animation frame by frame. If we
        # don't do this, it can create problems with keyframe data.
        frame = end_frame

        while frame > start_frame - 1:

            scene.frame_set(frame)

            frame -= 1

        # Mute the track
        track.mute = True

    # Create the bounding box from the values we found
    bb_vertices = bounding_box.data.vertices

    bb_vertices[0].co = lowest_x, lowest_y, lowest_z
    bb_vertices[1].co = lowest_x, highest_y, lowest_z
    bb_vertices[2].co = highest_x, lowest_y, lowest_z
    bb_vertices[3].co = highest_x, highest_y, lowest_z
    bb_vertices[4].co = lowest_x, lowest_y, highest_z
    bb_vertices[5].co = lowest_x, highest_y, highest_z
    bb_vertices[6].co = highest_x, lowest_y, highest_z
    bb_vertices[7].co = highest_x, highest_y, highest_z

    print(bb_vertices[0].co)

    # Sellect bounding box, so we can adjus the camera to it
    bounding_box.select_set(True)

    best_angle = 0
    best_scale = 0.0

    angle = 0
    angle_distance = 360 / angle_count
    index = 0

    # Test every angle for the best camera position
    while angle < (360 - angle_distance):

        angle = angle_distance * index
        pivot.rotation_euler = (0, 0, radians(angle))

        # Fits the view of the camera to all selected objects
        bpy.ops.view3d.camera_to_view_selected()

        # Since the angle is fixed, the camera scale should give indication of the
        # farthest position away from the objects.
        scale = camera.data.ortho_scale

        if scale > best_scale:

            best_angle = angle
            best_scale = scale

        index += 1

    # Go to the angle where the best camera position
    # was found. Then adjust the camera to it.
    pivot.rotation_euler = (0, 0, radians(best_angle))
    bpy.ops.view3d.camera_to_view_selected()

    # Return to the starting position
    pivot.rotation_euler = (0, 0, 0)


def render_frame(frame_num, pivot, track_name, angle_count, legacy):
    """
    Render one frame from all sides.
    """

    filename = bpy.path.basename(bpy.data.filepath).split('.')[0]

    path = "//%s/%s/%s_" % (filename, track_name, str(frame_num))

    scene = bpy.context.scene
    scene.frame_set(frame_num)

    angle = 0
    angle_distance = 360 / angle_count
    index = 0

    # In legacy mode, only render half of the sprites
    max_rotation = 360
    if legacy:
        max_rotation = 180 + angle_distance

    while angle < (max_rotation - angle_distance):

        angle = angle_distance * index
        pivot.rotation_euler = (0, 0, radians(angle))

        scene.render.filepath = "%s%s" % (path, str(angle))
        bpy.ops.render.render(write_still=True)

        index += 1


def render_animations(pivot, tracks, angle_count, animation_frame_count, legacy):
    """
    Renders the animations given NLA tracks.
    """

    animation_frames = animation_frame_count

    scene = bpy.context.scene

    for track in tracks:

        track.mute = False

        start_frame = scene.frame_start
        end_frame = ceil(track.strips[-1].frame_end)

        frame_distance = (end_frame - start_frame) / (animation_frames - 1)

        for index in range(animation_frames):

            rendered_frame = start_frame + int(index * frame_distance)

            # print(rendered_frame)

            render_frame(rendered_frame, pivot, track.name, angle_count, legacy)

        frame = rendered_frame

        # Reset scene
        while frame > start_frame - 1:

            scene.frame_set(frame)

            frame -= 1

        track.mute = True


def exit_blender(message):
    """
    Prints a message in the terminal and quits blender.
    """

    print("\n%s" % (message))
    sys.exit(1)


if __name__ == "__main__":
    main()
