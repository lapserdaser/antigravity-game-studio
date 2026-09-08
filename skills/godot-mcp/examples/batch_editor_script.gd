@tool
extends EditorScript

# Шаблон пакетной модификации сцены в редакторе Godot через scratch-скрипт.
# Запускается без микровызовов godot_node_edit.

func _run() -> void:
	var interface := get_editor_interface()
	var root := interface.get_edited_scene_root()
	if not root:
		printerr("BATCH_ERROR: No active scene opened in editor.")
		return

	var modified_count := 0
	
	# Пример: пакетный поиск и настройка узлов
	for child in root.get_children():
		if child is CanvasItem and child.is_in_group("ui_elements"):
			# Пакетное обновление параметров
			child.visible = true
			modified_count += 1

	# Краткий отчет в stdout для агента (1-2 токена)
	print("BATCH_SUCCESS: modified %d nodes in scene '%s'" % [modified_count, root.name])
