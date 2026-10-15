extends Node3D
const Bridge = preload("res://bridge.gd")
const Character = preload("res://character.gd")
const Director = preload("res://camera_director.gd")
const Routes = preload("res://room_routes.gd")
const Life = preload("res://life.gd")
const Effects = preload("res://effects.gd")
var bridge
var actor
var camera
var room:Node3D
var lighting:Node3D
var canvas:CanvasLayer
var menu:PanelContainer
var footer_root:VBoxContainer
var footer_width := -1.0
var reply:Label
var status:Label
var input:LineEdit
var mic:Button
var follow:CheckButton
var intro:Control
var intro_art:VideoStreamPlayer
var life = Life.new()
var effects
var routine_toggle:CheckButton
var affection_toggle:CheckButton
var effects_toggle:CheckButton
var privacy:PanelContainer
var outfit_button:Button
var intro_title:Label
var intro_credit:Label
var enter:Button
var load_note:Label
var progress:ProgressBar
var loaded := false
var entered := false
var intro_time := 0.0
var skipped := false
var lights_on := true
var generation := 0
var path := []
var after_walk := ""
var walk_area := "room"
var area := "room"
var destination := "room"
var phase := "idle"
var busy := false
var route_serial := 0
var tween:Tween
var frame_times := []
var fps_samples := []
var test_mode := false
var test_started := false
var last_mood := ""
var test_results := []
var closing := false
var balcony_door:Node3D
var bathroom_door:Node3D
func _ready():
 test_mode = OS.get_environment("LISA_ENGINE_TEST") == "1" or OS.get_cmdline_user_args().has("--self-test")
 if not test_mode:
  DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
 DisplayServer.window_set_title("LISA · Kitty Corp")
 get_tree().auto_accept_quit = false
 Engine.max_fps = 60
 canvas = CanvasLayer.new()
 add_child(canvas)
 effects = Effects.new()
 add_child(effects)
 setup_theme()
 build_interface()
 build_intro()
 bridge = Bridge.new()
 add_child(bridge)
 bridge.state_changed.connect(snapshot)
 bridge.action_received.connect(command)
 camera = Director.new()
 add_child(camera)
 actor = Character.new()
 add_child(actor)
 actor.position = Routes.NODES.room
 actor.camera = camera
 camera.actor = actor
 ResourceLoader.load_threaded_request("res://room-edit.tscn")
func setup_theme():
 var theme = Theme.new()
 theme.default_font_size = 16
 var normal = StyleBoxFlat.new()
 normal.bg_color = Color(0.065,0.051,0.075,0.69)
 normal.border_color = Color(0.85,0.74,0.63,0.22)
 normal.set_border_width_all(1)
 normal.set_corner_radius_all(14)
 normal.content_margin_left = 16
 normal.content_margin_right = 16
 normal.content_margin_top = 12
 normal.content_margin_bottom = 12
 theme.set_stylebox("panel","PanelContainer",normal)
 for kind in ["normal","hover","pressed","focus"]:
  var button = normal.duplicate()
  button.bg_color = Color(0.23,0.11,0.16,0.7) if kind=="hover" else Color(0.12,0.08,0.10,0.5) if kind=="pressed" else Color(0,0,0,0)
  button.set_corner_radius_all(10)
  button.content_margin_top = 8
  button.content_margin_bottom = 8
  theme.set_stylebox(kind,"Button",button)
 theme.set_color("font_color","Label",Color(0.95,0.90,0.83))
 theme.set_color("font_color","Button",Color(0.95,0.90,0.83))
 theme.set_color("font_color","LineEdit",Color(0.95,0.90,0.83))
 theme.set_stylebox("normal","LineEdit",normal.duplicate())
 var root = Control.new()
 root.name = "UI"
 root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 root.theme = theme
 root.mouse_filter = Control.MOUSE_FILTER_IGNORE
 canvas.add_child(root)
func button(text:String,callback,parent:Node):
 var b = Button.new()
 b.text = text
 b.pressed.connect(callback)
 parent.add_child(b)
 return b
func build_interface():
 var ui = canvas.get_node("UI")
 var top = HBoxContainer.new()
 top.position = Vector2(24,22)
 ui.add_child(top)
 button("☰",func(): menu.visible = not menu.visible,top)
 var name = Label.new()
 name.text = "  L I S A"
 name.add_theme_font_size_override("font_size",18)
 top.add_child(name)
 menu = PanelContainer.new()
 menu.position = Vector2(24,80)
 menu.custom_minimum_size = Vector2(290,0)
 menu.visible = false
 ui.add_child(menu)
 var list = VBoxContainer.new()
 list.add_theme_constant_override("separation",6)
 menu.add_child(list)
 var title = Label.new()
 title.text = "Your space"
 title.add_theme_font_size_override("font_size",20)
 list.add_child(title)
 follow = CheckButton.new()
 follow.text = "Follow Lisa"
 follow.button_pressed = true
 list.add_child(follow)
 follow.toggled.connect(func(value): camera.following = value; bridge.send("follow",value))
 button("Room lights",func(): set_lights(not lights_on),list)
 button("Chat & voice settings",func(): bridge.send("settings"),list)

 button("Saved memories",func(): bridge.send("memory"),list)
 button("Check for an update",func(): bridge.send("update"),list)
 button("Add desktop shortcut",func(): bridge.send("shortcut"),list)
 button("Fullscreen / window",toggle_fullscreen,list)
 routine_toggle = CheckButton.new()
 routine_toggle.text = "Daily routines"
 list.add_child(routine_toggle)
 routine_toggle.toggled.connect(func(value):bridge.send("routines",value))
 affection_toggle = CheckButton.new()
 affection_toggle.text = "Occasional affectionate gestures"
 list.add_child(affection_toggle)
 affection_toggle.toggled.connect(func(value):bridge.send("affection",value))
 effects_toggle = CheckButton.new()
 effects_toggle.text = "Room sound effects"
 list.add_child(effects_toggle)
 effects_toggle.toggled.connect(func(value):bridge.send("effects",value))
 outfit_button = button("Outfit · Midnight",func():bridge.send("outfit",1-actor.outfit),list)
 button("Buy Lisa · Kitty Corp",func():bridge.send("buy"),list)
 button("Licenses",show_licenses,list)
 button("Quit Lisa",quit_app,list)
 var footer = VBoxContainer.new()
 footer_root = footer
 footer.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
 footer.position = Vector2(-360,-190)
 footer.custom_minimum_size = Vector2(720,0)
 footer.add_theme_constant_override("separation",12)
 ui.add_child(footer)
 reply = Label.new()
 reply.text = "Hey, Sir. Make yourself comfortable."
 reply.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
 reply.custom_minimum_size = Vector2(720,56)
 reply.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
 reply.add_theme_font_size_override("font_size",18)
 reply.add_theme_color_override("font_shadow_color",Color(0,0,0,0.85))
 reply.add_theme_constant_override("shadow_outline_size",5)
 footer.add_child(reply)
 var panel = PanelContainer.new()
 panel.custom_minimum_size = Vector2(720,64)
 footer.add_child(panel)
 var row = HBoxContainer.new()
 row.add_theme_constant_override("separation",12)
 var glass = ColorRect.new()
 glass.mouse_filter = Control.MOUSE_FILTER_IGNORE
 var frost = ShaderMaterial.new()
 frost.shader = preload("res://glass.gdshader")
 glass.material = frost
 panel.add_child(glass)
 panel.add_child(row)
 mic = button("Talk",func(): bridge.send("voice"),row)
 input = LineEdit.new()
 input.placeholder_text = "Talk to Lisa…"
 input.max_length = 4000
 input.size_flags_horizontal = Control.SIZE_EXPAND_FILL
 row.add_child(input)
 input.text_submitted.connect(send_message)
 button("Send",func(): send_message(input.text),row)
 button("Interrupt",func(): bridge.send("barge"),row)
 status = Label.new()
 status.text = "LISA 2.2 · Kitty Corp"
 status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
 status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
 status.add_theme_font_size_override("font_size",12)
 status.add_theme_color_override("font_color",Color(0.84,0.80,0.76,0.74))
 footer.add_child(status)
 ui.visible = false
func build_intro():
 intro = Control.new()
 intro.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 intro.mouse_filter = Control.MOUSE_FILTER_STOP
 canvas.add_child(intro)
 var black = ColorRect.new()
 black.color = Color.BLACK
 black.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 intro.add_child(black)
 intro_art = VideoStreamPlayer.new()
 intro_art.stream = load("res://media/kitty-opening.ogv")
 intro_art.expand = true
 intro_art.volume_db = -18
 intro_art.autoplay = true
 intro_art.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 intro_art.modulate.a = 0
 intro.add_child(intro_art)
 var shade = ColorRect.new()
 shade.color = Color(0.015,0,0,0.52)
 shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
 intro.add_child(shade)
 var column = VBoxContainer.new()
 column.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
 column.position = Vector2(-300,-150)
 column.custom_minimum_size = Vector2(600,0)
 column.add_theme_constant_override("separation",24)
 intro.add_child(column)
 intro_credit = Label.new()
 intro_credit.text = "M A D E   B Y\n\nK I T T Y   C O R P"
 intro_credit.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
 intro_credit.add_theme_font_size_override("font_size",24)
 column.add_child(intro_credit)
 intro_title = Label.new()
 intro_title.text = "L I S A"
 intro_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
 intro_title.add_theme_font_size_override("font_size",72)
 intro_title.visible = false
 column.add_child(intro_title)
 load_note = Label.new()
 load_note.text = "Preparing your room…"
 load_note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
 column.add_child(load_note)
 progress = ProgressBar.new()
 progress.show_percentage = false
 progress.custom_minimum_size = Vector2(600,4)
 column.add_child(progress)
 enter = button("Enter Lisa  ↗",enter_room,column)
 enter.disabled = true
 enter.visible = false
 button("Skip cinematic",func(): skipped = true,column)
func send_message(text:String):
 if not entered or busy:
  return
 var message = text.strip_edges()
 if message.is_empty():
  return
 input.clear()
 life.touched()
 bridge.send("send",message)
func snapshot(state:Dictionary):
 reply.text = str(state.get("reply",""))
 busy = bool(state.get("busy",false))
 status.tooltip_text = str(state.get("updateNote","")) if not str(state.get("updateNote","")).is_empty() else str(state.get("status",""))
 status.text = status.tooltip_text.left(220)
 mic.text = "Stop talk" if state.get("conversation",false) else "Talk"
 actor.speaking = float(state.get("speechLevel",0))
 actor.talking = bool(state.get("talking",false))
 actor.outfit = int(state.get("outfit",0))
 life.routines = bool(state.get("routines",true))
 life.affection = bool(state.get("affection",false))
 effects.enabled = bool(state.get("effects",true))
 effects.ducked = actor.talking or bool(state.get("recording",false))
 if routine_toggle.button_pressed!=life.routines:
  routine_toggle.set_pressed_no_signal(life.routines)
 if affection_toggle.button_pressed!=life.affection:
  affection_toggle.set_pressed_no_signal(life.affection)
 if effects_toggle.button_pressed!=effects.enabled:
  effects_toggle.set_pressed_no_signal(effects.enabled)
 var outfit_label = "Outfit · "+("Midnight" if actor.outfit==0 else "Burgundy")
 if outfit_button.text!=outfit_label:
  outfit_button.text = outfit_label
 actor.motion = bool(state.get("motion",true))
 var selected = bool(state.get("follow",true))
 follow.set_pressed_no_signal(selected)
 camera.following = selected
 var mood = str(state.get("mood","smile"))
 if busy or actor.talking or bool(state.get("recording",false)):
  life.touched()
 if mood != last_mood:
  last_mood = mood
  actor.expression = "angry" if mood in ["angry","cold_angry"] else "sad" if mood in ["sad","crying"] else "front"
 if test_mode and loaded and not test_started:
  test_started = true
  run_tests()
func _process(dt):
 if entered:
  effects.tick(dt,actor.walking)
  var activity:String = life.tick(dt,not test_mode and not busy and not effects.ducked and phase=="idle",last_mood,actor.state=="sleeping")
  if not activity.is_empty():
   command(activity,false)
 if footer_root:
  var minimum = footer_root.get_combined_minimum_size()
  var width = minf(720,get_viewport().get_visible_rect().size.x-40)
  if width!=footer_width:
   footer_width = width
   footer_root.custom_minimum_size.x = width
   reply.custom_minimum_size.x = width
  var new_size = Vector2(width,minimum.y)
  var new_position = Vector2((get_viewport().get_visible_rect().size.x-width)/2,get_viewport().get_visible_rect().size.y-minimum.y-24)
  if footer_root.size!=new_size:
   footer_root.size = new_size
  if footer_root.position!=new_position:
   footer_root.position = new_position
 frame_times.append(dt*1000)
 if frame_times.size()>3600:
  frame_times.pop_front()
 if not loaded:
  var loading = []
  var state = ResourceLoader.load_threaded_get_status("res://room-edit.tscn",loading)
  progress.value = float(loading[0])*100 if not loading.is_empty() else 0
  if state == ResourceLoader.THREAD_LOAD_LOADED:
   room = ResourceLoader.load_threaded_get("res://room-edit.tscn").instantiate()
   add_child(room)
   setup_room()
   loaded = true
   progress.value = 100
   bridge.send("ready")
  elif state == ResourceLoader.THREAD_LOAD_FAILED:
   load_note.text = "Room could not load. Reinstall Lisa to restore its files."
 intro_time += dt
 if not entered:
  intro_art.modulate.a = clampf((intro_time-1.2)/2.0,0,1)
  if (intro_time>10.8 or skipped) and loaded:
   intro_credit.visible = false
   intro_title.visible = true
   load_note.text = "Your world can wait. She's been waiting for you."
   progress.visible = false
   enter.visible = true
   enter.disabled = false
 if not path.is_empty():
  move_actor(minf(dt,0.05))
func setup_room():
 var layout = JSON.parse_string(FileAccess.get_file_as_string("res://assets/room-layout.json"))
 camera.views = layout.views
 balcony_door = room.find_child("BalconyDoor",true,false)
 bathroom_door = room.find_child("BathroomDoor",true,false)
 lighting = Node3D.new()
 add_child(lighting)
 var environment = WorldEnvironment.new()
 var config = Environment.new()
 config.background_mode = Environment.BG_COLOR
 config.background_color = Color(0.04,0.045,0.065)
 config.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
 config.ambient_light_color = Color(0.80,0.73,0.69)
 config.ambient_light_energy = 0.55
 config.tonemap_mode = Environment.TONE_MAPPER_FILMIC
 config.tonemap_exposure = 1.10
 environment.environment = config
 add_child(environment)
 for fixture in layout.fixtures:
  var light = OmniLight3D.new()
  light.position = Vector3(fixture.position[0],fixture.position[1]-0.35,fixture.position[2])
  light.light_color = Color(fixture.color)
  light.light_energy = 1.6 if fixture.id=="main-ceiling" else 0.8
  light.omni_range = 7.0 if fixture.id=="main-ceiling" else 4.0
  light.shadow_enabled = false
  lighting.add_child(light)
 var sun = DirectionalLight3D.new()
 sun.rotation_degrees = Vector3(-42,-35,0)
 sun.light_color = Color(0.68,0.74,0.85)
 sun.light_energy = 0.30
 sun.shadow_enabled = true
 sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
 sun.directional_shadow_max_distance = 18
 lighting.add_child(sun)
 # One shadow pass. Intro decoder is stopped after entry.
func open_doors(next:String):
 var doors = create_tween().set_parallel(true)
 if balcony_door:
  doors.tween_property(balcony_door,"rotation:y",PI/2 if next=="balcony" or actor.position.x>5.5 else 0.0,0.85).set_trans(Tween.TRANS_SINE)
 if bathroom_door:
  doors.tween_property(bathroom_door,"rotation:y",-PI/2 if next in ["bathroom","toilet","shower"] or actor.position.z < -1.7 and actor.position.x > -2.8 and actor.position.x < -0.5 else 0.0,0.85).set_trans(Tween.TRANS_SINE)
func enter_room():
 if not loaded or entered:
  return
 entered = true
 intro_art.stop()
 effects.play("enter")
 bridge.send("enter")
 camera.enabled = true
 canvas.get_node("UI").visible = true
 var fade = create_tween()
 fade.tween_property(intro,"modulate:a",0.0,0.7)
 fade.tween_callback(func():intro.visible=false)
func set_lights(value:bool):
 lights_on = value
 if lighting:
  var fade = create_tween().set_parallel(true)
  for light in lighting.get_children():
   if light is Light3D:
    fade.tween_property(light,"light_energy",0.12 if not value else 0.30 if light is DirectionalLight3D else 1.6 if light.omni_range>5 else 0.8,0.8)
func command(action:String,user_requested:bool=true):
 if not entered:
  return
 if user_requested:
  life.touched()
 generation += 1
 actor.visible = true
 effects.shower(false)
 if privacy:
  privacy.visible = false
 var was_walking = actor.walking
 if tween:
  tween.kill()
 path.clear()
 actor.walking = false
 phase = "action"
 var move_actions = {"room":"room","sofa":"sofa","tea":"sofa","sleep":"bed","bathroom":"bathroom","toilet":"toilet","wardrobe":"wardrobe","balcony":"balcony","wash_hands":"washbasin","brush_teeth":"washbasin","covered_bath":"shower","exercise":"room","read":"sofa","phone":"sofa","sandals_off":"sofa","sandals_on":"sofa","sleeves_off":"wardrobe","sleeves_on":"wardrobe","skirt_change":"wardrobe"}
 if action == "lights_on" or action == "lights_off":
  set_lights(action=="lights_on")
  phase = "idle"
  return
 if action == "stop":
  if was_walking:
   actor.state = "standing"
  phase = "idle"
  return
 if action == "wake":
  set_lights(true)
  await leave_seat()
  phase = "idle"
  return
 if move_actions.has(action):
  var requested_generation = generation
  await leave_seat()
  if requested_generation != generation:
   return
  after_walk = action
  destination = move_actions[action]
  area = destination
  camera.area = "bathroom" if destination in ["shower","toilet","washbasin"] else destination
  open_doors(destination)
  path = Routes.route(actor.position,destination)
  actor.walking = not path.is_empty()
  actor.state = "standing"
  phase = "walking"
  if path.is_empty():
   arrived()
 else:
  var gesture_generation = generation
  await leave_seat()
  if gesture_generation != generation:
   return
  actor.state = action
  if action=="kiss":
   effects.play("kiss")
  var id = generation
  await get_tree().create_timer(3.0).timeout
  if id == generation:
   actor.state = "standing"
   phase = "idle"
func leave_seat():
 if actor.state in ["seated","tea","sleeping","read","phone","ankle"]:
  var target:Vector3 = Routes.NODES.get(destination,Routes.NODES.room)
  if actor.position.distance_to(target)<2.4:
   tween = create_tween()
   tween.tween_property(actor,"position",target,0.9).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
   await tween.finished
 actor.state = "standing"
func move_actor(dt:float):
 var point:Vector3 = path[0]
 var direction = point-actor.position
 var distance = direction.length()
 var speed = 0.9 * dt * (3.0 if test_mode else 1.0)
 if distance<=speed:
  actor.position = point
  path.pop_front()
  if path.is_empty():
   actor.walking = false
   arrived()
 else:
  actor.position += direction.normalized()*speed
  actor.facing = lerp_angle(actor.facing,atan2(direction.x,direction.z),minf(dt*5,1))
func arrived():
 phase = "settling"
 var id = generation
 if after_walk in ["sofa","tea","read","phone"]:
  actor.state = "tea" if after_walk=="tea" else "seated" if after_walk=="sofa" else after_walk
  tween = create_tween()
  tween.tween_property(actor,"position",Vector3(4.1,0,1.35),0.85).set_trans(Tween.TRANS_SINE)
  await tween.finished
 elif after_walk=="sleep":
  actor.state = "sleeping"
  tween = create_tween()
  tween.tween_property(actor,"position",Vector3(2.03,0.73,-2.65),1.2).set_trans(Tween.TRANS_SINE)
  await tween.finished
  if id == generation:
   set_lights(false)
 elif after_walk in ["sandals_off","sandals_on"]:
  actor.state = "ankle"
  await get_tree().create_timer(2.5).timeout
  if id == generation:
   actor.sandals = after_walk=="sandals_on"
   actor.state = "seated"
 elif after_walk in ["sleeves_off","sleeves_on"]:
  actor.sleeves = after_walk=="sleeves_on"
  actor.state = "standing"
 elif after_walk=="skirt_change":
  actor.state = "standing"
  bridge.send("outfit",1-actor.outfit)
  effects.play("cloth")
 elif after_walk in ["toilet","bathroom","covered_bath"]:
  await private_activity(after_walk,id)
  return
 else:
  actor.state = after_walk if actor.pose_map.has(after_walk) else "standing"
  if after_walk=="exercise":
   await get_tree().create_timer(8.0 if not test_mode else 1.0).timeout
   if id==generation:
    actor.state = "wipe_sweat"
  if after_walk=="balcony":
   actor.facing = PI/2
  elif after_walk in ["wardrobe","bathroom","wash_hands","brush_teeth"]:
   actor.facing = PI
 if id == generation:
  phase = "idle"
func private_activity(action:String,id:int):
 phase = "private"
 actor.visible = false
 camera.area = "room"
 if not privacy:
  privacy = PanelContainer.new()
  privacy.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
  privacy.position = Vector2(-240,-70)
  privacy.custom_minimum_size = Vector2(480,100)
  privacy.mouse_filter = Control.MOUSE_FILTER_IGNORE
  var note = Label.new()
  note.name = "Note"
  note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
  note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
  privacy.add_child(note)
  canvas.add_child(privacy)
 privacy.visible = true
 privacy.get_node("Note").text = "A quiet moment…\nLisa will be back shortly."
 var showering = action=="covered_bath"
 effects.shower(showering)
 await get_tree().create_timer(15.0 if showering else 10.0).timeout
 if id!=generation:
  return
 effects.shower(false)
 if showering:
  bridge.send("outfit",1-actor.outfit)
  effects.play("cloth")
 else:
  effects.play("flush")
 actor.visible = true
 privacy.visible = false
 actor.state = "dry_hair" if showering else "standing"
 # Use the same navigation graph for the return walk; no teleport.
 command("room",false)
func toggle_fullscreen():
 DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED if DisplayServer.window_get_mode()==DisplayServer.WINDOW_MODE_FULLSCREEN else DisplayServer.WINDOW_MODE_FULLSCREEN)
func show_licenses():
 var dialog = AcceptDialog.new()
 dialog.title = "LISA · Open source licenses"
 dialog.dialog_text = "LISA uses Godot Engine (MIT).\n\n" + Engine.get_license_text()
 dialog.min_size = Vector2i(900,600)
 canvas.add_child(dialog)
 dialog.popup_centered()
func _unhandled_key_input(event):
 if event.is_pressed() and event.keycode==KEY_ENTER and not entered:
  enter_room()
 elif event.is_pressed() and event.keycode==KEY_ESCAPE:
  menu.visible = not menu.visible
func _notification(what):
 if what == NOTIFICATION_WM_CLOSE_REQUEST:
  quit_app()
func quit_app():
 if closing:
  return
 closing = true
 bridge.send("interrupt")
 bridge.send("quit")
 await get_tree().create_timer(0.15).timeout
 get_tree().quit()
func run_tests():
 await get_tree().create_timer(3.0).timeout
 get_viewport().get_texture().get_image().save_png(OS.get_environment("LISA_ENGINE_DATA").path_join("opening.png"))
 skipped = true
 await get_tree().create_timer(0.1).timeout
 enter_room()
 await get_tree().create_timer(2.0).timeout
 test_results.append({"check":"startup","passed":loaded and entered})
 follow.set_pressed_no_signal(true)
 camera.following = true
 camera.manual_drag = true
 await get_tree().create_timer(0.1).timeout
 camera.manual_drag = false
 test_results.append({"check":"manual_camera_keeps_follow","passed":camera.following and follow.button_pressed})
 for pose in actor.poses.keys():
  actor.set_pose(pose)
  test_results.append({"check":"pose_"+pose,"passed":actor.current_pose==pose})
 bridge.state_changed.disconnect(snapshot)
 actor.talking = true
 await get_tree().create_timer(0.6).timeout
 test_results.append({"check":"talking_body_gesture","passed":actor.gesture_level>0.5})
 actor.talking = false
 bridge.state_changed.connect(snapshot)
 test_results.append({"check":"supplied_video","passed":intro_art.stream is VideoStreamTheora})
 for dest in Routes.NODES.keys():
  var points = Routes.route(Routes.NODES.room,dest)
  test_results.append({"check":"route_"+dest,"passed":dest=="room" or not points.is_empty()})
 actor.state = "standing"
 actor.position = Routes.NODES.room
 camera.area = "room"
 await get_tree().create_timer(1.0).timeout
 var folder = OS.get_environment("LISA_ENGINE_DATA")
 room.visible = false
 await get_tree().process_frame
 get_viewport().get_texture().get_image().save_png(folder.path_join("character-only.png"))
 room.visible = true
 for scenario in ["tea","sleep","balcony","wash_hands","exercise","kiss","bathroom","covered_bath","room"]:
  var before = actor.position
  command(scenario)
  var captured_squat = false
  var maximum_step = 0.0
  var previous = actor.position
  var previous_time = Time.get_ticks_msec()
  var max_speed = 0.0
  var started_at = Time.get_ticks_msec()
  while (not path.is_empty() or phase!="idle") and Time.get_ticks_msec()-started_at<35000:
   await get_tree().process_frame
   if scenario=="exercise" and actor.state=="exercise" and not captured_squat:
    await get_tree().create_timer(0.2).timeout
    get_viewport().get_texture().get_image().save_png(folder.path_join("exercise-active.png"))
    captured_squat = true
   var step_distance = actor.position.distance_to(previous)
   maximum_step = maxf(maximum_step,step_distance)
   max_speed = maxf(max_speed,step_distance/maxf((Time.get_ticks_msec()-previous_time)/1000.0,0.005))
   previous_time = Time.get_ticks_msec()
   previous = actor.position
  await get_tree().create_timer(0.8).timeout
  test_results.append({"check":"scene_"+scenario,"passed":path.is_empty() and phase=="idle" and not actor.walking and maximum_step<=0.20,"largest_step":maximum_step,"appearance":actor.status()})
  if scenario in ["bathroom","covered_bath"]:
   test_results.append({"check":"private_returns_"+scenario,"passed":actor.visible and actor.position.distance_to(Routes.NODES.room)<0.03 and (Time.get_ticks_msec()-started_at)>=10000})
  get_viewport().get_texture().get_image().save_png(folder.path_join("scene-"+scenario+".png"))
 actor.walking = false
 path.clear()
 actor.state = "standing"
 actor.position = Routes.NODES.room
 camera.area = "room"
 set_lights(true)
 var waking = Life.new()
 waking.elapsed = 200
 waking.next_activity = 0
 test_results.append({"check":"morning_wakes_after_sleep","passed":waking.tick(0,true,"smile",true,8)=="wake"})
 var scheduler = Life.new()
 scheduler.next_activity = 0
 scheduler.elapsed = 200
 test_results.append({"check":"routine_runs_when_idle","passed":not scheduler.tick(0,true,"smile").is_empty()})
 scheduler.touched()
 test_results.append({"check":"routine_respects_user_priority","passed":scheduler.tick(1,true,"smile").is_empty()})
 scheduler.elapsed += 200
 test_results.append({"check":"routine_during_talk_paused","passed":scheduler.tick(1,false,"smile").is_empty()})
 actor.state = "seated"
 command("stop")
 test_results.append({"check":"interrupt_keeps_seated_pose","passed":actor.state=="seated" and phase=="idle"})
 actor.walking = true
 command("stop")
 test_results.append({"check":"interrupt_stops_walking","passed":not actor.walking and actor.state=="standing"})
 follow.set_pressed_no_signal(false)
 camera.following = false
 camera.manual_drag = true
 await get_tree().process_frame
 camera.manual_drag = false
 test_results.append({"check":"manual_camera_keeps_follow_off","passed":not camera.following and not follow.button_pressed})
 follow.set_pressed_no_signal(true)
 camera.following = true
 actor.position = Routes.NODES.room
 camera.area = "room"
 await get_tree().create_timer(1.0).timeout
 get_viewport().get_texture().get_image().save_png(folder.path_join("ui-self-test.png"))
 test_results.append({"check":"exercise_crop_safe","passed":actor.poses.squat.rect[1]>=1735 and float(actor.poses.squat.height)<=1.3})
 test_results.append({"check":"whip_removed","passed":not actor.pose_map.has("whip") and not actor.poses.has("whip")})
 var record = {"testing_note":"Room movement is accelerated 3x for this test. Each walk step is capped at 0.135 m; seat/bed transitions are real tweens.","engine":Engine.get_version_info().string,"renderer":RenderingServer.get_current_rendering_method(),"godot_loaded":true,"tests":test_results,"appearance":actor.status(),"fps":Engine.get_frames_per_second(),"draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),"video_memory_bytes":Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED),"frame_times_ms":frame_times}
 var file = FileAccess.open(folder.path_join("self-test.json"),FileAccess.WRITE)
 file.store_string(JSON.stringify(record,"  "))
 file.flush()
 file.close()
 bridge.send("quit")
 await get_tree().create_timer(0.2).timeout
 get_tree().quit()
