extends Camera3D
var actor: Node3D
var following := true
var enabled := false
var manual_until := 0.0
var orbit := 0.0
var elevation := 0.0
var zoom := 2.95
var target := Vector3.ZERO
var manual_drag := false
var views := {}
var area := "room"
func _ready():
 current = true
 near = 0.08
 far = 40
 fov = 48
 global_position = Vector3(0.0,1.75,3.9)
 target = Vector3(0,1.0,0.25)
 look_at(target)
func _unhandled_input(event):
 if not enabled:
  return
 if event is InputEventMouseButton:
  if event.button_index == MOUSE_BUTTON_RIGHT:
   manual_drag = event.pressed
   manual_until = Time.get_ticks_msec()/1000.0 + 2
  if event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN]:
   zoom = clampf(zoom + (-0.25 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 0.25),2.2,5.5)
 if event is InputEventMouseMotion and manual_drag:
  orbit -= event.relative.x * 0.006
  elevation = clampf(elevation + event.relative.y * 0.002,-0.30,0.4)
  manual_until = Time.get_ticks_msec()/1000.0 + 2
func _process(dt):
 if not enabled or actor == null:
  return
 # Dragging pauses the director briefly; it never changes the user's Follow choice.
 var pausing = manual_drag or Time.get_ticks_msec()/1000.0 < manual_until
 if not following and not pausing:
  return
 var focus = actor.global_position + Vector3(0,1.0,0)
 var desired = actor.global_position + Vector3(sin(orbit)*zoom,1.70+elevation,cos(orbit)*zoom)
 if area != "room" and views.has(area) and not actor.walking and not pausing:
  var view = views[area]
  desired = Vector3(view.pos[0],view.pos[1],view.pos[2])
  focus = actor.global_position + Vector3(0,0.75 if actor.state in ["tea","seated","sleeping"] else 1.05,0)
 if not actor.walking and not pausing:
  if area=="balcony":
   desired = Vector3(5.3,1.65,-0.38)
  elif area=="sofa":
   desired = Vector3(3.0,1.45,3.30)
  elif area=="bed":
   desired = Vector3(1.20,1.50,-0.65)
 # Keep the lens within the actual shell. Balcony gets its own safe close-up.
 desired.x = clampf(desired.x,-5.55,8.1 if area=="balcony" else 5.55)
 desired.z = clampf(desired.z,-4.10,4.1)
 if actor.walking and actor.global_position.x > 5.5:
  desired = Vector3(6.85,1.75,0.20)
  focus = actor.global_position + Vector3(0,0.9,0)
 var alpha = 1.0-exp(-3.2*dt)
 global_position = global_position.lerp(desired,alpha)
 target = target.lerp(focus,alpha)
 if global_position.distance_to(target)>0.1:
  look_at(target)
