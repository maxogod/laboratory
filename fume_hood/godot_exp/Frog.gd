extends CharacterBody2D

# Get the gravity from the project settings to be synced with RigidBody nodes.
const SPEED = 80
const JUMP_VELOCITY = -300
const JUMP_OFFSET = -4
var gravity = ProjectSettings.get_setting("physics/2d/default_gravity")
var player
var chase = false

func _ready():
	get_node("AnimatedSprite2D").play("Idle")

func _physics_process(delta):
	# Gravity for frog
	velocity.y += gravity * delta
	
	if chase:
		if get_node("AnimatedSprite2D").animation != "Death":
			get_node("AnimatedSprite2D").play("Jump")
			
		player = get_node("../../Player/Player")
		var direction = (player.position - self.position).normalized()
		
		if direction.x > 0:
			get_node("AnimatedSprite2D").flip_h = true
		else:
			get_node("AnimatedSprite2D").flip_h = false
		
		# Movement
		velocity.x = direction.x * SPEED
		if is_on_floor():
			velocity.y = JUMP_VELOCITY
			position.y += JUMP_OFFSET * delta
			
	else:
		if get_node("AnimatedSprite2D").animation != "Death" and get_node("AnimatedSprite2D").animation != "Fall":
			get_node("AnimatedSprite2D").play("Idle")
		velocity.x = 0
	
	if velocity.y > 0 and get_node("AnimatedSprite2D").animation != "Death":
		# Falling
		get_node("AnimatedSprite2D").play("Fall")
	if is_on_floor() and get_node("AnimatedSprite2D").animation != "Death":
		get_node("AnimatedSprite2D").play("Idle")
		
	move_and_slide()

func _on_player_detection_body_entered(body):
	if body.name == "Player":
		chase = true


func _on_player_detection_body_exited(body):
	if body.name == "Player":
		chase = false


func _on_player_death_body_entered(body):
	if body.name == "Player":
		if get_node("AnimatedSprite2D").animation != "Death":
			Game.cherries += 1
			Utils.saveGame()
		chase = false
		get_node("AnimatedSprite2D").play("Death")
		await get_node("AnimatedSprite2D").animation_finished
		queue_free()


func _on_player_collision_body_entered(body):
	if body.name == "Player":
		# body.health -= 3
		Game.playerHP -= 3
