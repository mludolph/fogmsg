import json
import threading
import hashlib
import time
import sys
from datetime import datetime

from flask import Flask, Response, jsonify, render_template
from fogmsg.master.config import MasterConfig
from fogmsg.master.master import Master
from fogmsg.master.persistence import SQLitePersistence  # noqa


cli = sys.modules["flask.cli"]
cli.show_server_banner = lambda *x: None

app = Flask(__name__, template_folder="template")
app.config["DEBUG"] = False


def get_db():
    db = getattr(app, "db", None)
    if not db:
        config = getattr(app, "db_conf")
        setattr(app, "db", SQLitePersistence(config))
        db = getattr(app, "db")

    return db


def get_master() -> Master:
    return getattr(app, "master")


@app.route("/api/messages/<sensor_id>/<type>")
def get_messages_for_sensor(sensor_id, type):
    db = get_db()
    msgs = db.get_last_messages(sensor_id, type)
    return jsonify(msgs)


@app.route("/api/nodes")
def get_nodes():
    master = get_master()
    nodes = master.get_registered_nodes()
    ret = []
    for node in nodes:
        ret += [
            {"hashId": hashlib.md5(node.encode("utf-8")).hexdigest(), "hostname": node}
        ]

    return jsonify(ret)


def get_last_data(sensor_id, type):
    # yield initial data
    last_timestamp = 0
    db = get_db()
    msgs = db.get_last_messages(sensor_id, type)
    for msg in msgs:
        ts = datetime.utcfromtimestamp(msg["time"]).strftime("%Y-%m-%d %H:%M:%S")
        last_timestamp = msg["time"]

        del msg["time"]
        json_data = json.dumps({"time": ts, **msg})

        yield f"data:{json_data}\n\n"
    time.sleep(1)

    while True:
        msg = db.get_last_messages(sensor_id, type)[-1]
        if last_timestamp < msg["time"]:
            ts = datetime.utcfromtimestamp(msg["time"]).strftime("%Y-%m-%d %H:%M:%S")
            last_timestamp = msg["time"]
            del msg["time"]
            json_data = json.dumps({"time": ts, **msg})
            yield f"data:{json_data}\n\n"

        time.sleep(1)


@app.route("/api/live/<sensor_id>/<type>")
def live_data(sensor_id, type):
    return Response(get_last_data(sensor_id, type), mimetype="text/event-stream")


@app.route("/")
def index():
    return render_template("index.html")


class APIThread(threading.Thread):
    def __init__(self, master: Master, config: MasterConfig):
        threading.Thread.__init__(self)
        self.port = config.UI_PORT
        setattr(app, "master", master)
        setattr(app, "db_conf", config)

    def run(self):
        app.run(port=4002, threaded=True)
