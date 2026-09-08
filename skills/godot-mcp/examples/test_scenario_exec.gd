# Шаблон для передачи в godot_exec (source) внутри запущенного процесса игры.
# В скоупе доступны: Autoloads (GameManager, и т.д.), tree (SceneTree), root, holder (Node).

# 1. Точечная модификация игрового состояния без debug-хуков в кодовой базе
if "GameManager" in root.get_node_or_null("/root"):
	var gm = root.get_node("/root/GameManager")
	# Пример: сброс состояния партии, установка параметров для теста
	if gm.has_method("reset_board"):
		gm.reset_board()

# 2. Спавн тестового бота или таймера под `holder` (переживает смену сцен)
var bot_name := "McpTestWatcher"
if not holder.has_node(bot_name):
	var watcher := Node.new()
	watcher.name = bot_name
	holder.add_child(watcher)

# 3. Всегда возвращать JSON.stringify для сложных структур (Array/Dictionary),
# чтобы предотвратить усечение вывода MCP до 200 символов:
var report := {
	"status": "ready",
	"scene": tree.current_scene.name if tree.current_scene else "none",
	"holder_children": holder.get_child_count()
}
return JSON.stringify(report)
