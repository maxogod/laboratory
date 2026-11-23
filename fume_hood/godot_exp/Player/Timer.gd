extends Timer

func _process(delta):
	if get_node("../AnimatedSprite2D").animation == "Death":
		self.start(1.0)
		print("aaa")
		await self.timeout
		print("bbb")
		get_tree().change_scene_to_file("res://main.tscn")
