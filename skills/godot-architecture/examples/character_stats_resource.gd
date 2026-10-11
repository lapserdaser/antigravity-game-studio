# res://scripts/resources/character_stats_resource.gd
class_name CharacterStatsResource
extends Resource

## Референсный кастомный ресурс для характеристик персонажа / сущности.
## Настраивается в инспекторе Godot или сохраняется в .tres файлы для разных пресетов.

@export_group("Vital Stats", "vital_")
@export_range(1, 10000, 1, "suffix:hp") var vital_max_hp: int = 100
@export_range(0.0, 100.0, 0.5, "suffix:hp/s") var vital_hp_regen: float = 1.0

@export_group("Movement & Speed", "move_")
@export_range(10.0, 2000.0, 10.0, "suffix:px/s") var move_base_speed: float = 250.0
@export_range(1.0, 3.0, 0.05) var move_sprint_multiplier: float = 1.5

@export_group("Combat Tuning", "combat_")
@export_range(1, 500, 1, "suffix:dmg") var combat_base_damage: int = 25
@export_range(0.05, 5.0, 0.05, "suffix:s") var combat_attack_cooldown: float = 0.5
@export var combat_damage_falloff_curve: Curve

## Расчет итогового урона с учетом расстояния по кривой инспектора
func calculate_damage(distance: float, max_range: float) -> float:
	var ratio: float = clampf(distance / max_range, 0.0, 1.0)
	var falloff_mult: float = 1.0
	if combat_damage_falloff_curve:
		falloff_mult = combat_damage_falloff_curve.sample(ratio)
	return float(combat_base_damage) * falloff_mult
