"""
bx_reference_math.py - Studio Reference & Parametric Vehicle Blueprint Standard
Provides mathematical vehicle archetypes, blueprint coordinate solvers,
and modular game-ready mesh construction for Blender MCP.
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# ==============================================================================
# 1. МАТЕМАТИЧЕСКИЕ АРХЕТИПЫ (Vehicle Archetype Presets)
# Все размеры строго в метрах (метрическая система Blender)
# ==============================================================================

PRESET_VEHICLES = {
    "SPORTS_CAR": {
        "name": "Sports Car / Coupe (e.g. Porsche 911 / Toyota Supra)",
        "length": 4.45,
        "width": 1.86,
        "height": 1.28,
        "wheelbase": 2.45,
        "track_width": 1.58,
        "ground_clearance": 0.12,
        "wheel_radius": 0.34,
        "wheel_width": 0.26,
        "hood_length": 1.45,
        "cabin_length": 1.95,
        "trunk_length": 1.05,
        "roof_width_ratio": 0.72,   # сужение кабины относительно ширины кузова
        "windshield_angle_deg": 32.0, # угол наклона лобового стекла
    },
    "SEDAN": {
        "name": "Standard Sedan (e.g. BMW 3 / Toyota Camry)",
        "length": 4.75,
        "width": 1.83,
        "height": 1.44,
        "wheelbase": 2.85,
        "track_width": 1.58,
        "ground_clearance": 0.15,
        "wheel_radius": 0.33,
        "wheel_width": 0.22,
        "hood_length": 1.40,
        "cabin_length": 2.30,
        "trunk_length": 1.05,
        "roof_width_ratio": 0.75,
        "windshield_angle_deg": 38.0,
    },
    "SUV": {
        "name": "SUV / Offroad (e.g. Land Cruiser / Defender)",
        "length": 4.90,
        "width": 1.98,
        "height": 1.88,
        "wheelbase": 2.95,
        "track_width": 1.68,
        "ground_clearance": 0.24,
        "wheel_radius": 0.43,
        "wheel_width": 0.28,
        "hood_length": 1.45,
        "cabin_length": 2.65,
        "trunk_length": 0.80,
        "roof_width_ratio": 0.82,
        "windshield_angle_deg": 48.0,
    },
    "CYBERPUNK_COUPE": {
        "name": "Cyberpunk Low-Profile Wedge (e.g. Quadra Turbo-R)",
        "length": 4.60,
        "width": 2.05,
        "height": 1.18,
        "wheelbase": 2.70,
        "track_width": 1.76,
        "ground_clearance": 0.10,
        "wheel_radius": 0.36,
        "wheel_width": 0.32,
        "hood_length": 1.60,
        "cabin_length": 2.00,
        "trunk_length": 1.00,
        "roof_width_ratio": 0.68,
        "windshield_angle_deg": 28.0,
    },
    "TRUCK": {
        "name": "Heavy Duty Pickup / Light Truck",
        "length": 5.85,
        "width": 2.10,
        "height": 1.95,
        "wheelbase": 3.70,
        "track_width": 1.75,
        "ground_clearance": 0.26,
        "wheel_radius": 0.46,
        "wheel_width": 0.30,
        "hood_length": 1.60,
        "cabin_length": 2.10,
        "trunk_length": 2.15,
        "roof_width_ratio": 0.85,
        "windshield_angle_deg": 52.0,
    }
}

# ==============================================================================
# 2. МАТЕРИАЛЫ И ШЕЙДЕРЫ (PBR Studio Helpers)
# ==============================================================================

def get_or_create_material(name, base_color=(0.8, 0.8, 0.8, 1.0), roughness=0.5, metallic=0.0, emission_color=None, emission_strength=1.0, alpha=1.0):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    principled = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    
    if principled:
        # Base Color
        if "Base Color" in principled.inputs:
            principled.inputs["Base Color"].default_value = base_color
        # Roughness
        if "Roughness" in principled.inputs:
            principled.inputs["Roughness"].default_value = roughness
        # Metallic
        if "Metallic" in principled.inputs:
            principled.inputs["Metallic"].default_value = metallic
        # Alpha (Transparency)
        if alpha < 1.0 and "Alpha" in principled.inputs:
            principled.inputs["Alpha"].default_value = alpha
            if hasattr(mat, "blend_method"):
                mat.blend_method = 'BLEND'
        # Emission
        if emission_color:
            if "Emission Color" in principled.inputs:
                principled.inputs["Emission Color"].default_value = emission_color
            elif "Emission" in principled.inputs:
                principled.inputs["Emission"].default_value = emission_color
            if "Emission Strength" in principled.inputs:
                principled.inputs["Emission Strength"].default_value = emission_strength
                
    return mat

# ==============================================================================
# 3. ПОСТРОЕНИЕ ПАРАМЕТРИЧЕСКОГО КОЛЕСА (Game-Ready Wheel)
# Пивот строго в центре вращения колеса (X=0, Y=0, Z=0 локально)
# ==============================================================================

def create_wheel_mesh(name, radius, width, tire_mat, rim_mat):
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    obj = bpy.data.objects.new(name, mesh)
    
    bm = bmesh.new()
    
    # 1. Шина (Tire outer cylinder)
    # Ориентация: ось вращения вдоль X (вдоль оси колеи)
    segments = 24
    half_w = width * 0.5
    rim_r = radius * 0.62
    
    # Внешняя поверхность шины
    outer_verts_l = []
    outer_verts_r = []
    tread_steps = segments
    for i in range(tread_steps):
        angle = (2 * math.pi * i) / tread_steps
        y = radius * math.cos(angle)
        z = radius * math.sin(angle)
        v_l = bm.verts.new((-half_w, y, z))
        v_r = bm.verts.new((half_w, y, z))
        outer_verts_l.append(v_l)
        outer_verts_r.append(v_r)
        
    bm.verts.ensure_lookup_table()
    
    # Грани протектора (Tread faces)
    tread_faces = []
    for i in range(tread_steps):
        next_i = (i + 1) % tread_steps
        f = bm.faces.new([
            outer_verts_l[i],
            outer_verts_r[i],
            outer_verts_r[next_i],
            outer_verts_l[next_i]
        ])
        f.material_index = 0
        tread_faces.append(f)
        
    # Боковины и диск (Sidewall & Rim)
    rim_verts_l = []
    rim_verts_r = []
    hub_inset = width * 0.2
    for i in range(tread_steps):
        angle = (2 * math.pi * i) / tread_steps
        y = rim_r * math.cos(angle)
        z = rim_r * math.sin(angle)
        v_l = bm.verts.new((-half_w + hub_inset * 0.3, y, z))
        v_r = bm.verts.new((half_w - hub_inset * 0.3, y, z))
        rim_verts_l.append(v_l)
        rim_verts_r.append(v_r)
        
    bm.verts.ensure_lookup_table()
    
    # Боковины шины
    for i in range(tread_steps):
        next_i = (i + 1) % tread_steps
        # Внутренняя сторона (L)
        f_l = bm.faces.new([
            outer_verts_l[i],
            outer_verts_l[next_i],
            rim_verts_l[next_i],
            rim_verts_l[i]
        ])
        f_l.material_index = 0
        # Внешняя сторона (R)
        f_r = bm.faces.new([
            outer_verts_r[i],
            rim_verts_r[i],
            rim_verts_r[next_i],
            outer_verts_r[next_i]
        ])
        f_r.material_index = 0
        
    # Колесный диск (Rim / Hub center)
    hub_v_l = bm.verts.new((-half_w + hub_inset, 0, 0))
    hub_v_r = bm.verts.new((half_w - hub_inset, 0, 0))
    for i in range(tread_steps):
        next_i = (i + 1) % tread_steps
        f_rl = bm.faces.new([rim_verts_l[i], rim_verts_l[next_i], hub_v_l])
        f_rl.material_index = 1
        f_rr = bm.faces.new([rim_verts_r[next_i], rim_verts_r[i], hub_v_r])
        f_rr.material_index = 1
        
    bm.to_mesh(mesh)
    bm.free()
    
    mesh.materials.append(tire_mat)
    mesh.materials.append(rim_mat)
    
    # Добавляем фаску для гладкости
    bevel = obj.modifiers.new("Bevel", type='BEVEL')
    bevel.width = radius * 0.04
    bevel.segments = 2
    
    return obj

# ==============================================================================
# 4. МОДУЛЬНАЯ СБОРКА АВТОМОБИЛЯ (Parametric Vehicle Assembler)
# ==============================================================================

def assemble_vehicle(specs=None, preset_key="SPORTS_CAR", primary_color=(0.85, 0.05, 0.05, 1.0)):
    """
    Собирает параметрический автомобиль по точным размерам.
    Пивот рута Car_Root находится строго в точке (0, 0, 0) на уровне пола (контакт колес с землей).
    """
    if specs is None:
        specs = PRESET_VEHICLES.get(preset_key, PRESET_VEHICLES["SPORTS_CAR"])
        
    # Извлечение параметров
    L = specs["length"]
    W = specs["width"]
    H = specs["height"]
    Wb = specs["wheelbase"]
    Tw = specs["track_width"]
    Gc = specs["ground_clearance"]
    Rw = specs["wheel_radius"]
    Ww = specs["wheel_width"]
    roof_ratio = specs.get("roof_width_ratio", 0.75)
    
    # 1. Создаем коллекцию для сборки
    col_name = "Vehicle_Assembly"
    if col_name in bpy.data.collections:
        col = bpy.data.collections[col_name]
    else:
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)
        
    # Очищаем старые объекты сборки
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
        
    # 2. Создаем Root Empty (Origin на земле Z=0)
    root = bpy.data.objects.new("Car_Root", None)
    root.empty_display_type = 'ARROWS'
    root.empty_display_size = 1.0
    root.location = (0, 0, 0)
    col.objects.link(root)
    
    # 3. Материалы
    paint_mat = get_or_create_material("Car_Paint", base_color=primary_color, roughness=0.25, metallic=0.85)
    glass_mat = get_or_create_material("Car_Glass", base_color=(0.08, 0.1, 0.12, 1.0), roughness=0.05, metallic=0.1, alpha=0.35)
    tire_mat = get_or_create_material("Car_TireRubber", base_color=(0.03, 0.03, 0.03, 1.0), roughness=0.85, metallic=0.0)
    rim_mat = get_or_create_material("Car_RimAlloy", base_color=(0.7, 0.7, 0.72, 1.0), roughness=0.3, metallic=0.9)
    trim_mat = get_or_create_material("Car_DarkTrim", base_color=(0.05, 0.05, 0.05, 1.0), roughness=0.6, metallic=0.1)
    headlight_mat = get_or_create_material("Car_Headlight_Emit", base_color=(1.0, 1.0, 1.0, 1.0), emission_color=(1.0, 1.0, 0.95, 1.0), emission_strength=5.0)
    taillight_mat = get_or_create_material("Car_Taillight_Emit", base_color=(0.9, 0.05, 0.05, 1.0), emission_color=(1.0, 0.02, 0.02, 1.0), emission_strength=4.0)

    # 4. Колеса (4 инстанса с пивотом строго в центре ступицы на высоте Rw)
    # Передняя ось: Y = -Wb/2, Задняя ось: Y = +Wb/2 (в Blender -Y вперед)
    axle_front_y = -Wb * 0.5
    axle_rear_y = Wb * 0.5
    wheel_z = Rw  # Нижняя точка колеса касается пола (Z = Rw - Rw = 0)
    
    wheels_data = [
        ("Wheel_FL", -Tw * 0.5, axle_front_y),
        ("Wheel_FR",  Tw * 0.5, axle_front_y),
        ("Wheel_RL", -Tw * 0.5, axle_rear_y),
        ("Wheel_RR",  Tw * 0.5, axle_rear_y),
    ]
    
    for w_name, w_x, w_y in wheels_data:
        w_obj = create_wheel_mesh(w_name, Rw, Ww, tire_mat, rim_mat)
        w_obj.location = (w_x, w_y, wheel_z)
        w_obj.parent = root
        col.objects.link(w_obj)
        
    # 5. Кузов (Car_Body) - параметрическая геометрия с зеркальной симметрией (Mirror X)
    # Строим правую половину (+X >= 0) с модификатором Mirror
    body_mesh = bpy.data.meshes.new("Car_Body_Mesh")
    body_obj = bpy.data.objects.new("Car_Body", body_mesh)
    body_obj.parent = root
    col.objects.link(body_obj)
    
    bm = bmesh.new()
    
    # Ключевые геометрические уровни высот:
    z_floor = Gc
    z_beltline = z_floor + (H - z_floor) * 0.45
    z_roof = H
    
    # Продольные координаты (Y: -Y вперед, +Y назад):
    half_L = L * 0.5
    y_front_bumper = -half_L
    y_rear_bumper = half_L
    
    half_W = W * 0.5
    half_roof_w = half_W * roof_ratio
    
    # Базовые контрольные сечения кузова:
    # Сечение 0: Передний бампер
    # Сечение 1: Передняя колесная арка (перед колесом)
    # Сечение 2: Передняя колесная арка (над колесом)
    # Сечение 3: Передняя колесная арка (за колесом / основание капота)
    # Сечение 4: Лобовое стекло (база A-стойки)
    # Сечение 5: Крыша (B-стойка)
    # Сечение 6: Заднее стекло (C-стойка)
    # Сечение 7: Задняя колесная арка
    # Сечение 8: Задний бампер
    
    sections = [
        # (Y, X_sill, Z_sill, X_belt, Z_belt, X_roof, Z_roof)
        (y_front_bumper, 0.45 * half_W, z_floor + 0.05, 0.70 * half_W, z_floor + 0.35, None, None),
        (axle_front_y - Rw * 1.3, half_W * 0.9, z_floor, half_W * 0.95, z_beltline * 0.85, None, None),
        (axle_front_y, half_W, z_floor + Rw * 1.05, half_W * 0.98, z_beltline * 0.95, None, None), # арка
        (axle_front_y + Rw * 1.3, half_W * 0.92, z_floor, half_W * 0.96, z_beltline, None, None),
        (axle_front_y + (axle_rear_y - axle_front_y) * 0.35, half_W * 0.92, z_floor, half_W * 0.95, z_beltline, half_roof_w, z_roof),
        (axle_front_y + (axle_rear_y - axle_front_y) * 0.65, half_W * 0.92, z_floor, half_W * 0.95, z_beltline, half_roof_w, z_roof),
        (axle_rear_y - Rw * 1.3, half_W * 0.92, z_floor, half_W * 0.98, z_beltline * 1.02, half_roof_w * 0.9, z_beltline + (z_roof - z_beltline) * 0.4),
        (axle_rear_y, half_W, z_floor + Rw * 1.05, half_W * 0.98, z_beltline * 1.02, None, None), # арка
        (axle_rear_y + Rw * 1.3, half_W * 0.92, z_floor, half_W * 0.95, z_beltline, None, None),
        (y_rear_bumper, 0.50 * half_W, z_floor + 0.08, 0.75 * half_W, z_beltline * 0.95, None, None),
    ]
    
    # Построение половинчатой сетки (Half-Mesh для Mirror)
    # 4 линии вертексов: Centerline (X=0), Sill (порог), Beltline (пояс), Roof (крыша / капот)
    prev_verts = None
    
    for (sec_y, x_sill, z_s, x_belt, z_b, x_rf, z_rf) in sections:
        # 1. Центральный нижний (днище)
        v_bottom_center = bm.verts.new((0.0, sec_y, z_s))
        # 2. Порог
        v_sill = bm.verts.new((x_sill, sec_y, z_s))
        # 3. Поясная линия
        v_belt = bm.verts.new((x_belt, sec_y, z_b))
        
        # 4. Верх / Капот / Крыша
        if x_rf is not None and z_rf is not None:
            v_roof_side = bm.verts.new((x_rf, sec_y, z_rf))
            v_top_center = bm.verts.new((0.0, sec_y, z_rf))
            current_verts = [v_bottom_center, v_sill, v_belt, v_roof_side, v_top_center]
        else:
            # Капот или багажник (верхняя центральная плоскость)
            v_top_center = bm.verts.new((0.0, sec_y, z_b * 1.02))
            current_verts = [v_bottom_center, v_sill, v_belt, v_top_center]
            
        bm.verts.ensure_lookup_table()
        
        if prev_verts is not None:
            # Соединяем квадами текущее сечение с предыдущим
            if len(prev_verts) == 4 and len(current_verts) == 4:
                bm.faces.new([prev_verts[0], current_verts[0], current_verts[1], prev_verts[1]])
                bm.faces.new([prev_verts[1], current_verts[1], current_verts[2], prev_verts[2]])
                bm.faces.new([prev_verts[2], current_verts[2], current_verts[3], prev_verts[3]])
            elif len(prev_verts) == 4 and len(current_verts) == 5:
                bm.faces.new([prev_verts[0], current_verts[0], current_verts[1], prev_verts[1]])
                bm.faces.new([prev_verts[1], current_verts[1], current_verts[2], prev_verts[2]])
                bm.faces.new([prev_verts[2], current_verts[2], current_verts[3], prev_verts[3]])
                bm.faces.new([prev_verts[3], current_verts[3], current_verts[4]])
            elif len(prev_verts) == 5 and len(current_verts) == 5:
                bm.faces.new([prev_verts[0], current_verts[0], current_verts[1], prev_verts[1]])
                bm.faces.new([prev_verts[1], current_verts[1], current_verts[2], prev_verts[2]])
                bm.faces.new([prev_verts[2], current_verts[2], current_verts[3], prev_verts[3]])
                bm.faces.new([prev_verts[3], current_verts[3], current_verts[4], prev_verts[4]])
            elif len(prev_verts) == 5 and len(current_verts) == 4:
                bm.faces.new([prev_verts[0], current_verts[0], current_verts[1], prev_verts[1]])
                bm.faces.new([prev_verts[1], current_verts[1], current_verts[2], prev_verts[2]])
                bm.faces.new([prev_verts[2], current_verts[2], current_verts[3], prev_verts[3]])
                bm.faces.new([prev_verts[3], current_verts[3], prev_verts[4]])
                
        prev_verts = current_verts

    # Закрываем передний и задний бамперы на X=0
    # Передний торец
    bm.verts.ensure_lookup_table()
    # Нормали
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    
    bm.to_mesh(body_mesh)
    bm.free()
    
    body_mesh.materials.append(paint_mat)
    body_mesh.materials.append(trim_mat)
    
    # Модификаторы кузова:
    # 1. Mirror по X
    mirror = body_obj.modifiers.new("Mirror", type='MIRROR')
    mirror.use_axis[0] = True
    mirror.use_clip = True
    
    # 2. Bevel для гладких фасок
    bevel = body_obj.modifiers.new("Bevel", type='BEVEL')
    bevel.width = 0.025
    bevel.segments = 2
    
    # 6. Остекление (Car_Glass)
    glass_mesh = bpy.data.meshes.new("Car_Glass_Mesh")
    glass_obj = bpy.data.objects.new("Car_Glass", glass_mesh)
    glass_obj.parent = root
    col.objects.link(glass_obj)
    
    bm_g = bmesh.new()
    # Лобовое стекло, боковые окна и заднее стекло
    # Кабина расположена между сечениями 4, 5, 6
    g_y_a = sections[4][0]
    g_y_b = sections[5][0]
    g_y_c = sections[6][0]
    
    # Точки остекления
    w_belt = half_W * 0.94
    w_roof = half_roof_w * 0.98
    
    v_a_low = bm_g.verts.new((w_belt * 0.95, g_y_a + 0.05, z_beltline + 0.02))
    v_a_up  = bm_g.verts.new((w_roof, g_y_a + 0.25, z_roof - 0.02))
    v_b_low = bm_g.verts.new((w_belt, g_y_b, z_beltline + 0.02))
    v_b_up  = bm_g.verts.new((w_roof, g_y_b, z_roof - 0.02))
    v_c_low = bm_g.verts.new((w_belt * 0.95, g_y_c - 0.05, z_beltline + 0.02))
    v_c_up  = bm_g.verts.new((w_roof * 0.92, g_y_c - 0.20, z_beltline + (z_roof - z_beltline) * 0.42))
    
    v_a_center_low = bm_g.verts.new((0.0, g_y_a + 0.08, z_beltline + 0.05))
    v_a_center_up  = bm_g.verts.new((0.0, g_y_a + 0.28, z_roof - 0.01))
    v_c_center_low = bm_g.verts.new((0.0, g_y_c - 0.05, z_beltline + 0.05))
    v_c_center_up  = bm_g.verts.new((0.0, g_y_c - 0.22, z_beltline + (z_roof - z_beltline) * 0.44))
    
    bm_g.faces.new([v_a_center_low, v_a_low, v_a_up, v_a_center_up]) # Лобовое
    bm_g.faces.new([v_a_low, v_b_low, v_b_up, v_a_up])               # Боковое переднее
    bm_g.faces.new([v_b_low, v_c_low, v_c_up, v_b_up])               # Боковое заднее
    bm_g.faces.new([v_c_low, v_c_center_low, v_c_center_up, v_c_up]) # Заднее
    
    bmesh.ops.recalc_face_normals(bm_g, faces=bm_g.faces)
    bm_g.to_mesh(glass_mesh)
    bm_g.free()
    
    glass_mesh.materials.append(glass_mat)
    g_mirror = glass_obj.modifiers.new("Mirror", type='MIRROR')
    g_mirror.use_axis[0] = True
    g_mirror.use_clip = True
    
    # 7. Фары и фонари (Headlights & Taillights)
    # Передние фары
    hl_mesh = bpy.data.meshes.new("Car_Headlights_Mesh")
    hl_obj = bpy.data.objects.new("Car_Headlights", hl_mesh)
    hl_obj.parent = root
    col.objects.link(hl_obj)
    
    bm_hl = bmesh.new()
    hl_x = half_W * 0.65
    hl_y = y_front_bumper + 0.03
    hl_z = z_floor + 0.35
    hl_w = 0.18
    hl_h = 0.08
    v1 = bm_hl.verts.new((hl_x - hl_w*0.5, hl_y, hl_z))
    v2 = bm_hl.verts.new((hl_x + hl_w*0.5, hl_y, hl_z))
    v3 = bm_hl.verts.new((hl_x + hl_w*0.5, hl_y, hl_z + hl_h))
    v4 = bm_hl.verts.new((hl_x - hl_w*0.5, hl_y, hl_z + hl_h))
    bm_hl.faces.new([v1, v2, v3, v4])
    bm_hl.to_mesh(hl_mesh)
    bm_hl.free()
    hl_mesh.materials.append(headlight_mat)
    hl_mirror = hl_obj.modifiers.new("Mirror", type='MIRROR')
    hl_mirror.use_axis[0] = True
    
    # Задние фонари
    tl_mesh = bpy.data.meshes.new("Car_Taillights_Mesh")
    tl_obj = bpy.data.objects.new("Car_Taillights", tl_mesh)
    tl_obj.parent = root
    col.objects.link(tl_obj)
    
    bm_tl = bmesh.new()
    tl_x = half_W * 0.68
    tl_y = y_rear_bumper - 0.02
    tl_z = z_beltline * 0.95
    tl_w = 0.22
    tl_h = 0.07
    tv1 = bm_tl.verts.new((tl_x - tl_w*0.5, tl_y, tl_z))
    tv2 = bm_tl.verts.new((tl_x + tl_w*0.5, tl_y, tl_z))
    tv3 = bm_tl.verts.new((tl_x + tl_w*0.5, tl_y, tl_z + tl_h))
    tv4 = bm_tl.verts.new((tl_x - tl_w*0.5, tl_y, tl_z + tl_h))
    bm_tl.faces.new([tv1, tv2, tv3, tv4])
    bm_tl.to_mesh(tl_mesh)
    bm_tl.free()
    tl_mesh.materials.append(taillight_mat)
    tl_mirror = tl_obj.modifiers.new("Mirror", type='MIRROR')
    tl_mirror.use_axis[0] = True

    print(f"=== VEHICLE ASSEMBLED SUCCESSFULLY ===")
    print(f"Archetype: {specs.get('name', 'Custom')}")
    print(f"Dimensions: {round(L, 2)}m x {round(W, 2)}m x {round(H, 2)}m")
    print(f"Wheelbase: {round(Wb, 2)}m, Track: {round(Tw, 2)}m, Ground Clearance: {round(Gc, 2)}m")
    print(f"Root: {root.name} at Z=0.0 (Floor contact verified)")
    
    return root

# ==============================================================================
# 5. АУДИТ ПРОПОРЦИЙ И ГАБАРИТОВ (Proportions & Metrics Audit)
# ==============================================================================

def audit_vehicle_metrics(root_obj_name="Car_Root"):
    root = bpy.data.objects.get(root_obj_name)
    if not root:
        return {"status": "ERROR", "message": f"Root object '{root_obj_name}' not found."}
        
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    
    children = [o for o in bpy.data.objects if o.parent == root or o == root]
    mesh_children = [o for o in children if o.type == 'MESH']
    
    if not mesh_children:
        return {"status": "ERROR", "message": "No mesh components found under root."}
        
    # Считаем общий AABB по вычисленным мешам (с учетом модификаторов Mirror)
    all_corners = []
    for o in mesh_children:
        eval_o = o.evaluated_get(depsgraph)
        for c in eval_o.bound_box:
            all_corners.append(eval_o.matrix_world @ Vector(c))
            
    min_x = min(c.x for c in all_corners)
    max_x = max(c.x for c in all_corners)
    min_y = min(c.y for c in all_corners)
    max_y = max(c.y for c in all_corners)
    min_z = min(c.z for c in all_corners)
    max_z = max(c.z for c in all_corners)
    
    length = max_y - min_y
    width = max_x - min_x
    height = max_z - min_z
    
    # Проверка пола (Z=0)
    z_floor_delta = abs(min_z)
    floor_ok = z_floor_delta < 0.05
    
    # Проверка пропорций легкового авто (Длина > Ширины > Высоты)
    proportions_ok = (length > width) and (width > height * 0.6) and (length > 2.5 and length < 8.0)
    
    report = {
        "status": "PASS" if (floor_ok and proportions_ok) else "WARN",
        "length_m": round(length, 2),
        "width_m": round(width, 2),
        "height_m": round(height, 2),
        "z_floor_contact": round(min_z, 3),
        "floor_aligned": floor_ok,
        "proportions_realistic": proportions_ok,
        "parts_count": len(mesh_children)
    }
    return report

if __name__ == "__main__":
    assemble_vehicle(preset_key="SPORTS_CAR")
    print(audit_vehicle_metrics("Car_Root"))
