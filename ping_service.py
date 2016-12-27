import requests
import json
import redis
import os
from flask import Flask

app = Flask(__name__)
url = os.environ['PING_SERVICE_URL']
token = os.environ['PING_SERVICE_TOKEN']
ping_expire_time = 60
terminal_reload_time = 120
conn = redis.StrictRedis()


def get_terminal_data():
    response = requests.get(url, headers={'Authorization': 'Token %s' % token})
    if response.ok:
         return response.content
    else:
        response.raise_for_status()


def get_cached_terminals():
    if conn.ttl('terminals/list') < 0:
        data = get_terminal_data()
        conn.set('terminals/list', data, ex=terminal_reload_time)
        print "Requested new terminal data"

    return json.loads(conn.get('terminals/list'))


def update_status(conn, place):
    conn_value = 'Unknown'
    if place is not None:
        resp = os.system("ping -c 1 %s" % place)
        if resp == 0:
            conn_value = "Connected"
        else:
            conn_value = "Unreachable"
    conn.set('terminals/status/%s' % place, conn_value, ex=ping_expire_time)


@app.route("/")
def status():
    l = []
 
    for t in get_cached_terminals():
        place = t['place']
        key = "terminals/status/%s" % place
        if conn.ttl(key) < 0:
            print "Updating status from %s" % place
            update_status(conn, place)

        t['status'] = conn.get(key)
        l.append(t)

    return json.dumps(l)


if __name__ == "__main__":
    app.run()
	
