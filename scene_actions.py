"""Closed character action vocabulary. It never carries executable code or paths."""
import re
SCENE_ACTIONS=("room","sofa","tea","sleep","wake","toilet","bathroom","wash_hands","balcony","wardrobe","wave","command","listen","kiss","angry","sad","smile","sandals_off","sandals_on","exercise","stretch","wipe_sweat","drink_water","whip","put_whip_back","brush_teeth","phone","read","hair_touch","hair_tuck","wind","sleeves_off","sleeves_on","skirt_change","covered_bath","dry_hair","smoke","lights_on","lights_off","stop")
def scene_intent(text):
 t=re.sub(r"\s+"," ",str(text).casefold()).strip()
 patterns=[
 ("stop",r"\b(stop|ruko|cancel)\b"),
 ("lights_off",r"(light|batti).*\b(off|band)\b"),("lights_on",r"(light|batti).*\b(on|chalu)\b"),
 ("sandals_off",r"(take off|remove|utaro).*sandal|sandal.*(off|remove|utaro)"),
 ("sandals_on",r"(wear|put on|pehno).*sandal|sandal.*\bon\b"),
 ("put_whip_back",r"(return|put back).*whip|whip.*(back|away)"),
 ("whip",r"\bwhip\b"),("wipe_sweat",r"(wipe|dry).*(sweat|forehead)"),
 ("exercise",r"\b(exercise|workout|squat)\b"),("stretch",r"\bstretch\b"),
 ("drink_water",r"\b(drink water|pani piyo)\b"),("brush_teeth",r"brush.*teeth"),
 ("wash_hands",r"wash.*hands|\bbasin\b"),("covered_bath",r"\b(shower|take a bath)\b"),
 ("dry_hair",r"dry.*hair"),("hair_tuck",r"tuck.*hair"),("hair_touch",r"(touch|fix).*hair"),
 ("sleeves_off",r"remove.*sleeve"),("sleeves_on",r"(wear|put on).*sleeve"),
 ("skirt_change",r"(change|wear|put on).*skirt"),
 ("phone",r"\b(use phone|check phone)\b"),("read",r"\b(read a book|read book)\b"),
 ("wind",r"\b(wind|breeze)\b"),("smoke",r"\bsmok(e|ing)\b"),
 ("wake",r"\b(wake|utho|jago)\b"),("sleep",r"\b(sleep|bed|soja|sona|so ja)\b"),
 ("toilet",r"\btoilet\b"),("bathroom",r"\b(bathroom|washroom)\b"),("wardrobe",r"\b(wardrobe|closet|almari)\b"),
 ("balcony",r"\b(balcony|outside|bahar)\b"),("tea",r"\b(tea|chai)\b"),
 ("kiss",r"\b(kiss|flying kiss)\b"),("sofa",r"\b(sofa|couch|sit|baitho)\b"),("wave",r"\bwave\b"),
 ("room",r"\b(come back|come here|stand up|idhar)\b")]
 # Conditional suggestions belong to the companion's structured decision.
 if re.search(r"if (you want|you like)|agar.*chaho",t):return None
 # Direct room commands are handled locally; ordinary conversation goes to chat.
 command=re.sub(r"^(?:(?:hey|okay|ok|lisa|sir|please|buddy)[ ,]+)+","",t)
 direct=re.match(r"^(?:go|walk|come|sit|stand|turn|sleep|wake|take|have|drink|wear|remove|put|return|wash|brush|read|use|check|touch|fix|wipe|dry|change|exercise|stretch|wave|whip|kiss|lights?|sandals?|utho|jago|baitho|soja|sona|idhar|pani)\b",command)
 request=re.match(r"^(?:can you|could you|will you|would you|i want you to|let us|let's|lets)\b",command)
 exact=command in {"tea","sofa","bed","balcony","bathroom","wardrobe","toilet"}
 if not (direct or request or exact):return None
 for name,pattern in patterns:
  if re.search(pattern,t):return name
 return None
def validate_scene_action(value):
 if value not in SCENE_ACTIONS:raise ValueError("Unsupported character action")
 return value
