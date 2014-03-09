from bottle import run, route, post, request, abort, response
from message_handlers import message_handlers

@route('/json/<action>')
def handle_json(action):
    data = request.json
    spoof_cal = {"calendar_id":102, "events":[]}
    if action == "meeting_request": data = {"user_id":62, "meeting_name":"Battle of the Nerf Guns", "duration":60, "time_offset":2, "friends":["16","17","18"], "calendar_info":spoof_cal}
    if action == "check_in": data = {"user_id":62, "time":113, "date":"09-03-14", "time_offset":0}
    if not data:
        abort(400, "Bad JSON Syntax")
    response.content_type = "application/json"
    reply = message_handlers.get(action, lambda: abort(404, "Invalid JSON URI"))(data)
    return reply.to_json() 


run(host="localhost", port=9011)
