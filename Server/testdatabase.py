import logging
import database
import imp

cursor = database.cursor

cursor.execute("DROP TABLE Meetings")
cursor.execute("DROP TABLE Attending")
cursor.execute("DROP TABLE Users")
cursor.execute("DROP TABLE Events")
database.conn.commit()
database.conn.close()

imp.reload(database)

cursor = database.cursor

def dump_database():
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        logging.info("Table Found: " + str(table[0]))
        dump_table(table[0])

def dump_table(table):
    cursor.execute("SELECT * FROM " + table )
    results = cursor.fetchall()
    for result in results:
        logging.info("      Entry: " + str(result))

meetingOne = {
    "meeting_id":1,
    "user_id":2,
    "meeting_name":"Meeting One",
    "duration":60,
    "friends": [4,6,8]
}

meetingTwo = {
    "meeting_id":3,
    "user_id":4,
    "meeting_name":"Meeting Two",
    "duration":60,
    "friends": [6,8,10]
}

logging.info("Adding Meeting One")
database.add_meeting(meetingOne)
logging.info("Counting Meetings for User 4: " + str(database.count_meetings(4)))

logging.info("Adding Meeting Two")
database.add_meeting(meetingTwo)
logging.info("Counting Meetings for User 4: " + str(database.count_meetings(4)))

logging.info("Printing attendees of meeting one")
attendees = database.get_attendees(1)
for user in attendees:
    logging.info("Attending One: " + str(user[0]))

logging.info("Removing meeting One")
database.remove_meeting(1)
logging.info("Counting Meetings for User 4: " + str(database.count_meetings(4)))
attendees = database.get_attendees(3)
for user in attendees:
    logging.info("Attending Two: " + str(user[0]))


database.set_attending(8,3,"YES")

dump_database()
