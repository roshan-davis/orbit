"""Bounded, read-only discovery. Never consult environment hosts or proxies."""
import http.client
import json
import re
import socket
import time

ENDPOINT = "http://127.0.0.1:11434"
TIMEOUT = 0.5
MAX_BYTES = 262_144
MAX_MODELS = 256
_SAFE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/+@ -]{0,199}\Z")


class InvalidResponse(ValueError):
    pass


def _text(value):
    return value if isinstance(value, str) and _SAFE.fullmatch(value) else None


def _models(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
        raise InvalidResponse()
    if len(payload["models"]) > MAX_MODELS:
        raise InvalidResponse()
    result = []
    for item in payload["models"]:
        if not isinstance(item, dict) or not _text(item.get("name")):
            raise InvalidResponse()
        model = {"name": item["name"], "capabilities": {"tools": "unknown"}}
        for key in ("model", "modified_at", "digest"):
            if (value := _text(item.get(key))) is not None:
                model[key] = value
        size = item.get("size")
        if type(size) is int and 0 <= size <= 2**63 - 1:
            model["size_bytes"] = size
        details = item.get("details")
        if isinstance(details, dict):
            model["details"] = {key: value for key in (
                "format", "family", "parameter_size", "quantization_level")
                if (value := _text(details.get(key))) is not None}
            families = details.get("families")
            if isinstance(families, list):
                model["details"]["families"] = [v for v in families[:32] if _text(v)]
        result.append(model)
    return result


class _DeadlineSocket(socket.socket):
    """Apply one deadline to header and body reads, including slow trickles."""

    def recv_into(self, *args):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError()
        self.settimeout(remaining)
        return super().recv_into(*args)


class _LocalConnection(http.client.HTTPConnection):
    def connect(self):
        self.sock = _DeadlineSocket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.deadline = self.deadline
        self.sock.settimeout(max(0.001, self.deadline - time.monotonic()))
        self.sock.connect(("127.0.0.1", 11434))


def discover(endpoint=ENDPOINT):
    """Only the fixed literal loopback endpoint is accepted; redirects are not followed.

    Local reachability proves neither authentication nor execution/tool readiness.
    All error messages are fixed strings, never server bodies or exception details.
    """
    result = {"status": "offline", "reachable": False, "models": [],
              "endpoint": ENDPOINT, "execution_ready": False,
              "authentication": "unknown"}
    if endpoint != ENDPOINT:
        return {**result, "status": "invalid_endpoint"}
    deadline = time.monotonic() + TIMEOUT
    connection = _LocalConnection("127.0.0.1", 11434, timeout=TIMEOUT)
    connection.deadline = deadline
    response = None
    try:
        connection.request("GET", "/api/tags", headers={"Accept": "application/json"})
        response = connection.getresponse()
        result["reachable"] = True
        if 300 <= response.status < 400:
            return {**result, "status": "redirect_rejected"}
        if response.status != 200:
            return {**result, "status": "http_error"}
        length = response.getheader("Content-Length")
        if length is not None and (not length.isdecimal() or int(length) > MAX_BYTES):
            raise InvalidResponse()
        body = bytearray()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError()
            if connection.sock is not None:
                connection.sock.settimeout(remaining)
            chunk = response.read1(min(8192, MAX_BYTES + 1 - len(body)))
            body.extend(chunk)
            if len(body) > MAX_BYTES:
                raise InvalidResponse()
            if not chunk:
                break
        if length is not None and len(body) != int(length):
            raise InvalidResponse()
        models = _models(json.loads(body))
        return {**result, "status": "available" if models else "empty", "models": models}
    except (TimeoutError, socket.timeout):
        return {**result, "status": "timeout"}
    except (ValueError, UnicodeError, RecursionError, http.client.IncompleteRead):
        return {**result, "status": "malformed"}
    except (OSError, http.client.HTTPException):
        return result
    finally:
        if response is not None:
            response.close()
        connection.close()
