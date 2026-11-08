"""Loopback-only local web panel. No external service or Ghost API is called."""
from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse
from . import core

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
MIME = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8"}

class Handler(BaseHTTPRequestHandler):
    server_version = "GhostMeshLocal/1.0"

    def log_message(self, fmt, *args):
        # Do not log prompts, note content, or request bodies.
        print("[mesh] " + (fmt % args).split("?")[0])

    def _json(self, status, value):
        data = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data))); self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(data)

    def _body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length < 0 or length > 16_384:
            raise ValueError("Päring on liiga suur")
        value = json.loads(self.rfile.read(length) or b"{}")
        if not isinstance(value, dict):
            raise ValueError("JSON peab olema objekt")
        return value

    def _allowed_origin(self):
        host = self.headers.get("Host", "").split(":", 1)[0].lower()
        if host not in {"127.0.0.1", "localhost", "::1"}:
            return False
        origin = self.headers.get("Origin")
        return not origin or origin in {"http://127.0.0.1:8765", "http://localhost:8765"}

    def do_GET(self):
        if not self._allowed_origin(): return self._json(403, {"error": "Ainult kohalik ühendus"})
        path = urlparse(self.path).path
        if path == "/api/state": return self._json(200, core.state())
        if path == "/api/notes": return self._json(200, {"notes": core.list_notes(), "archived": core.list_notes(True) if False else []})
        if path == "/api/rules": return self._json(200, {"rules": core.get_rules()})
        if path == "/": path = "/index.html"
        file = (STATIC / path.lstrip("/")).resolve()
        if STATIC.resolve() not in file.parents or not file.is_file(): return self._json(404, {"error": "Ei leitud"})
        data = file.read_bytes(); self.send_response(200)
        self.send_header("Content-Type", MIME.get(file.suffix, "application/octet-stream")); self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff"); self.end_headers(); self.wfile.write(data)

    def do_POST(self):
        if not self._allowed_origin(): return self._json(403, {"error": "Ainult kohalik ühendus"})
        try:
            body = self._body(); path = urlparse(self.path).path
            if path == "/api/think": result = core.think(body.get("prompt"))
            elif path == "/api/notes": result = {"note": core.create_note(body.get("title"), body.get("body"), body.get("color", "blue"), body.get("size", 16), body.get("importance", 3), body.get("tags", []))}
            elif path == "/api/feedback": result = core.record_feedback(body.get("agent"), body.get("correction"))
            elif path == "/api/rules": result = {"rule": core.suggest_rule(body.get("body"))}
            else: return self._json(404, {"error": "Marsruuti pole"})
            return self._json(200, result)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return self._json(400, {"error": str(exc)})

    def do_PATCH(self):
        if not self._allowed_origin(): return self._json(403, {"error": "Ainult kohalik ühendus"})
        try:
            body = self._body(); path = urlparse(self.path).path.split("/")
            if len(path) == 4 and path[1] == "api" and path[2] == "notes":
                ok = core.archive_note(unquote(path[3]), bool(body.get("archived", True)))
            elif len(path) == 4 and path[1] == "api" and path[2] == "rules":
                ok = core.set_rule(unquote(path[3]), body.get("status", "pending"))
            else: return self._json(404, {"error": "Marsruuti pole"})
            return self._json(200 if ok else 404, {"ok": ok})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return self._json(400, {"error": str(exc)})

    def do_DELETE(self):
        if not self._allowed_origin(): return self._json(403, {"error": "Ainult kohalik ühendus"})
        parts = urlparse(self.path).path.split("/")
        if len(parts) != 4 or parts[1] != "api" or parts[2] != "notes": return self._json(404, {"error": "Marsruuti pole"})
        return self._json(200 if core.forget_note(unquote(parts[3])) else 404, {"ok": True})


def main():
    core.init_db()
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Ghost Mesh AI töötab ainult selles arvutis: http://127.0.0.1:8765")
    print("Peatamiseks vajuta Ctrl+C.")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__ == "__main__": main()
