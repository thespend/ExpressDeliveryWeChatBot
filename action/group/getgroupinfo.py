import http.client
import json
from env_loader import TOKEN


def get_group_info(group_id):
    conn = http.client.HTTPConnection("124.221.45.58")
    payload = json.dumps({
       "chatroomId": group_id
    })
    headers = {
       'AUTHORIZATION': TOKEN,
       'Content-Type': 'application/json'
    }
    conn.request("POST", "/getGroupInfo", payload, headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))

