---
name: godot-mcp
description: >-
  Workflows, best practices, and quota-efficient batch automation patterns for Godot MCP (godot-mcp).
  Activate whenever the user or task involves Godot MCP tools, runtime state inspection, node editing,
  scene generation, test automation, or headless script execution in Godot.
---

# Godot MCP Skill (Token-Efficient Live Workflow)

Практическое руководство и регламент для взаимодействия с движком Godot через сервер `godot-mcp` с максимальной экономией квот контекста и предотвращением ошибок.

---

## 1. Архитектурные принципы и квотная безопасность

1. **Scratch Batching (Пакетный запуск вместо цепочек вызовов)**:
   * **Запрещено**: Создавать или менять ноды/сцены по одной через повторные микровызовы (`godot_node_edit`, `godot_scene` и др.).
   * **Стандарт**: Создавать файл пакетного скрипта в `scratch/run_batch.gd` (на базе `EditorScript`) и запускать его за 1 вызов.
   * *Пример шаблона*: см. [batch_editor_script.gd](./examples/batch_editor_script.gd).

2. **Запрет визуального спама (Zero-Screenshot Policy)**:
   * Скриншоты (`screenshot_game`, `screenshot_editor`) создают тяжелые токены, которые оседают в истории диалога навсегда.
   * Для проверки позиций, переменных, состояния узлов и интерфейса использовать легковесный текстовый слепок: `godot_runtime_state` (действие `digest`).
   * Чтобы прочитать глобальный синглтон (например, `GameManager`), указывать абсолютный путь: `paths: ["/root/GameManager"]`.
   * Для богатой телеметрии без скриншотов рекомендовать добавление метода `func _mcp_state() -> Dictionary` на ключевые ноды.

3. **Лимит двух ошибок (Fail-Fast: 2)**:
   * Если вызов инструмента `godot_*` вернул ошибку связи (сокет недоступен, тайм-аут, редактор закрыт) **2 раза подряд** — немедленно прервать попытки.
   * Запросить у пользователя проверку:
     1. Запущен ли редактор Godot с целевым проектом.
     2. Включен ли аддон `godot-mcp` в `Project -> Project Settings -> Plugins`.

4. **Правила жизненного цикла Godot (Quirks)**:
   * **Правка `.gd` скриптов**: Перезапуск редактора НЕ нужен. Вызвать `godot_editor_edit(action: "stop")` $\rightarrow$ `godot_editor_edit(action: "run")`. Запущенный инстанс игры считывает скрипты свежими прямо с диска.
   * **Правка `project.godot`**: Редактор не перечитывает конфигурационный файл автоматически. Вызвать `godot_project(action: "check_stale")`, а при смене autoload или input map — перезапустить редактор (`godot_editor_edit(action: "restart")`).
   * **Сбои 3D-рендера**: При черных текстурах или проблемах со светом сначала запустить `godot_validate_meshes`, чтобы исключить битые нормали/тангенсы процедурных мешей, прежде чем крутить источники света.

---

## 2. Основные рабочие сценарии (Workflows)

### Сценарий 1: Быстрая итерация по коду скрипта
1. Выполнить точечную замену кода в целевом файле (`replace_file_content`).
2. Если игра уже запущена в тестовом режиме:
   ```json
   // Вызов 1: остановить старый процесс
   {"action": "stop"} // godot_editor_edit
   // Вызов 2: запустить с подхватом обновленного .gd с диска
   {"action": "run"} // godot_editor_edit
   ```
3. Редактор перезапускать НЕ требуется.

### Сценарий 2: Детерминированный плейтест и проверка механики
Для надежной проверки без ручных кликов мыши:
1. Запустить игру с заморозкой времени:
   `godot_editor_edit(action: "run", frozen: true)`
2. Настроить тестовую ситуацию через инъекцию:
   `godot_exec(action: "run", source: "...")` (см. [test_scenario_exec.gd](./examples/test_scenario_exec.gd)).
3. Продвинуть время до наступления условия и сразу получить отчет:
   ```json
   {
     "action": "step_until",
     "until": "tree.get_nodes_in_group('pieces').size() > 0",
     "report": ["tree.get_nodes_in_group('pieces').size()", "root.get_node('/root/GameManager').current_turn"],
     "max_ms": 5000
   }
   ```
   *(Аргумент `report` исключает необходимость отдельного вызова для снятия показаний!)*

### Сценарий 3: Массовая генерация/настройка узлов сцены
1. Записать логику создания в `scratch/build_scene_batch.gd`.
2. Выполнить скрипт в редакторе Godot за 1 операцию.
3. Проверить результат кратким чтением `godot_node_read(action: "describe")`.

---

## 3. Справочные материалы

* Полная матрица стоимости инструментов и правила вызова: [godot_tools_cheatsheet.md](./references/godot_tools_cheatsheet.md).
* Шаблон пакетного EditorScript: [batch_editor_script.gd](./examples/batch_editor_script.gd).
* Шаблон сценарного exec-модуля: [test_scenario_exec.gd](./examples/test_scenario_exec.gd).
