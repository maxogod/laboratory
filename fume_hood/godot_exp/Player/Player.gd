extends CharacterBody2D

# var health = 10
const SPEED = 200.0
const JUMP_VELOCITY = -350.0

# Get the gravity from the project settings to be synced with RigidBody nodes.
var gravity = ProjectSettings.get_setting("physics/2d/default_gravity")

@onready var animation = get_node("AnimationPlayer")
@onready var collision_shape = $CollisionShape2D #is the same as using get_node

func _physics_process(delta):
	# Add the gravity.
	if not is_on_floor():
		velocity.y += gravity * delta

	# Handle Jump.
	if Input.is_action_just_pressed("ui_accept") and is_on_floor():
		velocity.y = JUMP_VELOCITY
		animation.play("Jump")
		
	# Get the input direction and handle the movement/deceleration.
	# As good practice, you should replace UI actions with custom gameplay actions.
	var direction = Input.get_axis("ui_left", "ui_right")
	if direction == -1:
		get_node("AnimatedSprite2D").flip_h = true
	elif direction == 1:
		get_node("AnimatedSprite2D").flip_h = false
	if direction and get_node("AnimatedSprite2D").animation != "Death":
		velocity.x = direction * SPEED
		if Input.is_key_pressed(KEY_SHIFT) and not is_on_floor():
			velocity.x = SPEED * 2 * direction
		if velocity.y == 0:
			animation.play("Run")
	else:
		velocity.x = move_toward(velocity.x, 0, SPEED)
		if velocity.y == 0 and get_node("AnimatedSprite2D").animation != "Death":
			animation.play("Idle")
	if velocity.y > 0:
		animation.play("Fall")

	if Game.playerHP <= 0:
		velocity.y = JUMP_VELOCITY + 200
		move_and_slide()
		
		collision_shape.set_deferred("disabled", true)
		animation.play("Death")
		
		await get_tree().create_timer(1.6).timeout
		
		get_tree().change_scene_to_file("res://main.tscn")
		
		#queue_free()
		#get_tree().change_scene_to_file("res://main.tscn")

	move_and_slide()
