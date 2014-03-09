from bottle import response
import json
import database
import logging
import traceback
import time

#In Seconds
CALENDAR_TOLERANCE= 60 * 60 * 6 # 4 hours

class Response:
    def __init__(self, status):
        self.dict = {
            "server_id": "1",
            "status": status
        }

    def to_json(self):
        return json.dumps(self.dict)

class AckResponse(Response):
    def __init__(self, meeting_id, status):
        super(AckResponse, self).__init__(status)
        self.dict["meeting_id"] = meeting_id


class CheckInResponse(Response):
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

    def _update_calendar_if_needed(self, user_id):
        logging.info("Checking for Calendar Updates")
        last_updated = database.get_calendar_last_updated(user_id)
        logging.info("User " + str(user_id) + "'s calendar was last updated: " + str(last_updated))
        if database.count_meetings(user_id) > 0 and (last_updated + CALENDAR_TOLERANCE) < time.time():
            self.add_action("send_calendar_data")

    def _update_if_proposed_time(self, user_id):
        results = database.get_ready_meetings(user_id, CALENDAR_TOLERANCE)
        for meeting in results:
            self.add_action("respond_to_time", {
                "meeting_id": meeting[0],
                "meeting_name": meeting[1],
                "proposed" : {
                    "date": meeting[2],
                    "time": meeting[3]
                }
            })
        

def meeting_request(dict_received):
    try:
        meeting_id = database.max_meeting_id()+1
        dict_received["meeting_id"] = meeting_id
        database.add_meeting(dict_received)
        database.update_user_calendar_info(dict_received["user_id"], dict_received["calendar_info"])
        return AckResponse(meeting_id, "success")
    except AssertionError as e:
        logging.error("Assertion failed in meeting request, printing stack trace.")
        traceback.print_exc()
        return AckResponse(-1, "failure")


def check_in(dict_received):
    reply = CheckInResponse("success")
    reply.update_actions(dict_received["user_id"])
    return reply


def action_response(dict_received):
    pass



message_handlers = {
    "meeting_request": meeting_request,
    "check_in": check_in,
    "action_response": action_response
}
