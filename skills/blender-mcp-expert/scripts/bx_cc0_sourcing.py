"""
bx_cc0_sourcing.py - Studio CC0 Asset Sourcing, Ingestion & Kitbashing Standard
Provides automated download, import, scaling normalization, ground alignment,
and multi-asset kitbashing for CC0 / Public Domain 3D models in Blender MCP.
"""

import bpy
import urllib.request
import os
import ssl
from mathutils import Vector

SCRATCH_DIR = os.path.join(
    os.environ.get("USERPROFILE", os.path.expanduser("~")),
    ".gemini", "antigravity", "scratch", "cc0_cache"
)

# ==============================================================================
# 1. ПРОВЕРЕННЫЕ РЕПОЗИТОРИИ И ИСТОЧНИКИ CC0 (Verified CC0 Repositories)
# ==============================================================================

CC0_CURATED_SOURCES = {
    # Khronos Group official sample assets (CC0-1.0)
    "KHRONOS_TOY_CAR": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/ToyCar/glTF-Binary/ToyCar.glb",
    "KHRONOS_PBR_SPHERE": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/MetalRoughSpheres/glTF-Binary/MetalRoughSpheres.glb",
    "KHRONOS_LANTERN": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Lantern/glTF-Binary/Lantern.glb",
    "KHRONOS_CORSET": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Corset/glTF-Binary/Corset.glb",
    "KHRONOS_DUCK": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Duck/glTF-Binary/Duck.glb",
    
    # Kenney NL CC0 Game Kits (Vehicles, Characters, Props)
    "KENNEY_RACING_TRUCK_YELLOW": "https://raw.githubusercontent.com/KenneyNL/Starter-Kit-Racing/master/Models/GLTF%20format/vehicle-truck-yellow.glb",
    "KENNEY_RACING_SEDAN_BLUE": "https://raw.githubusercontent.com/KenneyNL/Starter-Kit-Racing/master/Models/GLTF%20format/vehicle-sedan-blue.glb",
    "KENNEY_RACING_RACER_RED": "https://raw.githubusercontent.com/KenneyNL/Starter-Kit-Racing/master/Models/GLTF%20format/vehicle-racer-red.glb",
    "KENNEY_RACING_SUITE_YELLOW": "https://raw.githubusercontent.com/KenneyNL/Starter-Kit-Racing/master/Models/GLTF%20format/vehicle-suit-yellow.glb",
    "KENNEY_3D_CHARACTER": "https://raw.githubusercontent.com/KenneyNL/Starter-Kit-3D-Platformer/master/Models/GLTF%20format/character.glb",
    "KENNEY_COIN": "https://raw.githubusercontent.com/KenneyNL/Starter-Kit-3D-Platformer/master/Models/GLTF%20format/coin.glb",
    "KENNEY_CHEST": "https://raw.githubusercontent.com/KenneyNL/Starter-Kit-3D-Platformer/master/Models/GLTF%20format/chest.glb",
}

# ==============================================================================
# 2. ЗАГРУЗКА И ИМПОРТ CC0 МОДЕЛЕЙ (Download & Ingestion)
# ==============================================================================

def download_file(url, local_filename):
    """Безопасно скачивает модель по URL в кэш."""
    if not os.path.exists(SCRATCH_DIR):
        os.makedirs(SCRATCH_DIR, exist_ok=True)
        
    out_path = os.path.join(SCRATCH_DIR, local_filename)
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return out_path
        
    print(f"Downloading CC0 asset from: {url}...")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Blender-Studio-Agent"}
    )
    with urllib.request.urlopen(req, context=ctx) as response, open(out_path, 'wb') as out_file:
        out_file.write(response.read())
        
    print(f"Downloaded: {out_path} ({os.path.getsize(out_path)} bytes)")
    return out_path

def import_cc0_model(file_path_or_url, asset_name="CC0_Asset", target_max_dimension=None, target_length_y=None):
    """
    Импортирует CC0 модель (.glb/.gltf/.obj) в Blender,
    создает отдельную коллекцию, нормализует масштаб и сажает пивот на Z=0.
    """
    if file_path_or_url.startswith("http://") or file_path_or_url.startswith("https://"):
        ext = os.path.splitext(file_path_or_url.split("?")[0])[1] or ".glb"
        safe_name = f"{asset_name}{ext}"
        local_path = download_file(file_path_or_url, safe_name)
    else:
        local_path = file_path_or_url
        
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Asset file not found: {local_path}")
        
    # Создаем изолированную коллекцию для этого ассета
    col = bpy.data.collections.new(asset_name)
    bpy.context.scene.collection.children.link(col)
    
    # Запоминаем текущие объекты до импорта
    existing_objs = set(bpy.data.objects.keys())
    
    # Импорт
    ext = os.path.splitext(local_path)[1].lower()
    if ext in [".glb", ".gltf"]:
        bpy.ops.import_scene.gltf(filepath=local_path)
    elif ext == ".obj":
        if hasattr(bpy.ops.wm, "obj_import"):
            bpy.ops.wm.obj_import(filepath=local_path)
        else:
            bpy.ops.import_scene.obj(filepath=local_path)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=local_path)
    else:
        raise ValueError(f"Unsupported format: {ext}")
        
    # Находим новые объекты
    new_objs = [bpy.data.objects[name] for name in bpy.data.objects.keys() if name not in existing_objs]
    
    # Перемещаем новые объекты в целевую коллекцию
    for obj in new_objs:
        for parent_col in obj.users_collection:
            parent_col.objects.unlink(obj)
        col.objects.link(obj)
        
    bpy.context.view_layer.update()
    
    # Создаем Root Empty для управления ассетом
    root = bpy.data.objects.new(f"{asset_name}_Root", None)
    root.empty_display_type = 'ARROWS'
    root.empty_display_size = 0.5
    col.objects.link(root)
    
    top_level_new = [o for o in new_objs if o.parent is None]
    for o in top_level_new:
        o.parent = root
        
    bpy.context.view_layer.update()
    
    # Измеряем AABB геометрии
    mesh_objs = [o for o in new_objs if o.type == 'MESH']
    if mesh_objs:
        all_corners = []
        for o in mesh_objs:
            for c in o.bound_box:
                all_corners.append(o.matrix_world @ Vector(c))
                
        min_x = min(c.x for c in all_corners)
        max_x = max(c.x for c in all_corners)
        min_y = min(c.y for c in all_corners)
        max_y = max(c.y for c in all_corners)
        min_z = min(c.z for c in all_corners)
        max_z = max(c.z for c in all_corners)
        
        current_dx = max_x - min_x
        current_dy = max_y - min_y
        current_dz = max_z - min_z
        current_max = max(current_dx, current_dy, current_dz)
        
        # Нормализация масштаба
        scale_factor = 1.0
        if target_length_y and current_dy > 0:
            scale_factor = target_length_y / current_dy
        elif target_max_dimension and current_max > 0:
            scale_factor = target_max_dimension / current_max
            
        if abs(scale_factor - 1.0) > 0.001:
            root.scale = (scale_factor, scale_factor, scale_factor)
            bpy.context.view_layer.update()
            
        # Привязка к полу (Z=0)
        # Пересчитываем min_z после масштабирования
        re_corners = []
        for o in mesh_objs:
            for c in o.bound_box:
                re_corners.append(o.matrix_world @ Vector(c))
        ground_z = min(c.z for c in re_corners)
        root.location.z -= ground_z
        
        # Центрирование по X и Y
        center_x = (min(c.x for c in re_corners) + max(c.x for c in re_corners)) / 2
        center_y = (min(c.y for c in re_corners) + max(c.y for c in re_corners)) / 2
        root.location.x -= center_x
        root.location.y -= center_y
        
        bpy.context.view_layer.update()
        
    print(f"=== CC0 ASSET IMPORTED: {asset_name} ===")
    print(f"Root: {root.name}, Mesh Parts: {len(mesh_objs)}, Normalized Scale: {root.scale[0]:.4f}")
    return root, new_objs

# ==============================================================================
# 3. КИТБАШИНГ И КОМБИНИРОВАНИЕ МОДЕЛЕЙ (Multi-Model Kitbash)
# ==============================================================================

def kitbash_assemble(base_root, part_roots_dict):
    """
    Прикрепляет дочерние CC0 компоненты (спойлеры, оружие, багаж, колеса)
    к базовому Root объекту по заданным смещениям.
    part_roots_dict: {root_obj: (offset_x, offset_y, offset_z, scale)}
    """
    for part_root, (ox, oy, oz, p_scale) in part_roots_dict.items():
        part_root.parent = base_root
        part_root.location = (ox, oy, oz)
        part_root.scale = (part_root.scale[0] * p_scale, part_root.scale[1] * p_scale, part_root.scale[2] * p_scale)
        
    bpy.context.view_layer.update()
    print(f"=== KITBASH ASSEMBLED: {len(part_roots_dict)} parts attached to {base_root.name} ===")
    return base_root
