import bpy
from mathutils import *
from math import *
import math
import os
import shutil

################# Place Puzzle File in 'Unpuzzler' folder on Desktop ############
################# ADD FILENAME HERE #############################################

# Get file and path from environment variables.
filename = os.getenv("unpuzzle_file_name")
UNPUZZLER_DIR = os.getenv('unpuzzle_path')
HTML_OUT_DIR = UNPUZZLER_DIR + "html"

VERT_COUNT_EPSILON = int(os.getenv('vertex_tolerance'))
RADIUS_FUDGE_FACTOR = float(os.getenv('radius_factor'))

#filename = "/full/path/to/myscript.py"
"""
exec(compile(open('/Users/fahminaahmed/Documents/unpuzzler/unpuzzler.py').read(), 'lol', 'exec'))
"""
################ PRESS 'Run Script' ############################################
################ Script takes ~5 min to run ####################################

LAYER_ONE = (True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False)
LAYER_TWO = (False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False)

# Sets the 3d viewport to align with the active camera- necessary because the
# OpenGL render uses the viewport directly. Don't really understand why this
# weird hacky blender UI context crap is necessary, but I don't really care.
def set_3d_view_to_camera():
    for area in bpy.context.screen.areas:
       if area.type == 'VIEW_3D':
           area.spaces[0].region_3d.view_perspective = 'CAMERA'

def make_grid():
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=30, y_subdivisions=30, location=(0,0,0), radius=20)
    bpy.context.active_object.draw_type = 'WIRE'
    bpy.context.active_object.show_all_edges = True

# Returns an approximate radius of the given mesh (for now the size of the
# longest diagonal of the AABB, ideally would be bounding sphere radius)
def get_mesh_radius(mesh):
    max_len = 0
    for i in mesh.bound_box:
        l = Vector((i[0], i[1], i[2])).length
        if l > max_len:
            max_len = l
    print(mesh.name + " radius is " + str(max_len))
    return max_len

def move_mesh_to_bbox_center(mesh):
    mat = mesh.matrix_world
    ctr = Vector()
    for i in mesh.bound_box:
        ctr += mat * Vector((i[0], i[1], i[2]))
    ctr /= 8
    mesh.location -= ctr

# Render the mesh 
# Move all objects to a new layer.
# Make that layer invisible.
# For each object:
# Move the object to the renderable layer.
# Move the object to the origin.
# Move the camera out to the right distance for the object
# Render.
# Move object back to original layer and position.
def render_mesh(mesh, r, max_r, image_dir, part_idx):
    # Move mesh to visible layer and origin.
    bpy.ops.object.select_all(action='DESELECT')
    mesh.select = True
    bpy.context.scene.layers = LAYER_TWO
    bpy.ops.object.move_to_layer(layers=LAYER_ONE)
    bpy.context.scene.layers = LAYER_ONE
    old_loc = mesh.location
    mesh.location = [0, 0, 0]

    img_paths = []

    # First image: shows scale
    bpy.context.scene.camera.location = [RADIUS_FUDGE_FACTOR * max_r, RADIUS_FUDGE_FACTOR * max_r, RADIUS_FUDGE_FACTOR * max_r]
    set_3d_view_to_camera()
    img_path = image_dir + "/part_" + str(part_idx) + "_0.png"
    bpy.context.scene.render.filepath = img_path
    bpy.ops.render.opengl( write_still=True )
    img_paths.append(img_path)

    # Second image: detail persp view
    bpy.context.scene.camera.location = [RADIUS_FUDGE_FACTOR * r, RADIUS_FUDGE_FACTOR * r, RADIUS_FUDGE_FACTOR * r]
    set_3d_view_to_camera()
    img_path = image_dir + "/part_" + str(part_idx) + "_1.png"
    bpy.context.scene.render.filepath = img_path
    bpy.ops.render.opengl( write_still=True )
    img_paths.append(img_path)

    # Third image: 
    mesh.rotation_euler.z += pi/2
    img_path = image_dir + "/part_" + str(part_idx) + "_2.png"
    bpy.context.scene.render.filepath = img_path
    bpy.ops.render.opengl( write_still=True )
    img_paths.append(img_path)

    # Third image: 
    mesh.rotation_euler.z += pi/2
    img_path = image_dir + "/part_" + str(part_idx) + "_3.png"
    bpy.context.scene.render.filepath = img_path
    bpy.ops.render.opengl( write_still=True )
    img_paths.append(img_path)

    # Move mesh back. Layer state crap makes deselecting messy...
    mesh.location = old_loc
    bpy.ops.object.move_to_layer(layers=LAYER_TWO)
    bpy.context.scene.layers = LAYER_TWO
    mesh.select = False
    bpy.context.scene.layers = LAYER_ONE
    return img_paths



# Renders and counts all meshes.
# Returns a list of [image_filename, instance_count] pairs.
def render_all_meshes(meshes, deduped_indices, image_dir):     
    # Move all objects to a new invisible layer.
    for mesh in meshes:
        mesh.select = True
    bpy.ops.object.move_to_layer(layers=LAYER_TWO)
    bpy.ops.object.select_all(action='DESELECT')
    
    # Set up the camera.
    # TODO: ortho/iso...
    # bpy.ops.object.camera_add(location = [5, 5, 5], rotation = [0, pi / 3.5, pi/4])
    bpy.ops.object.camera_add(location = [5, 5, 5], rotation = [pi / 3.5, 0 , 3 * pi / 4])
    bpy.context.scene.camera = bpy.context.active_object
    bpy.context.scene.render.resolution_x = 512
    bpy.context.scene.render.resolution_y = 512

    # Make the clip plane obscene because some objects are huge.
    for c in bpy.data.cameras:
        c.clip_end = 20000


    images_and_counts = []

    max_r = 0
        
    for i in range(len(deduped_indices)):
        unique_index_set = deduped_indices[i]
        mesh = meshes[unique_index_set[0]]
        rr = get_mesh_radius(mesh)
        if rr > max_r:
            max_r = rr

    for i in range(len(deduped_indices)):
        unique_index_set = deduped_indices[i]
        count = len(unique_index_set)
        mesh = meshes[unique_index_set[0]]
        r = get_mesh_radius(mesh)
        image_paths = render_mesh(mesh, r, max_r, image_dir, i)
        images_and_counts.append([image_paths, count])
    return images_and_counts;

def entry_div_string(filenames, count):
    html = '<div class="entry">'
    for img_src in filenames:
        relative_src = os.path.basename(os.path.dirname(img_src)) + "/" + os.path.basename(img_src)
        html += '<img class="im" src="' + relative_src + '"></img>'
    html += '<div class="ct">' + str(count) + '</div></div>'
    return html

# Takes a list of [image_filename, instance_count] pairs and exports an html
# filename should be relative to html folder, eg images/part1.png
def get_html(title, filenames_and_counts):
    html = ('<!DOCTYPE html><html><head><title>' + title + '</title><style type="text/css">'
    '.im { width: 256px; height:256px; position: relative; left: 5px; top:5px;}'
    '.im:first-of-type { margin-right: 10px; }'
    '.entry { height: 265px; width: 100%; position: relative; border-bottom: 1px dotted #ccc; }'
    '.ct { font-size: 12em; position: absolute; right: 0px; top: 10px;}'
    'body {font-family: helvetica,arial,sans-serif;}'
    '</style></head><body>'
    '<div style="font-size: 40px;"><span style="position:relative; left:5px; margin-right:75px;">Scale View</span><span>Rotation Views</span></div>')
    for fc in filenames_and_counts:
        html += entry_div_string(fc[0], fc[1])
    html += '</body></html>'
    return html

# This here is kinda the main thing.
def write_output(meshes, deduped_indices):
    title = filename.split('.')[0]
    html_dir = HTML_OUT_DIR + "/" + title
    html_image_dir = html_dir + "/images"
    html_file_path = html_dir + "/" + title + ".html"
    if not os.path.exists(HTML_OUT_DIR):
        os.mkdir(HTML_OUT_DIR)
    # Delete the old contents of the html directory.
    for fn in os.listdir(HTML_OUT_DIR):
        delfile = os.path.join(HTML_OUT_DIR, fn)
        if os.path.isfile(delfile):
            os.unlink(delfile)
        elif os.path.isdir(delfile):
            shutil.rmtree(delfile)

    if not os.path.exists(html_dir):
        os.mkdir(html_dir)
    if not os.path.exists(html_image_dir):
        os.mkdir(html_image_dir)

    # Do the rendering.
    filenames_and_counts = render_all_meshes(meshes, deduped_indices, html_image_dir)

    # Write the actual html.    
    html = get_html(title, filenames_and_counts)
    f = open(html_file_path, 'w')
    f.write(html)
    f.close()


# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=True)

# Find the file to unpuzzle and import
bpy.ops.import_mesh.stl(filepath=UNPUZZLER_DIR+filename)

# Take the full STL and break it apart into seperable components
# DOES NOT consider interconnected parts - will break apart chains
bpy.ops.object.mode_set(mode='EDIT') 
bpy.ops.mesh.separate(type='LOOSE')
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT')

# For all the new shells created....
num_shells = len(bpy.data.objects)
for each in range(num_shells):
    bpy.ops.object.select_all(action='DESELECT')

    # Select one shell
    bpy.data.objects[each].select = True
    bpy.context.scene.objects.active = bpy.data.objects[each]

    # Move the shell origin to the center of mass for that shell
    # This is NECESSARY to get the correct rotation
    bpy.ops.object.origin_set(type="GEOMETRY_ORIGIN",center="MEDIAN")

    # Duplicate the shell 
    bpy.ops.object.duplicate()
    bpy.ops.object.select_all(action='DESELECT')

    # Select the duplicate shell - duplicates always go to the end of the shell list
    # NECESSARY because the convex hull operator replaces the part it operates on
    bpy.data.objects[num_shells].select = True
    bpy.context.scene.objects.active = bpy.data.objects[num_shells]

    # Replace the duplicate shell with the shell's convex hull
    # The convex hull is the minimum subset of points that describes the shell outer boundary
    # It's like stretching an elastic bag around the part
    # For reference: http://en.wikipedia.org/wiki/Convex_hull
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.convex_hull()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Simplify the mesh - NECESSARY to find largest flat face
    bpy.ops.object.modifier_add(type='DECIMATE')
    bpy.data.objects[num_shells].modifiers["Decimate"].decimate_type='DISSOLVE'
    bpy.data.objects[num_shells].modifiers["Decimate"].angle_limit=.35
    bpy.ops.object.modifier_apply(modifier="Decimate")

    # Walk through all the faces...
    # ...of the simplified mesh...
    # ...of the convex hull ...
    # ...of the duplicate part ...
    # ...and add them the useful arrays
    areas = []
    normals = []
    for face in bpy.data.objects[num_shells].data.polygons:
        areas.append(face.area)
        normals.append(face.normal)

    # Select the index of the face with the largest area
    max_area_index = areas.index(max(areas))

    # Select the normal of that face
    max_normal = normals[max_area_index]

    # Delete this object
    # **All we wanted was the normal of the largest convex hull face
    # This normal defines the current orientation of the part
    bpy.ops.object.delete()

    # Select the original obeject
    this_mesh = bpy.data.objects[each]
    this_mesh.select = True

    # We now want to orient this part such that the largest convex hull face is down
    # This corresponds to the most likely orientation of the part when set on a table
    # The thought here is that it will make the parts easier to identify
    # Any orientation is possible

    # Define desired orientation
    align_vect = Vector([0,0,-1])

    # Determine the rotation vector
    # This is the vector around which the part must be rotated to go from its current orientation to the desired orientation
    # The rotation vector is orthogonal to both the current and desired orientation vectors
    part_rot_ax = align_vect.cross(max_normal)

    # Deterimine the rotation angle
    # This is the current angle between the desired and current orientation
    part_rot_ang = math.acos(align_vect.dot(max_normal))

    # Rotate the part around the rotation vector by the rotation angle
    bpy.ops.transform.rotate(value=-part_rot_ang, axis=part_rot_ax)

# At the point, all shells are oriented correctly but in are still in a jumble
# Now to split them out into a nice, even grid
# The grid will organize the largest part into the lower left corner 
# Parts will organize to the right from there

# Cycle through all objects to determine size and sort
bbx_volume = []
bbx_max = 0
for each in range(num_shells):

    # Select on shell
    this_mesh = bpy.data.objects[each]

    # Grab all vertices in this shell
    vert_list = [vertex.co for vertex in this_mesh.data.vertices]  

    # Drop vertices into convenient seperate vectors
    these_x = [row[0] for row in vert_list]
    these_y = [row[1] for row in vert_list]
    these_z = [row[2] for row in vert_list]

    # Determine crappy bounding box by grabbing largest vertices in each primary direction
    # Calculate crappy volume
    vol = (max(these_x)-min(these_x))*(max(these_y)-min(these_y))*(max(these_z)-min(these_z))
    bbx_volume.append(vol)

    # Variable to hold largest dimension of all in shells
    bbx_max = max(bbx_max,
        (max(these_x)-min(these_x)),
        (max(these_y)-min(these_y)),
        (max(these_z)-min(these_z)))


# Sort by volume - largest to smallest - return indexes
largest_part = sorted(range(num_shells), key=lambda k: bbx_volume[k], reverse=True)
print("largest_part:")
print(largest_part)

# Collapse and count duplicates.
# Store a list of lists of identical meshes:
shell_dups = []

#cur_val = bbx_volume[largest_part[0]]
cur_val = len(bpy.data.objects[largest_part[0]].data.vertices)
cur_set = []
ct = 0
for shell_idx in largest_part:
    #new_val = bbx_volume[shell_idx]
    new_val = len(bpy.data.objects[shell_idx].data.vertices)
    if abs(new_val - cur_val) <= VERT_COUNT_EPSILON:
        cur_set.append(shell_idx)
    else:
        shell_dups.append(cur_set)
        cur_set = [shell_idx]
        cur_val = new_val
# Add the last set :P
shell_dups.append(cur_set)


# Debug printing...
for s in shell_dups:
    print("size: " + str(len(s)))
    print("vert counts:")
    print([len(bpy.data.objects[ss].data.vertices) for ss in s])
    

all_shells = [m for m in bpy.data.objects]
write_output(all_shells, shell_dups)

dy = 0
for unique in shell_dups:
    dx = 0
    for dup_idx in unique:
        all_shells[dup_idx].location = [dx, dy, 0]
        dx += bbx_max
    dy += bbx_max


exit()
"""
# Set up loop to organize shells
fill_x = 0
fill_y = 0
count = 0

# Define size of grid -  grid will be a square with this dimension on each side
shift_row = sqrt(num_shells)

# Loop through each of the sorted part array
for each in largest_part:

    # Select this shell
    this_mesh = bpy.data.objects[each]
    print(str(this_mesh) + str(len(this_mesh.data.vertices)))

    # Calculate where this part should sit in the grid
    d_x = (fill_x+.5)*bbx_max
    d_y = (fill_y+.5)*bbx_max

    # Move the part to this x,y location
    # Center the part on the z plane
    this_mesh.location = [d_x,d_y,0]

    # Increment the grid counter
    if count < shift_row:
        fill_x += 1
        count += 1
    else:
        fill_y += 1
        fill_x = 0
        count = 0
"""

# Export the new, organized grid to a new file
# bpy.ops.object.select_all(action='SELECT')
# new_file = filename[0:(len(filename)-4)]+"_unpuzzled.stl"
# bpy.ops.export_mesh.stl(filepath=path+new_file)
# TODO(mprice): Uncomment again.
# os.remove(path+filename)