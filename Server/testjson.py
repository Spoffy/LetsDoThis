import http.client, urllib.parse
import logging
import time
import json

logging.getLogger().setLevel("WARN")

#params = urllib.parse.urlencode({'@number': 12524, '@type': 'issue', '@action': 'show'})
headers = {"Content-type": "application/json",
           "Accept": "text/plain"}

def post_json(action, json):
    conn = http.client.HTTPConnection("localhost", port=9012)
    conn.request("POST", "/json/"+action, json, headers)
    response = conn.getresponse()
    logging.info("Response: " + str(response.status) + str(response.reason))
    data = response.read()
    logging.info("Response Body: " + str(data))
    conn.close()
    return data

spoof_cal = {"calendar_id":102, "events":[{"StartDate":"10-03-14", "StartTime":960, "EndDate":"11-03-14", "EndTime":600}]}
spoof_meeting = {"user_id":60, "meeting_name":"Meeting: " + str(time.time()), "duration":60, "time_offset":2, "friends":["70","71","72"], "calendar_info":spoof_cal}
spoof_meeting2 = {"user_id":50, "meeting_name":"Meeting: " + str(time.time()), "duration":60, "time_offset":2, "friends":["80"], "calendar_info":spoof_cal}

def perform_action(id, action, body):
    response = '{"user_id":' + str(id) + ', "action":'
    if action == "respond_to_time":
        meeting_id = body[0]
        response = response + '{"action":"respond_to_time", "data":["' + str(meeting_id) + '", "YES"]}'
    if action == "send_calendar_data":
        temp = {"action":"send_calendar_data", "data":spoof_cal}
        response = response + json.dumps(temp)
    if action == "notify_meeting":
        meeting_name = str(body[0])
        duration = str(body[1])
        date = str(body[2])
        time = str(body[3])
        result = str(body[4])
        print("MEETING ARRANGED: " + meeting_name + " " + duration + " " + date + " " + time + " " + result)
        return
    response = response + "}"
    print(json.loads(response))
    post_json("action_response", response)

def check_in(id):
    checkin = json.dumps({"user_id":id, "time":113, "date":"09-03-14", "time_offset":0})
    result = str(post_json("check_in", checkin), encoding="UTF-8")
    result = json.loads(result)
    for action in result["actions"]:
        logging.info("Action Received: " + str(action["action"]))
        logging.info("Data: " + str(action["data"]))
        perform_action(id, action["action"], action["data"])

    


logging.info("Attempting check in with empty body")
post_json("check_in", "")

logging.info("Attempting check in with user_id 62")
post_json("check_in", '{"user_id":62}')

logging.info("Request Meeting as User 60")
post_json("meeting_request", json.dumps(spoof_meeting))

logging.info("Check in as User 70")
check_in(70)

logging.info("Check in as User 70")
check_in(70)

logging.info("Request Meeting as User 50 with 80")
post_json("meeting_request", json.dumps(spoof_meeting2))

logging.info("Check in as User 80")
check_in(80)

logging.info("Check in as User 80")
check_in(80)
logging.info("Check in as User 80")
check_in(80)
