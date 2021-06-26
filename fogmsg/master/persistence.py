import hashlib
import os
import sqlite3
import time

from fogmsg.master.config import MasterConfig


class SQLitePersistence:
    def __init__(self, config: MasterConfig):
        self.db = sqlite3.connect(
            os.path.join(config.PERSISTENCE_DIR, "messages.sqlite"),
            check_same_thread=False,
        )
        cur = self.db.cursor()

        try:
            cur.execute(
                """CREATE TABLE gpsdata
                (nodeHashId text, time integer, lat real, lon real)"""
            )

            cur.execute(
                """CREATE TABLE metricsdata
                (nodeHashId text, time integer, cpu_percent real, \
                mem_used integer, mem_free integer, mem_percent real, \
                net_sent integer, net_received integer)"""
            )
        except sqlite3.OperationalError:
            pass

    def get_last_messages(self, nodeHashId: str, type: str):
        cur = self.db.cursor()
        if type not in ["metrics", "gps"]:
            return None

        now = int(time.time())

        cur.execute(
            f"""SELECT * from {type}data
               WHERE nodeHashId like "{nodeHashId}"
                     and time > {now - 60}
               ORDER BY time DESC
            """
        )

        rows = cur.fetchall()
        ret = []

        if type == "gps":
            for row in rows:
                ret += [{"time": row[1], "lat": row[2], "lng": row[3]}]
        elif type == "metrics":
            for row in rows:
                ret += [
                    {
                        "time": row[1],
                        "cpu_percent": row[2],
                        "mem_used": row[3],
                        "mem_free": row[4],
                        "mem_percent": row[5],
                        "net_sent": row[6],
                        "net_received": row[7],
                    }
                ]
        return ret

    def persist_message(self, msg: dict):
        cur = self.db.cursor()

        origin = msg.get("origin", None)
        sensor = msg.get("sensor", None)
        payload = msg.get("payload", None)

        if not origin or not sensor or not payload:

            return

        origin = hashlib.md5(origin.encode("utf-8")).hexdigest()

        if sensor == "gps":
            time, lat, lon = payload["time"], payload["lat"], payload["lng"]
            cur.execute(
                f"""INSERT INTO gpsdata VALUES ("{origin}",{time},{lat},{lon})"""
            )
        elif sensor == "metrics":
            time, cpu_percent = payload["time"], payload["cpu_percent"]
            mem_used, mem_free, mem_percent = (
                payload["mem_used"],
                payload["mem_free"],
                payload["mem_percent"],
            )
            net_sent, net_received = payload["net_sent"], payload["net_received"]

            cur.execute(
                f"""INSERT INTO metricsdata VALUES ("{origin}",{time},{cpu_percent},{mem_used},\
                    {mem_free},{mem_percent},{net_sent},{net_received})"""
            )
        self.db.commit()

    def close(self):
        self.db.close()
