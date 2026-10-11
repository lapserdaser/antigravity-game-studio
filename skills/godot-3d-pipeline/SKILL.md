---
name: godot-3d-pipeline
description: >-
  Comprehensive 3D asset, model creation, and Godot scene (.tscn) workflow.
  Activate whenever the user or task involves creating, editing, importing,
  or troubleshooting 3D models, meshes, Blender assets, CSG, greyboxing,
  collision shapes, or .tscn scenes in Godot.
---

# Godot 3D & Scene Pipeline (Стандарт студии)

Регламент создания 3D-моделей, сборки сцен `.tscn`, настройки коллизий и интеграции с Blender MCP и Godot MCP без слепых итераций.

---

## 1. Фундаментальный запрет: «Zero Blind Edits»

* **СТРОГО ЗАПРЕЩЕНО**: Редактировать или создавать сложные 3D-меши, иерархии нод с трансформами и CSG вручную через слепую правку текстового формата `.tscn`.
* **Причина**: Текстовые координаты не валидируются движком. Это приводит к битым нормалям (невидимые полигоны), несовпадению коллизий с визуалом, смещенным пивотам (модель тонет в полу) и краху локальных идентификаторов (`ext_resource`/`sub_resource`).
* **Стандарт студии**:
  1. **Геометрия**: Загрузка готовых CC0 `.glb` ассетов (`bx_cc0_sourcing`) либо нативный CSG-блокаут в Godot (`CSGBox3D`, `CSGCombiner3D`). Процедурный `bpy`-код разрешен исключительно как параметрический чертежный Fallback (`bx_reference_math.py`) при отсутствии готовых моделей.
  2. **Сборка префаба `.tscn`**: Сцена собирается и сохраняется средствами самого движка Godot через `EditorScript` ([assemble_scene.gd](./scripts/assemble_scene.gd)) либо через атомарные команды Godot MCP.
  3. **Верификация**: Обязательный вызов `godot_validate_meshes` и `godot_scene3d(action: "get_bounds")`.

---

## 2. Метрический контракт (Обязательные параметры)

Перед началом генерации любой 3D-сущности агент обязан зафиксировать 4 параметра:
1. **Габариты (X, Y, Z в метрах)**: Например, персонаж = 0.8 x 1.8 x 0.6 м; дверь = 1.0 x 2.2 x 0.15 м.
2. **Пивот (Origin)**:
   * Напольные объекты, персонажи, пропсы, здания $\rightarrow$ **Bottom-Center** ($Y = 0$ строго на уровне пола/подошвы).
   * Летающие снаряды, физические шары, астероиды $\rightarrow$ **Center of Mass** ($[0, 0, 0]$ в геометрическом центре).
3. **Ориентация в пространстве Godot**: Лицо/перед объекта направлен вдоль оси **$-Z$**, верх — вдоль **$+Y$**.
4. **Масштаб (Scale)**: Корневой узел префаба ВСЕГДА имеет масштаб `Vector3(1, 1, 1)`. Никаких компенсаций масштаба через корень!

---

## 3. Рабочие сценарии (Workflows)

### Сценарий А: Получение 3D-модели (CC0 Sourcing / Godot CSG)
1. **Приоритет 1 (Готовые модели)**: Поиск проверенных CC0 / Public Domain моделей в сети (Kenney, Poly Haven, Khronos, Poly Pizza) через `search_web` и загрузка в `res://assets/models/` через `bx_cc0_sourcing.py`.
2. **Приоритет 2 (Прототипирование и блокаут)**: Создание геометрии нативно внутри Godot через `CSGBox3D`, `CSGCylinder3D`, `CSGCombiner3D` или примитивные `MeshInstance3D` без привлечения Blender.
3. **Параметрический Fallback**: Если готовых моделей нет и CSG недостаточен, допустима параметрическая чертежная сборка в Blender через `bx_reference_math.py`. Слепое процедурное кодирование мешей «из головы» запрещено.

### Сценарий Б: Сборка сцены префаба (.tscn) в Godot
1. Использовать пакетный `EditorScript` ([assemble_scene.gd](./scripts/assemble_scene.gd)).
2. Скрипт в редакторе Godot:
   * Инстанцирует меш или `.glb`.
   * Рассчитывает честный габаритный контейнер (AABB).
   * Автоматически создает правильный `CollisionShape3D` (BoxShape3D или ConvexPolygonShape3D) строго по AABB меша.
   * Добавляет необходимые точки крепления (`Marker3D` для спавна пуль, экипировки, камеры).
   * Назначает дефолтные материалы, слои коллизий и ресурсы строго по стандарту `godot-architecture` (Out-of-the-Box Ready).
   * Упаковывает сцену через `PackedScene.pack()` и сохраняет через `ResourceSaver.save()`.

### Сценарий В: Контроль качества (Quality Gate)
После создания или изменения 3D-сцены вызвать:
1. `godot_validate_meshes` — проверка на битые нормали, дыры в топологии и деформированные полигоны.
2. `godot_scene3d(action: "get_bounds", root_path: "...")` — проверка реального размера модели в метрах.

---

## 4. Справочные ресурсы
* Скрипт сборщика сцены: [assemble_scene.gd](./scripts/assemble_scene.gd)
* Шаблон скрипта Blender: [blender_prop_template.py](./examples/blender_prop_template.py)
* Архитектурные стандарты: [godot_3d_standards.md](./references/godot_3d_standards.md)
