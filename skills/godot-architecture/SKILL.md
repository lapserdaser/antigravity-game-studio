---
name: godot-architecture
description: >-
  Godot 4 Architecture, Zero-Hardcode & Rich Inspector standard.
  Mandatory for writing, refactoring, or reviewing GDScript, scenes (.tscn),
  and resources (.tres). Enforces Resource-Driven design, typed @export with
  @export_group, @export_range, physics bitmasks, Curve resources, Scene Unique Nodes (%Node),
  and zero string paths in code.
---

# Godot 4: Стандарт Zero-Hardcode & Rich Inspector

Обязательный стандарт студии для написания кода на GDScript, проектирования сцен (`.tscn`) и ресурсов (`.tres`). Главная цель стандарта — **полное устранение хардкода** и создание таких компонентов, которые любой геймдизайнер или разработчик может **удобно настраивать и редактировать руками в редакторе Godot**.

---

## 1. Фундаментальный закон Zero-Hardcode

Любая игровая сущность должна проектироваться так, чтобы её поведение, числовые параметры, визуальные и звуковые ассеты можно было изменить **прямо в инспекторе Godot**, не открывая файл скрипта.

| Что СТРОГО ЗАПРЕЩЕНО (Hardcode) | Что ОБЯЗАТЕЛЬНО ИСПОЛЬЗОВАТЬ (Inspector-First) |
|---|---|
| `preload("res://assets/sounds/hit.wav")` | `@export var hit_sound: AudioStream` |
| `preload("res://scenes/bullet.tscn")` | `@export var bullet_scene: PackedScene` |
| `$"UI/HealthBar"` или `get_node("CanvasLayer/Bar")` | `@export var health_bar: ProgressBar` (внешняя зависимость)<br>или `%HealthBar` (внутренний Scene Unique Node) |
| `var speed: float = 300.0` (голая переменная) | `@export_range(50.0, 1000.0, 10.0, "suffix:px/s") var move_speed: float = 300.0` |
| `collision_mask = 3` или `ray.collision_mask = 1 \| 2` | `@export_flags_2d_physics var target_layers: int` |
| Зашитая математика спада урона / ускорения | `@export var progression_curve: Curve` (настройка кривой в инспекторе) |
| Жесткие статы прямо в контроллере персонажа | `@export var stats: CharacterStatsResource` (кастомный `.tres` ресурс) |

---

## 2. Стандарт привязки ассетов и узлов

### 2.1. Внешние зависимости и сменные ассеты — ТОЛЬКО через `@export`
Никаких жестко прописанных путей `res://` внутри `.gd` файлов. Пути к файлам хранятся исключительно в манифестах сцен (`.tscn`) и ресурсов (`.tres`).

```gdscript
# ПЛОХО (Хардкод: замена звука или префаба требует правки кода)
const LASER_SOUND = preload("res://assets/audio/laser.wav")
const EXPLOSION_FX = preload("res://vfx/explosion.tscn")

# ХОРОШО (Любой звук и префаб выбирается/перетаскивается в инспекторе)
@export_group("Audio & FX")
@export var laser_sound: AudioStream
@export var explosion_scene: PackedScene
```

### 2.2. Навигация по узлам: `@export` vs Scene Unique Nodes (`%`)
* **Внешние узлы** (UI-элементы другого экрана, камера, точка спавна снарядов, глобальный таргет) $\rightarrow$ объявлять через `@export var target_node: NodePath` или `@export var target_node: CanvasItem`.
* **Приватные внутренние узлы** инкапсулированной сцены (собственный `AnimationPlayer`, `CollisionShape2D`, `Sprite2D`) $\rightarrow$ использовать **Scene Unique Nodes** с префиксом `%` (например, `@onready var anim_player: AnimationPlayer = %AnimationPlayer`).
* **СТРОГО ЗАПРЕЩЕНЫ**: пути вида `get_node("../../../Player")` или `$"SubViewport/UI/Container/Button"`. При любом перемещении ноды в дереве такой код крашит игру.

---

## 3. Стандарт "Rich Inspector" (Удобство настройки руками)

Чтобы инспектор Godot оставался чистым, понятным и удобным для рук, соблюдать правила:

### 3.1. Обязательная группировка (`@export_group`, `@export_subgroup`)
Если у скрипта $\ge 3$ экспортируемых параметров, группировка обязательна. Указывайте префикс группы, чтобы Godot скрывал избыточные приставки в именах полей:

```gdscript
@export_group("Movement Settings", "move_")
@export_range(10.0, 1000.0, 10.0, "suffix:px/s") var move_speed: float = 300.0
@export_range(0.0, 1.0, 0.05) var move_acceleration: float = 0.2
@export_range(0.0, 1.0, 0.05) var move_friction: float = 0.15

@export_subgroup("Jumping", "jump_")
@export_range(-1500.0, -100.0, 50.0, "suffix:px/s") var jump_velocity: float = -600.0
@export_range(0.0, 0.5, 0.02, "suffix:s") var jump_coyote_time: float = 0.12
```

### 3.2. Слайдеры и единицы измерения (`@export_range`)
Числа никогда не объявляются как простой `@export var value: float`. Всегда задавайте разумный диапазон, шаг изменения и единицу измерения:
* Время: `"suffix:s"` или `"suffix:ms"`
* Скорость: `"suffix:px/s"` или `"suffix:m/s"`
* Углы: `"suffix:deg"`
* Здоровье / Опыт: `"suffix:hp"`, `"suffix:xp"`
* Проценты: `@export_range(0.0, 1.0, 0.01)`

### 3.3. Физические слои через битовые маски
Для слоев коллизий используйте специальные аннотации:
```gdscript
@export_group("Collision Filters")
@export_flags_2d_physics var hit_scan_mask: int = 1
@export_flags_2d_physics var terrain_mask: int = 2
```
В инспекторе отобразятся чекбоксы с понятными именами слоев из `Project Settings -> Layer Names`.

### 3.4. Нелинейное поведение через `Curve`
Вместо математических формул затухания, отдачи оружия или кривых ускорения используйте `Curve`:
```gdscript
@export_group("Damage Falloff")
@export var distance_damage_curve: Curve
```
Дизайнер может кликнуть на поле в Godot и нарисовать кривую от руки за 5 секунд.

---

## 4. Паттерн Resource-Driven Architecture (`.tres`)

Все характеристики персонажей, оружия, волн врагов и предметов должны описываться через кастомные классы `Resource`.

### 4.1. Создание ресурсного класса
```gdscript
# res://scripts/resources/character_stats.gd
class_name CharacterStats
extends Resource

@export_group("Health")
@export_range(1, 10000, 1, "suffix:hp") var max_health: int = 100
@export_range(0.0, 50.0, 0.5, "suffix:hp/s") var health_regen: float = 1.0

@export_group("Mobility")
@export_range(10.0, 1500.0, 10.0, "suffix:px/s") var base_speed: float = 250.0
@export_range(1.0, 3.0, 0.1) var sprint_multiplier: float = 1.6
```

### 4.2. Преимущества для пользователя
* Создание нового типа врага («Элитный гоблин») = ПКМ в Godot $\rightarrow$ `New Resource...` $\rightarrow$ `CharacterStats` $\rightarrow$ сохранение в `goblin_elite_stats.tres`.
* **Ноль строк кода** для нового балансного варианта!

---

## 5. Принцип Out-of-the-Box Ready & Fallback Safety

1. **Готовность префабов к запуску (F6)**:
   При создании новой сцены (.tscn) агент **обязан**:
   * Создать базовый ресурс с дефолтными статами (например, `res://data/enemies/goblin_default_stats.tres`).
   * Назначить этот ресурс в инспекторе созданной сцены.
   * Слинковать все дочерние узлы и ноды.
   * Сцена обязана успешно запускаться по **F6** сразу после создания без ошибок `Invalid get index` или `null instance`.

2. **Защитный код (Defensive Fallback)**:
   В коде скрипта обязательна проверка на случай, если пользователь удалит ресурс в инспекторе:
   ```gdscript
   @export_group("Configuration")
   @export var stats: CharacterStats

   func _ready() -> void:
       if not stats:
           push_warning("[%s] CharacterStats is not assigned! Creating default fallback." % name)
           stats = CharacterStats.new()
   ```

---

## 6. Автоматическая проверка: скрипт-валидатор

Перед сдачей любого GDScript кода или сцен агент обязан запустить локальный валидатор:

```powershell
python "C:\Users\Денис\.gemini\config\skills\godot-architecture\scripts\audit_zero_hardcode.py" "res://path/to/script_or_folder"
```

Скрипт проверяет:
1. Отсутствие `preload("res://...")` и `load("res://...")` внутри `.gd` файлов.
2. Отсутствие прямых путей `get_node("...")` и `$A/B` без `%UniqueName`.
3. Наличие `@export_group` при количестве экспортов $\ge 3$.
4. Отсутствие зашитых магических констант урона, здоровья и скорости без `@export`.
