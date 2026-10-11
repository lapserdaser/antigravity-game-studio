"""
export_game_ready.py - Game-Ready GLB & Master .blend Exporter
Enforces studio metric contract: Origin at base (Z=0), Scale 1.0, normals outside, clean GLB.
Compatible with Blender 4.x and 5.x.
"""

import bpy
import bmesh
import os
import json
from mathutils import Vector

def prepare_and_export_game_ready(export_glb_path, save_blend_path=None, pivot_mode="BOTTOM"):
    """
    pivot_mode: 'BOTTOM' (Z=0 at floor level) or 'CENTER' (Center of mass)
    """
    mesh_objs = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not mesh_objs:
        raise RuntimeError("No mesh objects found in scene to export.")
        
    bpy.ops.object.select_all(action='DESELECT')
    for obj in mesh_objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objs[0]
    
    # 1. Apply all existing transforms
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    
    # 2. Recalculate normals outward & remove loose elements
    for obj in mesh_objs:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        # Remove loose verts
        loose_verts = [v for v in bm.verts if len(v.link_edges) == 0]
        bmesh.ops.delete(bm, geom=loose_verts, context='VERTS')
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()
        
    # 3. Calculate bounding box of primary or grouped mesh
    all_corners = []
    for obj in mesh_objs:
        all_corners.extend([obj.matrix_world @ Vector(corner) for corner in obj.bound_box])
        
    min_x = min(c.x for c in all_corners)
    max_x = max(c.x for c in all_corners)
    min_y = min(c.y for c in all_corners)
    max_y = max(c.y for c in all_corners)
    min_z = min(c.z for c in all_corners)
    max_z = max(c.z for c in all_corners)
    
    width = max_x - min_x
    depth = max_y - min_y
    height = max_z - min_z
    
    # 4. Set Origin according to studio standard
    if pivot_mode == "BOTTOM":
        pivot_z = min_z
        pivot_point = Vector(((min_x + max_x) / 2.0, (min_y + max_y) / 2.0, pivot_z))
    else:
        pivot_point = Vector(((min_x + max_x) / 2.0, (min_y + max_y) / 2.0, (min_z + max_z) / 2.0))
        
    # Shift scene geometry so pivot_point sits exactly at World (0,0,0)
    for obj in mesh_objs:
        obj.location -= pivot_point
        
    bpy.ops.object.select_all(action='DESELECT')
    for obj in mesh_objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objs[0]
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    
    # 5. Ensure target directory exists
    export_dir = os.path.dirname(os.path.abspath(export_glb_path))
    os.makedirs(export_dir, exist_ok=True)
    
    # 6. Export to GLB
    # Check export_format argument safely
    bpy.ops.export_scene.gltf(
        filepath=os.path.abspath(export_glb_path),
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_yup=True, # Standard GLTF conversion (+Z Blender up -> +Y Godot/Web up)
        export_cameras=False,
        export_lights=False
    )
    
    # 7. Optionally save master .blend file
    saved_blend = None
    if save_blend_path:
        blend_dir = os.path.dirname(os.path.abspath(save_blend_path))
        os.makedirs(blend_dir, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(save_blend_path))
        saved_blend = os.path.abspath(save_blend_path)
        
    result = {
        "status": "SUCCESS",
        "exported_glb": os.path.abspath(export_glb_path),
        "saved_blend": saved_blend,
        "metrics": {
            "width_meters": round(width, 3),
            "depth_meters": round(depth, 3),
            "height_meters": round(height, 3),
            "pivot_mode": pivot_mode,
            "origin_at_world_zero": True
        },
        "mesh_objects_exported": [obj.name for obj in mesh_objs]
    }
    
    print("=== EXPORT_GAME_READY_START ===")
    print(json.dumps(result, indent=2))
    print("=== EXPORT_GAME_READY_END ===")
    return result

if __name__ == "__main__":
    # Example standalone execution with fallback
    import tempfile
    default_out = os.path.join(tempfile.gettempdir(), "studio_asset_export.glb")
    prepare_and_export_game_ready(default_out)
