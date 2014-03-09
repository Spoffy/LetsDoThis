import logging
import traceback
import database
from message_handlers import CALENDAR_TOLERANCE
from meeting_time_calc import calculate_meeting_time

def respond_to_time(user_id, data):
    meeting_id = data[0]
    decision = data[1]
    assert (user_id and decision), "Invalid response to time"
    database.set_attending(user_id, meeting_id, decision)
        

def update_calendar_data(user_id, data):
    assert (user_id and data), "Invalid set of calendar data"
    database.update_user_calendar_info(user_id, data)
    meetings = database.get_meetings(user_id)
    for meeting in meetings:
        if(database.meeting_ready_for_time(meeting[0], CALENDAR_TOLERANCE)):
            time_tuple = calculate_meeting_time(meeting[0])
            database.set_proposed_meeting_time(meeting[0], time_tuple[1], time_tuple[0])

action_handlers = {
    "respond_to_time": respond_to_time,
    "send_calendar_data": update_calendar_data
}
