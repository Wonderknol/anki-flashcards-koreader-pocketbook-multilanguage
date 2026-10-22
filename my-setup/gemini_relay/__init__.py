"""Gemini relay: lets the KOReader Anki plugin call Gemini through this PC."""
import json
import os
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from aqt import gui_hooks, mw
from aqt.utils import tooltip

ADDON = __name__
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "relay.log")

_cfg = {}
_server = None


def _load_config():
    global _cfg
    _cfg = mw.addonManager.getConfig(ADDON) or {}


def _log(line):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")
    except OSError:
        pass


def ask_gemini(prompt):
    key = (_cfg.get("gemini_api_key") or "").strip()
    if not key:
        raise RuntimeError("No Gemini API key set in the add-on config")
    model = _cfg.get("gemini_model") or "gemini-3.5-flash-lite"
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent")
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json", "x-goog-api-key": key})
    last = "unknown error"
    for _ in range(3):  # retry on rate limit / overload
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts)
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code not in (429, 503):
                break
            time.sleep(1)
        except Exception as e:
            last = str(e)
            break
    raise RuntimeError(last)


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        t0 = time.time()
        try:
            n = int(self.headers.get("Content-Length", 0))
            prompt = json.loads(self.rfile.read(n))["prompt"]
            out, status = {"text": ask_gemini(prompt)}, 200
        except Exception as e:
            out, status = {"error": str(e)}, 502
        payload = json.dumps(out).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
        _log(f"{status} in {time.time() - t0:.1f}s")

    def log_message(self, *args):
        pass  # keep the default stderr logging quiet


def _start_server():
    global _server
    if _server is not None:
        return
    _load_config()
    port = int(_cfg.get("port", 8787))
    try:
        _server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    except OSError as e:
        tooltip(f"Gemini relay could not start on port {port}: {e}", period=8000)
        return
    threading.Thread(target=_server.serve_forever, daemon=True).start()
    if not (_cfg.get("gemini_api_key") or "").strip():
        tooltip("Gemini relay: set your API key under Tools > Add-ons > Config",
                period=8000)


gui_hooks.profile_did_open.append(_start_server)
mw.addonManager.setConfigUpdatedAction(ADDON, lambda _new: _load_config())