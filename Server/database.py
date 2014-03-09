import sqlite3
import logging
import time

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

conn = sqlite3.connect("letsdothis.db")
cursor = conn.cursor()

def check_table_existance(tablename):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (tablename,))
    result = cursor.fetchall()
    logging.info("Checking for " + str(tablename) + ": " + str(result))
    if(result): return True
    return False

#Add TimeOffsets for TimeZones at some point, else this won't work internationally.
if not check_table_existance("Meetings"):
    cursor.execute("CREATE TABLE Meetings(Id INTEGER PRIMARY KEY, Name TEXT, Duration INTEGER, ProposedDate TEXT, ProposedTime INTEGER)")
    logging.info("Created Meetings")

if not check_table_existance("Events"):
    cursor.execute("CREATE TABLE Events(UserId INTEGER, StartDate TEXT, StartTime INTEGER, EndDate TEXT, EndTime INTEGER, PRIMARY KEY(UserId, StartDate, StartTime, EndDate, EndTime))")
    logging.info("Created Events")

if not check_table_existance("Users"):
    cursor.execute("CREATE TABLE Users(UserId INTEGER PRIMARY KEY, CalendarLastUpdated INTEGER)")
    logging.info("Created Users")


if not check_table_existance("Attending"):
    cursor.execute("CREATE TABLE Attending(UserId INTEGER REFERENCES Users, MeetingId INTEGER REFERENCES Meetings, Attending TEXT, PRIMARY KEY(UserId, MeetingId))")
    logging.info("Created Meetings")

conn.commit()

#Fix the repeated searches we do every time we call this. Does SQLite even allow multiple elements? Can it do it without raising an error? (Tune in next week..)
def _add_user(user):
    cursor.execute("SELECT UserId FROM Users WHERE UserId=?", (user,))
    result = cursor.fetchone()
    if not result:
        cursor.execute("INSERT INTO Users(UserId, CalendarLastUpdated) VALUES (?, 0)", (user,))
        return True
    return False

def _remove_user(user):
    cursor.execute("DELETE FROM Users WHERE UserId=?", (user,))
    cursor.execute("DELETE FROM Events WHERE UserId=?", (user,))

def _remove_if_no_meetings(user):
    if(count_meetings(user) < 1):
        _remove_user(user)

def _add_meeting(id, name, duration):
    cursor.execute("INSERT INTO Meetings(Id, Name, Duration, ProposedDate, ProposedTime) VALUES (?, ?, ?, 'UNK', -1)", (id, name, duration))

def _add_attending(user_id, meeting_id, attending="UNK"):
    cursor.execute("INSERT INTO Attending(UserId, MeetingId, Attending) VALUES (?, ?, ?)", (user_id, meeting_id, attending))

def set_attending(user_id, meeting_id, status):
    cursor.execute("UPDATE Attending SET Attending = ? WHERE UserId = ? AND MeetingId = ?", (status, user_id, meeting_id))
    conn.commit()

def add_meeting(meeting_dict):
    logging.info("Attempting to insert meeting: " + str(meeting_dict))
    user = meeting_dict["user_id"]
    meeting_id = meeting_dict["meeting_id"]
    name = meeting_dict["meeting_name"]
    duration = meeting_dict["duration"]
    friends = meeting_dict["friends"]
    assert (user and meeting_id and name and duration and len(friends) > 0), "Meeting insert failed - Insufficient Data"
    _add_user(user)
    _add_meeting(meeting_id, name, duration)
    _add_attending(user, meeting_id, attending="YES")
    for friend_id in friends:
        _add_user(friend_id)
        _add_attending(friend_id, meeting_id)
    logging.info("Meeting insert succeeded")
    conn.commit()
    return True

def get_attendees(meeting_id):
    logging.info("Retrieving Attendees")
    cursor.execute("SELECT UserId FROM Attending WHERE MeetingId=?", (meeting_id,))
    values = cursor.fetchall()
    return values

def remove_attendee(user_id, meeting_id):
    logging.info("Removing " + str(user_id) + " from " + str(meeting_id))
    cursor.execute("DELETE FROM Attending WHERE UserId=? AND MeetingId=?", (user_id, meeting_id))
    conn.commit()

def count_meetings(user_id):
    logging.info("Counting Meetings for user " + str(user_id))
    cursor.execute("SELECT COUNT(*) FROM Attending WHERE UserId=?", (user_id,))
    result = cursor.fetchone()
    return result[0]

def get_meetings(user_id):
    logging.info("Getting meetings for " + str(user_id))
    cursor.execute("SELECT MeetingId FROM Attending WHERE UserId=?", (user_id,))
    return cursor.fetchall()

def update_user_calendar_info(user_id, calendar):
    logging.info("Updating calendar info for user " + str(user_id))
    _add_user(user_id)
    cursor.execute("DELETE FROM Events WHERE UserId=?", (user_id,))
    for event in calendar["events"]:
        start_date = calendar["StartDate"]
        start_time = calendar["StartTime"]
        end_date = calendar["EndDate"]
        end_time = calendar["EndTime"]
        assert (user_id and start_date and end_date and end_time), "Unable to add calendar, insufficient data"
        cursor.execute("INSERT INTO Events(UserId, StartDate, StartTime, EndDate, EndTime) VALUES (?,?,?,?,?)", (user_id, start_date, start_time, end_date, end_time))
    cursor.execute("UPDATE Users SET CalendarLastUpdated=? WHERE UserId=?", (time.time(), user_id))
    conn.commit()
    
def remove_meeting(meeting_id):
    logging.info("Removing Meeting " + str(meeting_id))
    cursor.execute("SELECT UserId FROM Attending WHERE MeetingId=?", (meeting_id,))
    attendees = cursor.fetchall()
    cursor.execute("DELETE FROM Attending WHERE MeetingId=?", (meeting_id,))
    cursor.execute("DELETE FROM Meetings WHERE Id=?", (meeting_id,))
    for user in attendees:
        _remove_if_no_meetings(user[0])
    conn.commit()

def get_meeting_duration(meeting_id):
    logging.info("Getting meeting length")
    cursor.execute("SELECT Duration FROM Meetings WHERE Id=?", (meeting_id,))
    return cursor.fetchone()[0]

def max_meeting_id():
    logging.info("Finding Max Meeting ID")
    cursor.execute("SELECT MAX(Id) FROM Meetings")
    result = cursor.fetchone()
    if not result: return 0
    return result[0]

def get_calendar_last_updated(user_id):
    logging.info("Finding date that " + str(user_id) + "'s calendar was last updated.")
    cursor.execute("SELECT CalendarLastUpdated FROM Users WHERE UserId=?", (user_id,))
    result = cursor.fetchone()
    if result: return result[0]
    return 0

def get_ready_meetings(user_id, calendar_tolerance):
    logging.info("Listing meetings that are ready for user " + str(user_id) + "'s response.")
    adjusted_time = time.time() - calendar_tolerance
    cursor.execute("""
    SELECT Meetings.Id, Meetings.Name, Meetings.ProposedDate, Meetings.ProposedTime FROM Attending,Users,Meetings 
    WHERE Users.UserId=Attending.UserId AND Attending.MeetingId=Meetings.Id 
    AND Users.UserId = ? AND ProposedTime != -1""", (user_id,))
    return cursor.fetchall()

#REFACTOR
def get_finished_meetings(user_id):
    logging.info("Listing finished meetings for user " + str(user_id))
    cursor.execute("SELECT Attending.MeetingId FROM Attending WHERE UserId = ?", (user_id,))
    meetings = cursor.fetchall()
    result_ids = list()
    for meeting in meetings:
        cursor.execute("SELECT UserId, Attending FROM Attending WHERE MeetingId=?", (meeting[0],))
        users = cursor.fetchall()
        for user in users:
            if(user[1] == "UNK"):
                break
            if(user[1] == "NO"):
                result_ids.append((meeting[0], "NO")) 
                break
        else:
            result_ids.append((meeting[0], "YES"))
    
    results = list()
    print(result_ids)
    for meeting_pair in result_ids:
        print(meeting_pair)
        meeting_id = meeting_pair[0]
        print(meeting_id)
        cursor.execute("SELECT Id, Name, Duration, ProposedDate, ProposedTime FROM Meetings WHERE Id = ?", (meeting_id,))
        result = list(cursor.fetchone())
        result.append(meeting_pair[1])
        results.append(result)
    return results

def meeting_ready_for_time(meeting_id, calendar_tolerance):
    logging.info("Checking if meeting " + str(meeting_id) + " is ready for a time.")
    adjusted_time = time.time() - calendar_tolerance
    cursor.execute("""
    SELECT COUNT(Users.UserId) 
    FROM Users,Attending 
    WHERE Users.UserId=Attending.UserId AND Users.CalendarLastUpdated < ? AND Attending.MeetingId = ?
    """, (adjusted_time, meeting_id))
    result = cursor.fetchone()[0]
    logging.info("Result: " + str(result))
    if(result > 0): return False
    return True
    
def set_proposed_meeting_time(meeting_id, time, date):
    logging.info("Setting " + str(meeting_id) + "'s proposal to " + str(time) + " ---- " + str(date))
    cursor.execute("UPDATE Meetings SET ProposedDate=?, ProposedTime=? WHERE Id=?", (date, time, meeting_id))
    conn.commit()

def get_user_events(user_id):
    logging.info("Retrieving events for " + str(user_id))
    cursor.execute("SELECT * FROM Events WHERE UserId = ?", (user_id,))
    return cursor.fetchall()
