"""
bx_review.py - Studio Lighting & Camera Rig for Turnaround Review
Sets up 3-point lighting and positions review cameras for high-clarity viewport screenshots.
Compatible with Blender 4.x and 5.x.
"""

import bpy
import math
from mathutils import Vector

def ensure_collection(name):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col

def get_scene_focus_target():
    mesh_objs = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not mesh_objs:
        return Vector((0, 0, 1)), 2.0
    
    # Calculate unified AABB
    all_corners = []
    for obj in mesh_objs:
        all_corners.extend([obj.matrix_world @ Vector(corner) for corner in obj.bound_box])
    
    min_x = min(c.x for c in all_corners)
    max_x = max(c.x for c in all_corners)
    min_y = min(c.y for c in all_corners)
    max_y = max(c.y for c in all_corners)
    min_z = min(c.z for c in all_corners)
    max_z = max(c.z for c in all_corners)
    
    center = Vector(((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2))
    size = max(max_x - min_x, max_y - min_y, max_z - min_z)
    return center, max(size, 1.0)

def setup_studio_lighting(center, size):
    col = ensure_collection("Studio_Review_Lighting")
    
    # Remove older lights in this collection
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
        
    dist = size * 2.5
    
    # 1. Key Light (45 deg right, 45 deg up, warm white)
    key_data = bpy.data.lights.new(name="Review_KeyLight", type='AREA')
    key_data.energy = size * 300.0
    key_data.size = size * 0.8
    key_data.color = (1.0, 0.96, 0.92)
    key_obj = bpy.data.objects.new(name="Review_KeyLight", object_data=key_data)
    key_obj.location = center + Vector((dist * 0.7, -dist * 0.7, dist * 0.8))
    col.objects.link(key_obj)
    
    # 2. Fill Light (Opposite side, soft cool tint, 35% power)
    fill_data = bpy.data.lights.new(name="Review_FillLight", type='AREA')
    fill_data.energy = size * 110.0
    fill_data.size = size * 1.5
    fill_data.color = (0.85, 0.92, 1.0)
    fill_obj = bpy.data.objects.new(name="Review_FillLight", object_data=fill_data)
    fill_obj.location = center + Vector((-dist * 0.8, -dist * 0.5, dist * 0.4))
    col.objects.link(fill_obj)
    
    # 3. Rim / Back Light (Directly behind and above for silhouette separation)
    rim_data = bpy.data.lights.new(name="Review_RimLight", type='SPOT')
    rim_data.energy = size * 450.0
    rim_data.spot_size = math.radians(60)
    rim_data.spot_blend = 0.3
    rim_data.color = (1.0, 1.0, 1.0)
    rim_obj = bpy.data.objects.new(name="Review_RimLight", object_data=rim_data)
    rim_obj.location = center + Vector((0, dist * 0.9, dist * 1.0))
    col.objects.link(rim_obj)
    
    # Track to center constraint for each light
    for light_obj in [key_obj, fill_obj, rim_obj]:
        const = light_obj.constraints.new(type='TRACK_TO')
        empty = get_or_create_focus_empty(center)
        const.target = empty
        const.track_axis = 'TRACK_NEGATIVE_Z'
        const.up_axis = 'UP_Y'

def get_or_create_focus_empty(center):
    if "Review_FocusTarget" in bpy.data.objects:
        empty = bpy.data.objects["Review_FocusTarget"]
    else:
        empty = bpy.data.objects.new("Review_FocusTarget", None)
        bpy.context.scene.collection.objects.link(empty)
    empty.location = center
    return empty

def setup_review_camera(viewpoint="ISO"):
    """
    viewpoint options: 'ISO' (Isometric 3/4), 'FRONT', 'SIDE', 'TOP'
    """
    center, size = get_scene_focus_target()
    setup_studio_lighting(center, size)
    empty = get_or_create_focus_empty(center)
    
    if "Review_Camera" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["Review_Camera"], do_unlink=True)
        
    cam_data = bpy.data.cameras.new(name="Review_Camera")
    cam_data.lens = 50.0
    cam_obj = bpy.data.objects.new(name="Review_Camera", object_data=cam_data)
    
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    
    dist = size * 2.2
    
    if viewpoint == "FRONT":
        cam_obj.location = center + Vector((0, -dist, size * 0.1))
    elif viewpoint == "SIDE":
        cam_obj.location = center + Vector((dist, 0, size * 0.1))
    elif viewpoint == "TOP":
        cam_obj.location = center + Vector((0, 0, dist * 1.3))
    else:  # ISO (Isometric 3/4 default)
        cam_obj.location = center + Vector((dist * 0.75, -dist * 0.75, dist * 0.55))
        
    const = cam_obj.constraints.new(type='TRACK_TO')
    const.target = empty
    const.track_axis = 'TRACK_NEGATIVE_Z'
    const.up_axis = 'UP_Y'
    
    # Switch 3D Viewport to MATERIAL preview and clean overlays for crisp review
    try:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.shading.type = 'MATERIAL'
                            space.overlay.show_overlays = False
    except Exception:
        pass
        
    print(f"=== BX_REVIEW_READY: Viewpoint set to {viewpoint}, Focus Center: {list(round(c, 2) for c in center)}, Size: {round(size, 2)}m ===")

if __name__ == "__main__":
    setup_review_camera("ISO")
