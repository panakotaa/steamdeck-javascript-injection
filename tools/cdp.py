#!/usr/bin/env python3
import base64
import json
import os
import socket
import struct
import urllib.request
from urllib.parse import urlparse

CEF_URL = "http://localhost:8080"

OP_CONT  = 0x0
OP_TEXT  = 0x1
OP_BIN   = 0x2
OP_CLOSE = 0x8
OP_PING  = 0x9
OP_PONG  = 0xA


def get_targets(cef_url=CEF_URL):
    with urllib.request.urlopen(f"{cef_url}/json", timeout=5) as r:
        return json.loads(r.read())


def pick_target(targets, prefer="SharedJSContext"):
    t = next((t for t in targets if prefer in t.get("title", "")), None)
    if not t:
        t = next((t for t in targets if t.get("type") == "page"), None)
    return t


class CDPClient:
    def __init__(self, ws_url, timeout=10):
        self.ws_url = ws_url
        self.timeout = timeout
        self.sock = None
        self._id = 0

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *a):
        self.close()

    def connect(self):
        u = urlparse(self.ws_url)
        host = u.hostname
        port = u.port or 80
        path = u.path or "/"
        if u.query:
            path += "?" + u.query

        self.sock = socket.create_connection((host, port), timeout=self.timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n"
            f"\r\n"
        ).encode())

        resp = b""
        while b"\r\n\r\n" not in resp:
            chunk = self.sock.recv(1)
            if not chunk:
                raise ConnectionError("WebSocket handshake failed")
            resp += chunk
        if b"101" not in resp.split(b"\r\n")[0]:
            raise ConnectionError(f"Handshake rejected: {resp.splitlines()[0]!r}")

    def _send_frame(self, data, opcode=OP_TEXT):
        payload = data.encode("utf-8") if isinstance(data, str) else data
        header = bytearray()
        header.append(0x80 | opcode)
        length = len(payload)
        mask_bit = 0x80
        if length < 126:
            header.append(mask_bit | length)
        elif length < (1 << 16):
            header.append(mask_bit | 126)
            header += struct.pack(">H", length)
        else:
            header.append(mask_bit | 127)
            header += struct.pack(">Q", length)
        mask = os.urandom(4)
        header += mask
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(bytes(header) + masked)

    def _recv_exact(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("Connection closed during read")
            buf += chunk
        return buf

    def _recv_frame(self):
        b0, b1 = self._recv_exact(2)
        fin    = b0 & 0x80
        opcode = b0 & 0x0F
        masked = b1 & 0x80
        length = b1 & 0x7F
        if length == 126:
            length = struct.unpack(">H", self._recv_exact(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", self._recv_exact(8))[0]
        mask    = self._recv_exact(4) if masked else None
        payload = self._recv_exact(length) if length else b""
        if mask:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        return fin, opcode, payload

    def _recv_message(self):
        data = b""
        while True:
            fin, opcode, payload = self._recv_frame()
            if opcode == OP_PING:
                self._send_frame(payload, OP_PONG)
                continue
            if opcode == OP_CLOSE:
                raise ConnectionError("WebSocket closed by server")
            if opcode in (OP_TEXT, OP_BIN, OP_CONT):
                data += payload
                if fin:
                    return data

    def evaluate(self, expression, await_promise=True, return_by_value=True):
        self._id += 1
        msg_id = self._id
        self._send_frame(json.dumps({
            "id": msg_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "returnByValue": return_by_value,
                "awaitPromise": await_promise,
                "userGesture": True,
            },
        }))
        while True:
            obj = json.loads(self._recv_message().decode("utf-8"))
            if obj.get("id") == msg_id:
                return obj

    def call(self, method, params=None):
        self._id += 1
        msg_id = self._id
        self._send_frame(json.dumps({
            "id": msg_id, "method": method, "params": params or {},
        }))
        while True:
            obj = json.loads(self._recv_message().decode("utf-8"))
            if obj.get("id") == msg_id:
                return obj

    def screenshot(self, path, fmt="png"):
        resp = self.call("Page.captureScreenshot", {"format": fmt})
        data = resp.get("result", {}).get("data")
        if not data:
            raise RuntimeError(f"No screenshot data: {resp}")
        with open(path, "wb") as f:
            f.write(base64.b64decode(data))
        return path

    def close(self):
        if self.sock:
            try:
                self._send_frame(b"", OP_CLOSE)
            except Exception:
                pass
            try:
                self.sock.close()
            finally:
                self.sock = None


def eval_on_page(expression, cef_url=CEF_URL, prefer="SharedJSContext"):
    targets = get_targets(cef_url)
    target = pick_target(targets, prefer)
    if not target:
        raise RuntimeError("No CEF page available")
    with CDPClient(target["webSocketDebuggerUrl"]) as c:
        return c.evaluate(expression)


def extract_value(cdp_response):
    res = cdp_response.get("result", {})
    if "exceptionDetails" in res:
        exc = res["exceptionDetails"]
        return f"[JS EXCEPTION] {exc.get('text')} {exc.get('exception', {}).get('description', '')}"
    return res.get("result", {}).get("value")


if __name__ == "__main__":
    try:
        r = eval_on_page("1 + 1")
        print("CDP OK, 1+1 =", extract_value(r))
    except Exception as e:
        print("CDP FAIL:", e)
