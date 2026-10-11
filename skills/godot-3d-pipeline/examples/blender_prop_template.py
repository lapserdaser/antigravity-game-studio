import bpy
import os

# [FALLBACK ONLY] Шаблон процедурного создания 3D-пропса в Blender через Blender MCP
# Применяется ИСКЛЮЧИТЕЛЬНО как Fallback при отсутствии готовых CC0 моделей (bx_cc0_sourcing)
# и невозможности сделать блокаут через Godot CSG. Выполняется через execute_blender_code.

def create_prop(output_glb_path: str):
    # 1. Очистка дефолтной сцены
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # 2. Создание базовой геометрии (пример: деревянный ящик / сундук)
    width = 1.0   # X
    depth = 0.8   # Y
    height = 0.9  # Z
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, height / 2.0))
    obj = bpy.context.active_object
    obj.name = "PropMesh"
    obj.scale = (width, depth, height)
    
    # Применение масштаба (Apply Scale обязателен перед модификаторами!)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    # 3. Добавление Bevel модификатора (скругление жестких ребер)
    bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = 0.04
    bevel.segments = 2
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    
    # 4. Смещение Origin (Pivot) строго в основание (Bottom-Center)
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    
    # 5. Автоматическая UV-развертка
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 6. Простой PBR материал
    mat = bpy.data.materials.new(name="PropMaterial")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.35, 0.22, 0.12, 1.0) # Древесный оттенок
        bsdf.inputs['Roughness'].default_value = 0.7
    obj.data.materials.append(mat)
    
    # 7. Экспорт в GLB
    os.makedirs(os.path.dirname(output_glb_path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=output_glb_path,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_yup=True
    )
    print(f"[Blender] Успешно экспортировано: {output_glb_path}")

# Пример вызова:
# create_prop("C:/path_to_project/assets/models/crate.glb")
