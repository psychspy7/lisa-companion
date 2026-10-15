extends RefCounted
# Local, interruptible room schedule. Never starts microphone or PC tools.
var elapsed := 0.0
var last_interaction := 0.0
var next_activity := 120.0
var last_kiss := -10000.0
var index := 0
var routines := true
var affection := false
func touched():
 last_interaction = elapsed
 next_activity = elapsed+120.0
func tick(dt:float,available:bool,mood:String,sleeping:bool=false,hour:int=-1)->String:
 elapsed += dt
 if not routines or not available or elapsed-last_interaction<90 or elapsed<next_activity:
  return ""
 next_activity = elapsed+150.0
 if hour<0:
  hour = Time.get_datetime_dict_from_system().hour
 if sleeping:
  return "wake" if hour>=6 and hour<23 else ""
 if affection and elapsed-last_kiss>900 and not mood in ["sad","crying","caring","angry"]:
  last_kiss = elapsed
  return "kiss"
 var activities:Array
 if hour>=6 and hour<12:
  activities = ["tea","stretch","wash_hands","exercise","drink_water"]
 elif hour>=12 and hour<18:
  activities = ["read","balcony","drink_water","sofa"]
 elif hour>=18 and hour<23:
  activities = ["tea","phone","sofa","hair_touch"]
 else:
  activities = ["sleep"]
 var action:String = activities[index%activities.size()]
 index += 1
 return action
