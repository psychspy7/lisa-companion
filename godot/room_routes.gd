extends RefCounted
const NODES = {
"room":Vector3(0,0,0.25),"front":Vector3(0,0,2.12),"sofa":Vector3(3.90,0,2.18),"bed":Vector3(2.03,0,-0.92),
"bathFront":Vector3(-0.94,0,-1.25),"bathDoor":Vector3(-0.94,0.045,-1.92),"bathroom":Vector3(-0.94,0.095,-2.44),"bathInside":Vector3(-2.38,0.095,-2.35),
"shower":Vector3(-2.38,0.095,-3.6),"toilet":Vector3(-1.06,0.055,-3.35),"toiletFront":Vector3(-1.06,0.095,-2.82),
"leftAisle":Vector3(-4.45,0,-0.8),"wardrobe":Vector3(-4.45,0,-2.72),"washbasin":Vector3(-3.35,0,-1.45),
"rightAisle":Vector3(3.96,0,-0.72),"balconyFront":Vector3(5.20,0,-1.43),"balconyDoor":Vector3(6.13,0,-1.43),"balcony":Vector3(7.08,0,-1.94)}
const EDGES = [["room","front"],["front","sofa"],["room","bed"],["room","bathFront"],["bathFront","bathDoor"],["bathDoor","bathroom"],["bathroom","bathInside"],["bathroom","toiletFront"],["toiletFront","toilet"],["bathInside","shower"],["room","leftAisle"],["leftAisle","wardrobe"],["leftAisle","washbasin"],["bed","rightAisle"],["rightAisle","balconyFront"],["balconyFront","balconyDoor"],["balconyDoor","balcony"]]
static func shortest(start:String, finish:String):
 var costs = {start:0.0}
 var previous = {}
 var pending = NODES.keys()
 while not pending.is_empty():
  var u = pending[0]
  for candidate in pending:
   if costs.get(candidate,INF) < costs.get(u,INF):
    u = candidate
  pending.erase(u)
  if u == finish:
   break
  for edge in EDGES:
   var v = edge[1] if edge[0] == u else edge[0] if edge[1] == u else ""
   if v.is_empty() or not pending.has(v):
    continue
   var cost = costs.get(u,INF) + NODES[u].distance_to(NODES[v])
   if cost < costs.get(v,INF):
    costs[v] = cost
    previous[v] = u
 var path = [finish]
 while path[0] != start:
  if not previous.has(path[0]):
   return {"cost":INF,"path":[]}
  path.push_front(previous[path[0]])
 return {"cost":costs.get(finish,INF),"path":path}
static func route(position:Vector3,destination:String):
 if not NODES.has(destination):
  return []
 var best = INF
 var points = []
 for edge in EDGES:
  var p:Vector3 = NODES[edge[0]]
  var q:Vector3 = NODES[edge[1]]
  var flat = Vector3(q.x-p.x,0,q.z-p.z)
  var t = clampf(Vector3(position.x-p.x,0,position.z-p.z).dot(flat)/flat.length_squared(),0,1)
  var projection = p.lerp(q,t)
  for name in edge:
   var result = shortest(name,destination)
   var cost = position.distance_to(projection)+projection.distance_to(NODES[name])+result.cost
   if cost < best:
    best = cost
    points = [projection]
    for n in result.path:
     points.append(NODES[n])
 var cleaned = []
 var last = position
 for point in points:
  if last.distance_to(point)>0.012:
   cleaned.append(point)
   last = point
 return cleaned
