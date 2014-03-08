from bottle import response
import json
import database
import logging
import traceback

def _create_ack(meeting_id, status):
    ack = {
        "server_id": "1",
        "status": status,
        "meeting_id": meeting_id
    }
    return json.dumps(ack)

def meeting_request(dict_received):
    try:
        meeting_id = database.max_meeting_id()+1
        dict_received["meeting_id"] = meeting_id
        database.add_meeting(dict_received)
        database.add_user_calendar_info(dict_received["calendar_info"])
        return _create_ack(meeting_id, "success")
    except AssertionError as e:
        logging.error("Assertion failed in meeting request, printing stack trace.")
        traceback.print_exc()
        return _create_ack(-1, "failure")


def check_in(json):
    pass

def action_response(json):
    pass



message_handlers = {
    "meeting_request": meeting_request,
    "check_in": check_in,
    "action_response": action_response
}
