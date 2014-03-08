from bottle import run, route, post, request, abort, response
from message_handlers import message_handlers

@route('/json/<action>')
def handle_json(action):
    data = request.json
    if not data:
        abort(400, "Bad JSON Syntax")
    response.content_type = "application/json"
    return message_handlers.get(action, lambda: abort(404, "Invalid JSON URI"))()


run(host="localhost", port=9011)
