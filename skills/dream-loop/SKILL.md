---
name: dream-loop
description: >-
  Autonomous Closed-Loop Vision Feedback Pipeline for Blender 3D modeling.
  Uses a multi-modal "Dream -> Build -> Capture -> Critique -> Refine" cycle
  where an Art Director evaluates live Blender viewport screenshots against a target
  concept or reference using a 5-point rubric with a strict 3-iteration cap.
---

# Autonomous Dream-Loop Pipeline (Стандарт визуальной доводки)

Замкнутый автономный цикл итеративного 3D-моделирования в Blender MCP, вдохновленный концепцией `dream-loop` и стандартами визуального контроля ведущих игровых студий.

---

## 1. Архитектура замкнутого цикла (Closed-Loop Workflow)

```mermaid
sequenceDiagram
    autonumber
    actor User as Пользователь / Запрос
    participant Director as Ведущий агент (Арт-директор)
    participant Builder as Субагент-строитель (Blender MCP)
    participant Blender as Живой Blender (MCP Server)

    User->>Director: "Создай стилизованную таверну / sci-fi турель"
    Note over Director: 1. DREAM (Целевой визуал)
    Director->>Director: Генерация концепта (generate_image) или анализ референса
    
    loop Максимум 3 итерации цикла (Fail-Fast Cap)
        Note over Builder,Blender: 2. BUILD (Сборка сцены)
        Director->>Builder: ТЗ + директивы по коду
        Builder->>Blender: execute_blender_code (bpy, пропсы, шейдеры)
        
        Note over Builder,Blender: 3. CAPTURE (Съемка вьюпорта)
        Builder->>Blender: bx_review.py (Свет + Камера ISO)
        Builder->>Blender: look(mode: viewport, max_size: 768)
        Blender-->>Director: Скриншот живого вьюпорта
        
        Note over Director: 4. CRITIQUE (Оценка по матрице)
        Director->>Director: Анализ скриншота по 5-балльной матрице (rubric.md)
        alt Оценка >= 19 баллов (PASS)
            Note over Director: Критерии выполнены! Выход из цикла.
        else Итерация < 3 (ITERATE)
            Director->>Builder: Punch-List конкретных правок
        else Итерация = 3 (FORCED_DELIVERY)
            Note over Director: Достигнут лимит. Фиксация текущего результата.
        end
    end

    Note over Builder,Blender: 5. DELIVER (Game-Ready Экспорт)
    Builder->>Blender: bx_audit.py (Проверка сетки)
    Builder->>Blender: export_game_ready.py (Origin Z=0, нормали, GLB + .blend)
    Director->>User: Сдача: Скриншот + GLB в проекте + Master .blend
```

---

## 2. Фазы выполнения

### Фаза 1: DREAM (Поиск готовых CC0 моделей и фиксация ориентиров)
1. **Поиск CC0 моделей в сети (`search_web`)**:
   Для абсолютно любого объекта (транспорт, архитектура, пропс, персонаж, оружие) ведущий агент **обязательно** выполняет поиск готовых **CC0 / Public Domain** 3D-моделей в открытых репозиториях (Khronos, Kenney, Poly Haven, Poly Pizza, GitHub).
2. **Многокомпонентный подбор (Kitbash Discovery)**:
   Если объект сложный, агент находит 1 или несколько моделей-доноров (например, шасси + надстройка, корпус + обвес).
3. **Фиксация габаритов в метрах**:
   Определяются целевые габариты ($L, W, H$) и привязка к полу ($Z = 0$).

### Фаза 2: BUILD (Импорт CC0, нормализация и китбашинг через Blender MCP)
Субагент `blender_3d_artist` (предварительно объявленный через `define_subagent` с `enable_mcp_tools: true` и `enable_write_tools: true`) либо основной агент:
1. Импортирует найденную модель (модели) через `bx_cc0_sourcing.import_cc0_model(url, asset_name, target_size)` или нативный MCP tool `import_asset`.
2. Очищает служебную геометрию, подставки, настраивает PBR-материалы (`BSDF_PRINCIPLED`).
3. При необходимости стыкует дополнительные CC0-компоненты через `bx_cc0_sourcing.kitbash_assemble`.
4. Только при полном отсутствии CC0 моделей переходит к процедурной fallback-сборке.

### Фаза 3: CAPTURE (Постановка света и съемка)
1. Выполняется скрипт студийного света и ракурса:
   ```python
   import sys, os
   scripts_dir = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), ".gemini", "config", "skills", "blender-mcp-expert", "scripts")
   if scripts_dir not in sys.path:
       sys.path.append(scripts_dir)
   import bx_review
   bx_review.setup_review_camera("ISO")
   ```
2. Вызывается инструмент съемки:
   `call_mcp_tool(ServerName: "blender", ToolName: "look", Arguments: {"mode": "viewport", "max_size": 768})`.

### Фаза 4: CRITIQUE (Визуальная критика по матрице)
Ведущий агент (Арт-директор) сопоставляет полученный скриншот с концептом по [Матрице рубрик](./references/rubric.md):
* **Силуэт и габариты** (1-5)
* **Свет и читаемость** (1-5)
* **Материалы и шейдинг** (1-5)
* **Чистота сетки и отсутствие артефактов** (1-5)
* **Соответствие исходному стилю** (1-5)

Если суммарный балл $\ge 19$ из 25 — переход к экспорту. Иначе составляется список точечных правок (Punch-List).

### Фаза 5: REFINE & FAIL-FAST LIMITS
* **СТРОГИЙ ЛИМИТ**: Не более **3 итераций** доработки.
* Каждая итерация исправляет только пункты из Punch-List, не переписывая всю сцену с нуля.

### Фаза 6: DELIVER (Сдача результата)
1. Вызов `bx_audit.py` для подтверждения целостности сетки.
2. Вызов `export_game_ready.py`:
   - Напольный пивот выставляется на $Z=0$;
   - Применяются трансформации;
   - Сохраняются `.glb` и `.blend`;
3. Отчет пользователю с итоговым скриншотом и путями к артефактам.
