extends Node3D
# Native illustrated 2.5D actor. Every visible pose is Lisa's painted artwork.
var sprite: MeshInstance3D
var material:ShaderMaterial
var poses:Dictionary
var textures := {}
var clock := 0.0
var current_pose := ""
var facing := 0.0
var sandals := true
var sleeves := true
var motion := true
var speaking := 0.0
var expression := "idle"
var state := "standing"
var walking := false
var camera:Camera3D
var pose_map := {"wave":"wave","command":"command","angry":"angry","sad":"sad","kiss":"kiss","exercise":"squat","stretch":"stretch","wipe_sweat":"sweat","drink_water":"water","whip":"whip","sandals_off":"ankle","sandals_on":"ankle","wash_hands":"wash","brush_teeth":"brush","read":"book","phone":"phone","hair_touch":"hair","hair_tuck":"hair","dry_hair":"dryhair","covered_bath":"dryhair","wind":"hair","ankle":"ankle"}
func _ready():
 poses = JSON.parse_string(FileAccess.get_file_as_string("res://assets/poses.json"))
 for pose in poses.values():
  if not textures.has(pose.sheet):
   textures[pose.sheet] = load("res://assets/"+pose.sheet+".png")
 sprite = MeshInstance3D.new()
 sprite.mesh = QuadMesh.new()
 sprite.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 material = ShaderMaterial.new()
 material.shader = preload("res://illustrated.gdshader")
 sprite.material_override = material
 add_child(sprite)
 set_pose("front")
func set_pose(id:String):
 if not poses.has(id):
  id = "front"
 if current_pose==id:
  return
 current_pose = id
 var p = poses[id]
 var texture:Texture2D = textures[p.sheet]
 var dimensions = texture.get_size()
 var rect = p.rect
 var height = float(p.get("height",1.8))
 sprite.mesh.size = Vector2(height*float(rect[2])/float(rect[3]),height)
 sprite.position.y = float(p.get("center",height*0.5))+0.025
 material.shader = preload("res://illustrated_seated.gdshader") if id in ["seated","seated_bare","tea","sleep","book","phone","ankle"] else preload("res://illustrated.gdshader")
 material.set_shader_parameter("artwork",texture)
 material.set_shader_parameter("frame_rect",Vector4(rect[0]/dimensions.x,rect[1]/dimensions.y,rect[2]/dimensions.x,rect[3]/dimensions.y))
 material.set_shader_parameter("face_enabled",id=="front")
func _process(dt):
 clock += dt
 var pose = "front"
 var mirror = false
 if walking:
  pose = "walk"+str(int(clock*6.0)%4)
  if camera:
   var right = camera.global_transform.basis.x
   mirror = Vector3(sin(facing),0,cos(facing)).dot(right)<0
 elif state=="sleeping":
  pose = "sleep"
 elif state=="seated":
  pose = "seated" if sandals else "seated_bare"
 elif state=="tea":
  pose = "tea"
 elif pose_map.has(state):
  pose = pose_map[state]
 elif sandals and sleeves:
  if camera:
   var direction = camera.global_position-global_position
   var angle = wrapf(atan2(direction.x,direction.z)-facing,-PI,PI)
   var a = abs(angle)
   pose = "front" if a<0.45 else "quarter" if a<1.20 else "profile" if a<2.25 else "back"
   mirror = angle<0
  if expression in ["angry","sad","kiss","command","wave"]:
   pose = expression
 else:
  pose = "bare" if sleeves else "sleeveless" if sandals else "sleeveless_bare"
 set_pose(pose)
 material.set_shader_parameter("mirror",mirror)
 var breath = sin(clock*1.9)*0.0025 if motion else 0.0
 sprite.scale = Vector3(1,1+breath,1)
 if camera:
  var direction = camera.global_position-global_position
  sprite.rotation.y = atan2(direction.x,direction.z)
 if walking:
  sprite.position.y = float(poses[pose].get("center",0.9))+0.025+sin(clock*12.0)*0.009
 var blink_phase = fmod(clock,4.35)
 var blink_value = sin((blink_phase-4.05)/0.25*PI) if blink_phase>4.05 and blink_phase<4.30 else 0.0
 material.set_shader_parameter("blink",blink_value if motion else 0.0)
 material.set_shader_parameter("voice",clampf(speaking*3.0,0,1))
func status():
 return {"pose":current_pose,"state":state,"walking":walking,"sandals":sandals,"sleeves":sleeves,"rough_model_visible":false}
