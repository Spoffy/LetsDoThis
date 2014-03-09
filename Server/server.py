from bottle import run, route, post, request, abort, response
from message_handlers import message_handlers, AckResponse
import logging
import traceback

@post('/json/<action>')
def handle_json(action):
    logging.info("Incoming JSON Body: " + str(request.body.getvalue(), encoding='UTF-8'))
    try:
        data = request.json
    except ValueError:
        traceback.print_exc()
        return AckResponse(-1,"failure").to_json()
    if not data:
        abort(400, "Bad JSON Syntax")
    response.content_type = "application/json"
    reply = message_handlers.get(action, lambda self: abort(404, "Invalid JSON URI"))(data)
    return reply.to_json() 


#run(host="152.78.201.14", port=9011)
run(host="localhost", port=9012)
