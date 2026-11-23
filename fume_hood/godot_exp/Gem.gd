extends Area2D



func _on_body_entered(body):
	if body.name == "Player":
		Game.won = true
		
		var position_tween = get_tree().create_tween()
		var modulate_tween = get_tree().create_tween()
		position_tween.tween_property(self, "position", position - Vector2(0, 35), 0.35)
		modulate_tween.tween_property(self, "modulate:a", 0, 0.3)
		
		position_tween.tween_callback(queue_free)
