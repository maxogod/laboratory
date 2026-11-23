extends Label

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta):
	if Game.won:
		self.visible = true
	else:
		self.visible = false
