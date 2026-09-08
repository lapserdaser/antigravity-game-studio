# Архитектурные стандарты 3D для Godot 4.x

## 1. Системы координат и единицы измерения
* **1 единица Godot = 1 метр**.
* **Оси**:
  * `+X` = Вправо (Right)
  * `+Y` = Вверх (Up)
  * `-Z` = Вперед (Forward)
  * `+Z` = Назад (Back)
* **Камеры и персонажи**: Всегда ориентировать «лицом» в сторону `-Z`.

## 2. Иерархия сцены (.tscn)
Правильная структура префаба в Godot:
```text
RootNode3D (CharacterBody3D / StaticBody3D / Area3D) [Scale: 1, 1, 1, Pivot at Y=0]
├── Visual (Node3D или MeshInstance3D) [Смещен по Y так, чтобы основание касалось пола]
│   └── (Дочерние меши, LODs)
├── CollisionShape3D [Сгенерирован строго по AABB меша]
├── Sockets / Markers (Marker3D)
│   ├── MuzzleMarker (точка вылета снаряда)
│   └── InteractionArea (Area3D триггер)
└── AnimationPlayer / AnimationTree (при наличии анимаций)
```

## 3. Чек-лист валидации (QA)
1. **Pivot check**: `root.global_position.y == 0` соответствует подошве объекта.
2. **Scale check**: `root.scale == Vector3(1, 1, 1)`. Никаких отрицательных или растянутых масштабов на корне.
3. **Collision check**: `CollisionShape3D` не пустой и не имеет нулевой размер (`size > Vector3(0.01, 0.01, 0.01)`).
4. **Mesh check**: Запуск `godot_validate_meshes` возвращает 0 ошибок (нет свернутых треугольников, нормали направлены наружу).
