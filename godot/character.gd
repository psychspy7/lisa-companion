extends Node3D
# Illustrated actor with anchored deformation; not a deformable 3D likeness.
var sprite:MeshInstance3D
var material:ShaderMaterial
var poses:Dictionary
var textures := {}
var clock := 0.0
var blend_clock := 1.0
var current_pose := ""
var facing := 0.0
var sandals := true
var sleeves := true
var motion := true
var speaking := 0.0
var talking := false
var outfit := 0
var voice_smoothed := 0.0
var gesture_level := 0.0
var expression := "idle"
var state := "standing"
var walking := false
var target_size := Vector2(1,1.8)
var target_center := 0.925
var camera:Camera3D
var pose_map := {"wave":"wave","command":"command","angry":"angry","sad":"sad","kiss":"kiss","exercise":"squat","stretch":"stretch","wipe_sweat":"sweat","drink_water":"water","sandals_off":"ankle","sandals_on":"ankle","wash_hands":"wash","brush_teeth":"brush","read":"book","phone":"phone","hair_touch":"hair","hair_tuck":"hair","dry_hair":"dryhair","wind":"hair","ankle":"ankle"}
func _ready():
 poses = JSON.parse_string(FileAccess.get_file_as_string("res://assets/poses.json"))
 for pose in poses.values():
  if not textures.has(pose.sheet):
   textures[pose.sheet] = load("res://assets/"+pose.sheet+".png")
 sprite = MeshInstance3D.new()
 var plane = PlaneMesh.new()
 plane.orientation = PlaneMesh.FACE_Z
 plane.subdivide_width = 24
 plane.subdivide_depth = 36
 sprite.mesh = plane
 sprite.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 material = ShaderMaterial.new()
 material.shader = preload("res://illustrated.gdshader")
 sprite.material_override = material
 add_child(sprite)
 set_pose("front")
func rect_for(p:Dictionary)->Vector4:
 var dimensions:Vector2 = textures[p.sheet].get_size()
 var rect:Array = p.rect
 return Vector4(rect[0]/dimensions.x,rect[1]/dimensions.y,rect[2]/dimensions.x,rect[3]/dimensions.y)
func set_pose(id:String):
 if not poses.has(id):
  id = "front"
 if current_pose==id:
  return
 var initial = current_pose.is_empty()
 var old = poses.get(current_pose,poses[id])
 var p:Dictionary = poses[id]
 current_pose = id
 var rect:Array = p.rect
 var height = float(p.get("height",1.8))
 target_size = Vector2(height*float(rect[2])/float(rect[3]),height)
 target_center = float(p.get("center",height*0.5))+0.025
 material.shader = preload("res://illustrated_seated.gdshader") if id in ["seated","seated_bare","tea","sleep","book","phone","ankle"] else preload("res://illustrated.gdshader")
 material.set_shader_parameter("previous_artwork",textures[old.sheet])
 material.set_shader_parameter("previous_rect",rect_for(old))
 material.set_shader_parameter("artwork",textures[p.sheet])
 material.set_shader_parameter("frame_rect",rect_for(p))
 var top:Array = p.get("top_region",[0.12,0.19,0.76,0.30])
 material.set_shader_parameter("top_region",Vector4(top[0],top[1],top[2],top[3]))
 material.set_shader_parameter("face_enabled",id=="front")
 blend_clock = 1.0 if initial else 0.0
 if initial:
  sprite.mesh.size = target_size
  sprite.position.y = target_center
func _process(dt):
 clock += dt
 var pose = "front"
 var mirror = false
 if walking:
  pose = "walk"+str(int(clock*6.0)%4)
  if camera:
   mirror = Vector3(sin(facing),0,cos(facing)).dot(camera.global_transform.basis.x)<0
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
 if talking and not walking and state=="standing":
  pose = "front"
  mirror = false
 set_pose(pose)
 blend_clock = minf(1.0,blend_clock+dt*9.0)
 material.set_shader_parameter("pose_mix",smoothstep(0,1,blend_clock))
 material.set_shader_parameter("mirror",mirror)
 sprite.mesh.size = sprite.mesh.size.lerp(target_size,minf(dt*12,1))
 var center = target_center+(sin(clock*12.0)*0.009 if walking and motion else 0.0)
 sprite.position.y = lerpf(sprite.position.y,center,minf(dt*12,1))
 var breath = sin(clock*1.9)*0.0025 if motion else 0.0
 sprite.scale = Vector3(1,1+breath,1)
 if camera:
  var direction = camera.global_position-global_position
  sprite.rotation.y = atan2(direction.x,direction.z)
 var blink_phase = fmod(clock,4.35)
 var blink_value = sin((blink_phase-4.05)/0.25*PI) if blink_phase>4.05 and blink_phase<4.30 else 0.0
 var voice_target = maxf(speaking*3.0,0.12+0.09*sin(clock*12) if talking else 0.0)
 voice_smoothed = lerpf(voice_smoothed,clampf(voice_target,0,1),minf(dt*14,1))
 gesture_level = lerpf(gesture_level,0.9 if talking else 0.16 if state in ["standing","wave","command"] else 0.0,minf(dt*5,1))
 material.set_shader_parameter("blink",blink_value if motion else 0.0)
 material.set_shader_parameter("voice",voice_smoothed)
 material.set_shader_parameter("gesture",gesture_level)
 material.set_shader_parameter("motion_amount",1.0 if motion else 0.0)
 material.set_shader_parameter("exercise",1.0 if state=="exercise" else 0.0)
 material.set_shader_parameter("outfit",float(outfit))
func status():
 return {"pose":current_pose,"state":state,"walking":walking,"sandals":sandals,"sleeves":sleeves,"outfit":outfit,"gesture":gesture_level,"rough_model_visible":false}
