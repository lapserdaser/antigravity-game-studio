# res://scripts/combat/weapon_controller_example.gd
class_name WeaponControllerExample
extends Node2D

## Референсный контроллер оружия, реализующий стандарт Zero-Hardcode & Rich Inspector.
## Все параметры и ассеты настраиваются в инспекторе, внутренние узлы привязаны через %UniqueNode.

@export_group("Stats & Balance")
## Кастомный .tres ресурс с характеристиками. Настраивается в инспекторе.
@export var stats: CharacterStatsResource

@export_group("Assets & Prefabs")
## Сменные ассеты: звук выстрела и префаб пули. Перетаскиваются в инспекторе.
@export var shoot_sound: AudioStream
@export var bullet_scene: PackedScene

@export_group("Physics & Targeting")
## Битовые маски физических слоев. В инспекторе раскрываются в виде чекбоксов с именами слоев.
@export_flags_2d_physics var target_layers: int = 1

@export_group("External Dependencies")
## Ссылка на внешний UI-элемент (ProgressBar). Никаких get_node("../UI/AmmoBar")!
@export var ammo_progress_bar: ProgressBar

# Внутренние инкапсулированные узлы собственной сцены адресуются через Scene Unique Nodes (%)
@onready var _muzzle: Marker2D = %Muzzle
@onready var _audio_player: AudioStreamPlayer2D = %AudioStreamPlayer2D
@onready var _shoot_timer: Timer = %ShootTimer

var _current_ammo: int = 30

func _ready() -> void:
	# Защита от Null: мягкий fallback, если дизайнер забыл назначить ресурс в инспекторе
	if not stats:
		push_warning("[%s] CharacterStatsResource is missing! Applying default fallback." % name)
		stats = CharacterStatsResource.new()
	
	if _shoot_timer:
		_shoot_timer.wait_time = stats.combat_attack_cooldown
		_shoot_timer.one_shot = true

func shoot() -> void:
	if not _shoot_timer.is_stopped():
		return
	
	if not bullet_scene:
		push_warning("[%s] BulletScene is not assigned in Inspector! Cannot fire." % name)
		return
		
	# Спавн снаряда через инжектированный PackedScene
	var bullet: Node2D = bullet_scene.instantiate() as Node2D
	if bullet:
		get_parent().add_child(bullet)
		bullet.global_position = _muzzle.global_position
	
	# Воспроизведение звука через инжектированный AudioStream
	if shoot_sound and _audio_player:
		_audio_player.stream = shoot_sound
		_audio_player.play()
		
	_shoot_timer.start()
