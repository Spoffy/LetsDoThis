import database
import logging
import time
import sys

_START_OFFSET = (60 * 60 * 24)
_END_OFFSET = (60 * 60 * 24 * 30)

_EARLIEST_START = 0
_LATEST_START = 1

def calculate_meeting_time(meeting_id):
    duration = database.get_meeting_duration(meeting_id) * 60 #In seconds
    free_time = list()
    free_time_buffer = list()
    events = _get_events(meeting_id)

    free_time.append(_starting_time())

    for event in events:
        for block in free_time:
            if block[0] <= event[0] and block[1] >= event[1]:
                free_time_buffer.append((block[0], event[0]))
                free_time_buffer.append((event[1], block[1]))
        
        free_time = free_time_buffer
        free_time_buffer = list()

    valid_min = (sys.maxsize, sys.maxsize)
    for block in free_time:
        if(block[1] - block[0] >= duration and block[0] < valid_min[0]):
            valid_min = block
    
    struct_time = time.gmtime(valid_min[0])
    date = time.strftime("%d-%m-%y", struct_time)
    minutes = (valid_min[0]-time_to_epoch(date, 0))/60
    return (date, minutes)

def _starting_time():
    init = time.time() + _START_OFFSET
    end = time.time() + _END_OFFSET
    return (init, end)
    
    
def _get_events(meeting_id):
    timetables = list()
    attendees = database.get_attendees(meeting_id)
    events = list()
    for attendee in attendees:
        timetables.append(database.get_user_events(attendee[0]))
    for timetable in timetables:
        for event in timetable:
            events.append(_event_to_tuple(event))

    return events

def _event_to_tuple(event):
    start_time = time_to_epoch(event[1], event[2])
    end_time = time_to_epoch(event[3], event[4])
    return (start_time, end_time)
    

def time_to_epoch(date_string, minutes_since_midnight):
    timestruct = time.strptime(date_string, "%d-%m-%y") 
    midnight_since_epoch = time.mktime(timestruct)
    return midnight_since_epoch + minutes_since_midnight * 60
