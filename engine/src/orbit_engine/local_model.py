"""Fixed loopback Ollama inference; no environment hosts, proxies or redirects."""
import http.client
import json
import os
import stat
import re
import socket
import time
from pathlib import Path
from .ollama import _LocalConnection
from .tasks import TaskError

MAX_RESPONSE = 262144

class LocalModel:
    def __init__(self):
        self.connection = None
        self.socket = None

    def cancel(self):
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def request(self, route, payload, stopped):
        if stopped.is_set():
            raise TaskError('Run cancelled')
        connection = _LocalConnection('127.0.0.1', 11434, timeout=120)
        connection.deadline = time.monotonic() + 120
        self.connection = connection
        try:
            connection.request('POST', route, json.dumps(payload).encode(),
                               {'Content-Type': 'application/json'})
            self.socket = connection.sock
            if stopped.is_set():
                raise TaskError('Run cancelled')
            response = connection.getresponse()
            if response.status != 200:
                raise TaskError('Local model request failed; no fallback attempted')
            body = bytearray()
            while True:
                if stopped.is_set():
                    raise TaskError('Run cancelled')
                chunk = response.read1(min(8192, MAX_RESPONSE + 1 - len(body)))
                body.extend(chunk)
                if len(body) > MAX_RESPONSE:
                    raise TaskError('Local model response exceeded limit')
                if not chunk:
                    break
            value = json.loads(body)
            if not isinstance(value, dict):
                raise ValueError()
            return value
        except TaskError:
            raise
        except (OSError, ValueError, RecursionError, http.client.HTTPException) as exc:
            raise TaskError('Local model unavailable, timed out or returned invalid data') from exc
        finally:
            connection.close()
            self.connection = None
            self.socket = None

    def verify(self, model, stopped):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}', model) or 'cloud' in model.lower():
            raise TaskError('Choose an installed local model')
        info = self.request('/api/show', {'model': model}, stopped)
        if any(info.get(key) for key in ('remote_model', 'remote_host')):
            raise TaskError('Cloud model entries cannot execute')
        capabilities = info.get('capabilities')
        if not isinstance(capabilities, list) or 'completion' not in capabilities:
            raise TaskError('Model completion capability is unverified')
        # Require a real local GGUF, not a cloud alias or inventory-only assertion.
        match = re.search(r'^FROM (.+)$', info.get('modelfile', ''), re.MULTILINE)
        if not match:
            raise TaskError('Local model weights are unverified')
        path = Path(match[1].strip().strip('"'))
        if not path.is_absolute() or not re.fullmatch(r'sha256-[0-9a-f]{64}', path.name):
            raise TaskError('Local model weights are unverified')
        try:
            if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
                raise TaskError('Local regular GGUF weights required')
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, 'rb') as weights:
                if weights.read(4) != b'GGUF':
                    raise TaskError('Local GGUF weights required')
        except OSError as exc:
            raise TaskError('Local model weights are unavailable') from exc
        return path.name

    def generate(self, model, prompt, stopped):
        value = self.request('/api/chat', {
            'model': model, 'messages': [{'role': 'user', 'content': prompt}],
            'stream': False, 'format': 'json', 'think': False,
            'options': {'num_predict': 8192, 'temperature': 0}, 'keep_alive': '0s',
        }, stopped)
        if value.get('done') is not True or value.get('done_reason') != 'stop':
            raise TaskError('Model did not complete a bounded response')
        try:
            return json.loads(value['message']['content'])
        except (KeyError, TypeError, ValueError, RecursionError) as exc:
            raise TaskError('Model did not return file replacement JSON') from exc
