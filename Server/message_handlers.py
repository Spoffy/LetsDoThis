#CONFIG
CALENDAR_TOLERANCE = 60 * 60 * 3
#ENDCONFIG
from bottle import response
import json
import database
import logging
import traceback
import time
from action_handlers import action_handlers, update_calendar_data


class _Response:
    def __init__(self, status):
        self.dict = {
            "server_id": "1",
            "status": status
        }

    def to_json(self):
        return json.dumps(self.dict)

class AckResponse(_Response):
    def __init__(self, meeting_id, status):
        super(AckResponse, self).__init__(status)
        self.dict["meeting_id"] = meeting_id


class CheckInResponse(_Response):
    def __init__(self, status):
        super(CheckInResponse, self).__init__(status)
        self.dict["actions"] = list()

    def add_action(self, action, data=None):
        self.dict["actions"].append({
            "action":action,
            "data": data
        })

    def update_actions(self, user_id):
        self._update_calendar_if_needed(user_id)
        self._update_if_proposed_time(user_id)
        self._notify_if_arranging_complete(user_id)

    def _update_calendar_if_needed(self, user_id):
        logging.info("Checking for Calendar Updates")
        last_updated = database.get_calendar_last_updated(user_id)
        logging.info("User " + str(user_id) + "'s calendar was last updated: " + str(last_updated))
        if database.count_meetings(user_id) > 0 and (last_updated + CALENDAR_TOLERANCE) < time.time():
            self.add_action("send_calendar_data")

    def _update_if_proposed_time(self, user_id):
        logging.info("Checking for times to propose...")
        results = database.get_ready_meetings(user_id, CALENDAR_TOLERANCE)
        logging.info("Found " + str(results) + " ready meetings.")
        for meeting in results:
            self.add_action("respond_to_time", [
                meeting[0],
                meeting[1],
                meeting[2],
                meeting[3]
                ]
            )
        
    def _notify_if_arranging_complete(self, user_id):
        logging.info("Looking for finished meetings...")
        meetings = database.get_finished_meetings(user_id)
        logging.info("Meetings found: " + str(meetings))
        for meeting in meetings:
            self.add_action("notify_meeting", meeting)
            database.remove_attendee(user_id, meeting[0])


def meeting_request(dict_received):
    try:
        meeting_id = database.max_meeting_id()+1
        dict_received["meeting_id"] = meeting_id
        database.add_meeting(dict_received)
        update_calendar_data(dict_received["user_id"], dict_received["calendar_info"])
        return AckResponse(meeting_id, "success")
    except (KeyError, AssertionError):
        logging.error("Assertion failed in meeting request, printing stack trace.")
        traceback.print_exc()
        return AckResponse(-1, "failure")


def check_in(dict_received):
    try:
        logging.info("Check in by User: " + str(dict_received["user_id"]))
        status = "success"
        if not dict_received["user_id"]: status = "failure"
        reply = CheckInResponse("success")
        reply.update_actions(dict_received["user_id"])
        return reply
    except (AssertionError, KeyError):
        logging.error("Check in Error.")
        traceback.print_exc()
        return AckResponse(-1, "failure")


def action_response(dict_received):
    try:
        user_id = dict_received["user_id"]
        action = dict_received["action"]
        assert (user_id and action), "Missing Json Data"
        action_handlers[action["action"]](user_id, action["data"])
        return AckResponse(-1, "success")
    except (KeyError, AssertionError):
        logging.error("Assertion failed, received bad Action Response")
        traceback.print_exc()
        return AckResponse(-1, "failure")



message_handlers = {
    "meeting_request": meeting_request,
    "check_in": check_in,
    "action_response": action_response
}
