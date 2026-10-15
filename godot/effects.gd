extends Node
var enabled := true
var ducked := false
var step_time := 0.0
var step_variant := 0
var player:AudioStreamPlayer
var loop:AudioStreamPlayer
func _ready():
 player = AudioStreamPlayer.new()
 loop = AudioStreamPlayer.new()
 player.volume_db = -18
 loop.volume_db = -23
 add_child(player)
 add_child(loop)
func play(id:String):
 if not enabled or ducked:
  return
 var file = "res://media/"+id+".wav"
 if ResourceLoader.exists(file):
  player.stream = load(file)
  player.play()
func shower(start:bool):
 loop.stop()
 if start and enabled and not ducked:
  var water:AudioStreamWAV = load("res://media/shower.wav").duplicate()
  water.loop_mode = AudioStreamWAV.LOOP_FORWARD
  water.loop_end = water.data.size()/2
  loop.stream = water
  loop.play()
func stop():
 if player.playing:
  player.stop()
 if loop.playing:
  loop.stop()
func tick(dt:float,walking:bool):
 if not enabled or ducked:
  stop()
  return
 step_time += dt
 if walking and step_time>0.5:
  step_time = 0
  step_variant = 1-step_variant
  play("step"+str(step_variant+1))
