extends Node2D

func _on_quit_pressed():
	get_tree().quit()


func _on_play_pressed():
	Game.playerHP = 10
	Game.cherries = 0
	get_tree().change_scene_to_file("res://world.tscn")


func _on_load_pressed():
	Utils.loadGame()
	get_tree().change_scene_to_file("res://world.tscn")
