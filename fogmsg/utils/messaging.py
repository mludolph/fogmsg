from fogmsg.node.sensor import GPSSensor, MetricsSensor
from typing import List, Union

# message types
_REG = "1"
_UNREG = "2"
_ACK = "3"
_PUB = "4"
_CTRL = "5"

# payload types
_PAYLOAD_METRICS = "1"
_PAYLOAD_GPS = "2"

# seperator
_SEPERATOR = "|"


def ack_message():
    return _ACK.encode("utf-8")


def register_message(advertised_hostname: str) -> bytes:
    return _SEPERATOR.join([_REG, advertised_hostname]).encode("utf-8")


def unregister_message(advertised_hostname: str) -> bytes:
    return _SEPERATOR.join([_UNREG, advertised_hostname]).encode("utf-8")


def control_message(action: str) -> bytes:
    return _SEPERATOR.join([_CTRL, action]).encode("utf-8")


def publish_message(origin: str, sensor: str, payload: dict) -> bytes:
    parts = [_PUB, origin]
    if sensor == "metrics":
        schema = MetricsSensor.schema()
        parts += [
            _PAYLOAD_METRICS,
            _serialize_payload(schema, payload),
        ]
    elif sensor == "gps":
        schema = GPSSensor.schema()
        parts += [
            _PAYLOAD_GPS,
            _serialize_payload(schema, payload),
        ]

    return _SEPERATOR.join(parts).encode("utf-8")


def _serialize_payload(schema: dict, payload: dict) -> str:
    ret = []
    fields = schema["_order"]
    for field in fields:
        ret += [str(payload[field])]

    return _SEPERATOR.join(ret)


def _deseralize_payload(schema: dict, payload_tokens: List[str]) -> dict:
    ret = {}
    fields = schema["_order"]

    for idx, field in enumerate(fields):
        type = schema[field]
        ret[field] = type(payload_tokens[idx])

    return ret


def deserialize(msg: bytes) -> Union[dict, str]:
    msg = msg.decode("utf-8")
    parts = msg.split(_SEPERATOR)
    cmd = parts[0]
    if cmd == _REG:
        return {"cmd": "register", "advertised_hostname": parts[1]}
    elif cmd == _UNREG:
        return {"cmd": "unregister", "advertised_hostname": parts[1]}
    elif cmd == _ACK:
        return "ack"
    elif cmd == _CTRL:
        return {"cmd": "control", "action": parts[1]}
    elif cmd == _PUB:
        origin = parts[1]
        type = parts[2]
        if type == _PAYLOAD_METRICS:
            sensor = "metrics"
            schema = MetricsSensor.schema()
        elif type == _PAYLOAD_GPS:
            sensor = "gps"
            schema = GPSSensor.schema()

        return {
            "cmd": "publish",
            "origin": origin,
            "sensor": sensor,
            "payload": _deseralize_payload(schema, parts[3:]),
        }
