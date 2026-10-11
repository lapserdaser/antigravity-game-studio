"""
bx_audit.py - Mesh & Scene Quality Audit for Blender MCP
Checks topology, manifold integrity, applied transforms, and bounding metrics.
Compatible with Blender 4.x and 5.x.
"""

import bpy
import bmesh
import mathutils
import json

def audit_mesh_object(obj):
    if obj.type != 'MESH':
        return {"name": obj.name, "status": "SKIPPED", "reason": "Not a mesh"}
    
    # 1. Check Transform application
    scale_applied = all(abs(s - 1.0) < 1e-4 for s in obj.scale)
    rot_applied = all(abs(r) < 1e-4 for r in obj.rotation_euler)
    
    # 2. Check Bounding Box & Dimensions (Blender: Z is up, X is right, Y is forward/backward)
    bbox_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
    min_z = min(c.z for c in bbox_corners)
    max_z = max(c.z for c in bbox_corners)
    height = max_z - min_z
    width = max(c.x for c in bbox_corners) - min(c.x for c in bbox_corners)
    depth = max(c.y for c in bbox_corners) - min(c.y for c in bbox_corners)
    
    is_grounded = abs(min_z) < 0.05  # Within 5cm of ground floor (Z=0)
    
    # 3. Topology Audit via BMesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    
    vert_count = len(bm.verts)
    edge_count = len(bm.edges)
    face_count = len(bm.faces)
    
    # Non-manifold checks
    non_manifold_edges = sum(1 for e in bm.edges if not e.is_manifold)
    non_manifold_verts = sum(1 for v in bm.verts if not v.is_manifold)
    loose_edges = sum(1 for e in bm.edges if len(e.link_faces) == 0)
    loose_verts = sum(1 for v in bm.verts if len(v.link_edges) == 0)
    
    # N-gons check (>4 verts)
    ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
    tri_count = sum(1 for f in bm.faces if len(f.verts) == 3)
    quad_count = sum(1 for f in bm.faces if len(f.verts) == 4)
    
    bm.free()
    
    issues = []
    if not scale_applied:
        issues.append(f"Unapplied Scale: {list(round(s, 3) for s in obj.scale)}")
    if not rot_applied:
        issues.append("Unapplied Rotation")
    if non_manifold_edges > 0:
        issues.append(f"Non-manifold edges: {non_manifold_edges}")
    if loose_verts > 0:
        issues.append(f"Loose vertices: {loose_verts}")
    if ngons > 0:
        issues.append(f"N-gons detected: {ngons} (recommend triangulation or quad remesh)")
        
    status = "PASS" if len(issues) == 0 else ("WARNING" if non_manifold_edges == 0 else "FAIL")
    
    return {
        "name": obj.name,
        "status": status,
        "metrics_meters": {
            "width_x": round(width, 3),
            "depth_y": round(depth, 3),
            "height_z": round(height, 3),
            "min_z_ground": round(min_z, 3),
            "is_grounded_z0": is_grounded
        },
        "topology": {
            "vertices": vert_count,
            "edges": edge_count,
            "faces": face_count,
            "tris": tri_count,
            "quads": quad_count,
            "ngons": ngons,
            "non_manifold_edges": non_manifold_edges,
            "non_manifold_verts": non_manifold_verts,
            "loose_edges": loose_edges,
            "loose_verts": loose_verts
        },
        "transforms": {
            "scale_applied": scale_applied,
            "rotation_applied": rot_applied
        },
        "issues": issues
    }

def audit_scene():
    mesh_objs = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    results = [audit_mesh_object(obj) for obj in mesh_objs]
    
    overall_status = "PASS"
    if any(r["status"] == "FAIL" for r in results):
        overall_status = "FAIL"
    elif any(r["status"] == "WARNING" for r in results):
        overall_status = "WARNING"
        
    report = {
        "total_mesh_objects": len(mesh_objs),
        "overall_status": overall_status,
        "objects": results
    }
    print("=== BX_AUDIT_REPORT_START ===")
    print(json.dumps(report, indent=2))
    print("=== BX_AUDIT_REPORT_END ===")
    return report

if __name__ == "__main__":
    audit_scene()
