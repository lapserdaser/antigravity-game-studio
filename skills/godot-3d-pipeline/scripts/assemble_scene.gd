@tool
extends EditorScript

## Универсальный скрипт сборки .tscn префаба из 3D-меша (.glb / .obj / Mesh)
## Исключает ручные правки текстового .tscn, гарантирует точные AABB и коллизии.
##
## Использование:
## 1. Заполните параметры ниже (или передайте их через аргументы).
## 2. В Script Editor выберите File -> Run (Ctrl+Shift+X).

const SOURCE_MODEL_PATH: String = "res://assets/models/item.glb"
const TARGET_SCENE_PATH: String = "res://scenes/item.tscn"
const ROOT_CLASS_NAME: String = "StaticBody3D" # CharacterBody3D, StaticBody3D, RigidBody3D, Area3D
const SNAP_PIVOT_TO_GROUND: bool = true
const AUTO_GENERATE_COLLIDER: bool = true

func _run() -> void:
	if not FileAccess.file_exists(SOURCE_MODEL_PATH):
		printerr("[AssembleScene] Исходный файл не существует: ", SOURCE_MODEL_PATH)
		return

	var root_node: Node3D = null
	match ROOT_CLASS_NAME:
		"CharacterBody3D":
			root_node = CharacterBody3D.new()
		"RigidBody3D":
			root_node = RigidBody3D.new()
		"Area3D":
			root_node = Area3D.new()
		_:
			root_node = StaticBody3D.new()

	var scene_name = TARGET_SCENE_PATH.get_file().get_basename().capitalize().replace(" ", "")
	root_node.name = scene_name

	# Загрузка визуальной модели
	var loaded_asset = load(SOURCE_MODEL_PATH)
	var visual_node: Node3D = null

	if loaded_asset is PackedScene:
		visual_node = loaded_asset.instantiate()
	elif loaded_asset is Mesh:
		var mi = MeshInstance3D.new()
		mi.mesh = loaded_asset
		visual_node = mi
	else:
		printerr("[AssembleScene] Неизвестный формат ассета: ", SOURCE_MODEL_PATH)
		return

	visual_node.name = "Visual"
	root_node.add_child(visual_node)
	visual_node.owner = root_node

	# Рекурсивный расчет общего AABB всех дочерних мешей
	var total_aabb := _get_combined_aabb(visual_node)
	print("[AssembleScene] Рассчитанный AABB: size=", total_aabb.size, " center=", total_aabb.get_center())

	# Выравнивание пивота в основание на уровень Y = 0
	if SNAP_PIVOT_TO_GROUND:
		var ground_offset = -total_aabb.position.y
		visual_node.position.y += ground_offset
		total_aabb.position.y += ground_offset
		print("[AssembleScene] Пивот выровнен по полу (смещение Y = +", ground_offset, ")")

	# Автоматическое создание формы коллизии
	if AUTO_GENERATE_COLLIDER and root_node is CollisionObject3D:
		var col_shape := CollisionShape3D.new()
		col_shape.name = "CollisionShape3D"
		var box := BoxShape3D.new()
		box.size = total_aabb.size
		col_shape.shape = box
		col_shape.position = total_aabb.get_center()

		root_node.add_child(col_shape)
		col_shape.owner = root_node
		print("[AssembleScene] Сгенерирован CollisionShape3D с размерами: ", box.size)

	# Сохранение .tscn
	var packed_scene := PackedScene.new()
	var pack_res = packed_scene.pack(root_node)
	if pack_res == OK:
		var save_err = ResourceSaver.save(packed_scene, TARGET_SCENE_PATH)
		if save_err == OK:
			print("[AssembleScene] Сцена успешно сохранена: ", TARGET_SCENE_PATH)
			EditorInterface.get_resource_filesystem().scan()
		else:
			printerr("[AssembleScene] Ошибка при сохранении сцены: ", save_err)
	else:
		printerr("[AssembleScene] Ошибка упаковки PackedScene: ", pack_res)

func _get_combined_aabb(node: Node) -> AABB:
	var combined := AABB()
	var is_first := true

	var meshes: Array[MeshInstance3D] = []
	if node is MeshInstance3D:
		meshes.append(node)
	for child in node.find_children("*", "MeshInstance3D", true, false):
		meshes.append(child)

	for mi in meshes:
		if mi.mesh:
			var mi_aabb = mi.transform * mi.mesh.get_aabb()
			if is_first:
				combined = mi_aabb
				is_first = false
			else:
				combined = combined.merge(mi_aabb)

	if is_first:
		return AABB(Vector3(-0.5, 0, -0.5), Vector3(1.0, 1.0, 1.0))
	return combined
