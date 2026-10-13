extends Node
signal state_changed(state: Dictionary)
signal action_received(action: String)
var endpoint := ""
var token := ""
var since := 0
var request: HTTPRequest
var timer := 0.0
var connected := false
var inflight := false
func _ready():
 endpoint = OS.get_environment("LISA_ENGINE_URL")
 token = OS.get_environment("LISA_ENGINE_TOKEN")
 request = HTTPRequest.new()
 request.timeout = 3.0
 add_child(request)
 request.request_completed.connect(_received)
func _process(dt):
 timer += dt
 if timer >= 0.10 and not inflight and not endpoint.is_empty():
  timer = 0
  inflight = true
  var error = request.request(endpoint + "/state?since=" + str(since), PackedStringArray(["Authorization: Bearer " + token]))
  if error != OK:
   inflight = false
func _received(result, code, _headers, body):
 inflight = false
 if result != HTTPRequest.RESULT_SUCCESS or code != 200:
  return
 var state = JSON.parse_string(body.get_string_from_utf8())
 if not state is Dictionary:
  return
 connected = true
 state_changed.emit(state)
 for event in state.get("events", []):
  if int(event.id) > since:
   since = int(event.id)
   action_received.emit(str(event.action))
func send(name: String, value = null):
 if endpoint.is_empty():
  return
 var command = HTTPRequest.new()
 command.timeout = 5
 add_child(command)
 command.request_completed.connect(func(_r,_c,_h,_b): command.queue_free())
 var error = command.request(endpoint + "/command", PackedStringArray(["Authorization: Bearer " + token, "Content-Type: application/json"]), HTTPClient.METHOD_POST, JSON.stringify({"name":name,"value":value}))
 if error != OK:
  command.queue_free()
