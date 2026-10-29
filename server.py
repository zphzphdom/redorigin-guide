# -*- coding: utf-8 -*-
"""红源智导 · 本地服务（标准库实现，无第三方依赖）

启动：python run.py --port 8770
默认账号见 users.json（由 tools/make_users.py 生成，密码以哈希存储）。
"""
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import secrets
import threading
import time
from collections import Counter
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from agent.config import VERSION
from agent.ipwriter import BANNED, build_copy, list_products
from agent.planner import plan
from agent.respond import Agent

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
DATA = ROOT / "data"
USERS = DATA / "users.json"
USAGE = DATA / "usage.jsonl"

agent = Agent()
sessions: dict[str, dict] = {}
chat_memory: dict[str, dict] = {}
rate_bucket: dict[str, list[float]] = {}
lock = threading.Lock()
START_TS = time.time()


def load_users() -> dict[str, dict]:
    raw = json.loads(USERS.read_text(encoding="utf-8"))
    return {u["username"]: u for u in raw["users"]}


def verify(username: str, password: str) -> dict | None:
    users = load_users()
    u = users.get(username)
    if not u:
        return None
    calc = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(u["salt"]), u["iterations"])
    if secrets.compare_digest(calc.hex(), u["hash"]):
        return {"username": u["username"], "display": u.get("display", u["username"]), "role": u.get("role", "user")}
    return None


def new_session(user: dict) -> str:
    token = secrets.token_urlsafe(24)
    with lock:
        sessions[token] = {"user": user, "exp": time.time() + 8 * 3600}
    return token


def auth(header: str | None) -> dict | None:
    if not header or not header.startswith("Bearer "):
        return None
    token = header[7:].strip()
    with lock:
        s = sessions.get(token)
    if not s or s["exp"] < time.time():
        return None
    return s["user"]


def allow(ip: str, limit: int = 40, window: float = 60.0) -> bool:
    now = time.time()
    with lock:
        arr = [t for t in rate_bucket.get(ip, []) if now - t < window]
        if len(arr) >= limit:
            rate_bucket[ip] = arr
            return False
        arr.append(now)
        rate_bucket[ip] = arr
    return True


def log_event(rec: dict) -> None:
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), **rec}
    with lock:
        with USAGE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read_usage() -> list[dict]:
    if not USAGE.exists():
        return []
    out = []
    for line in USAGE.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


class Handler(BaseHTTPRequestHandler):
    server_version = "HongYuanZhiDao/1.0"
    protocol_version = "HTTP/1.1"

    # ---------- 基础 ----------
    def _json(self, obj, code: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self._json({"error": "not found"}, 404)
            return
        body = path.read_bytes()
        ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        if path.suffix in (".html", ".css", ".js", ".svg", ".json"):
            ctype += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    def log_message(self, fmt, *args):  # 静默默认日志
        pass

    # ---------- 路由 ----------
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/", "/index.html"):
            self._file(WEB / "index.html")
            return
        if path == "/health":
            self._json({"ok": True, "uptime_s": int(time.time() - START_TS), "kb_docs": len(agent.kb.docs),
                        "mode": agent.cfg.mode, "search": agent.cfg.search_enabled, "version": VERSION})
            return
        if path == "/api/config":
            # 公开能力声明：只暴露模式与开关，不含任何密钥
            self._json(agent.cfg.public_dict())
            return
        if path == "/api/preview_token":
            # 默认关闭：反向隧道会让请求源地址变成 127.0.0.1，仅靠 IP 判断不可靠。
            # 只有显式设置 ALLOW_PREVIEW=1 时才启用（仅本地截图/演示用）。
            if os.environ.get("ALLOW_PREVIEW") != "1":
                self._json({"error": "disabled"}, 403)
                return
            if self.client_address[0] not in ("127.0.0.1", "::1"):
                self._json({"error": "forbidden"}, 403)
                return
            token = new_session({"username": "demo", "display": "演示预览", "role": "demo"})
            self._json({"token": token})
            return
        if path.startswith("/api/"):
            user = auth(self.headers.get("Authorization"))
            if not user:
                self._json({"error": "unauthorized"}, 401)
                return
            if path == "/api/products":
                self._json({"items": list_products()})
                return
            if path == "/api/spots":
                self._json({"items": agent.spots})
                return
            if path == "/api/admin/stats":
                # 运营看板只对 demo 账号开放；judge 账号不展示、不可访问
                if user.get("role") != "demo":
                    self._json({"error": "forbidden", "detail": "运营看板仅对 demo 账号开放"}, 403)
                    return
                self._admin_stats()
                return
            if path == "/api/kb/search":
                q = (parse_qs(parsed.query).get("q") or [""])[0]
                hits = agent.kb.search(q, k=5)
                self._json({"items": [{"id": d.id, "title": d.title, "text": d.text,
                                       "source": d.source, "score": round(s, 2)} for d, s in hits]})
                return
            self._json({"error": "not found"}, 404)
            return
        # 静态资源
        rel = path.lstrip("/")
        target = (WEB / rel).resolve()
        if not str(target).startswith(str(WEB.resolve())):
            self._json({"error": "forbidden"}, 403)
            return
        self._file(target)

    def _client_key(self) -> str:
        """限流键：反向隧道下所有请求都来自 127.0.0.1，改用 X-Forwarded-For 区分真实访客。"""
        xff = (self.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
        return xff or self.client_address[0]

    def do_POST(self):
        path = urlparse(self.path).path
        ip = self._client_key()
        if path == "/api/login":
            if not allow(ip, limit=12, window=60):
                self._json({"error": "请求过于频繁，请稍后再试"}, 429)
                return
            data = self._body()
            user = verify((data.get("username") or "").strip(), data.get("password") or "")
            if not user:
                self._json({"error": "账号或密码不正确"}, 401)
                return
            token = new_session(user)
            log_event({"event": "login", "user": user["username"]})
            self._json({"token": token, "user": user})
            return

        user = auth(self.headers.get("Authorization"))
        if not user:
            self._json({"error": "unauthorized"}, 401)
            return
        if not allow(ip):
            self._json({"error": "请求过于频繁"}, 429)
            return

        if path == "/api/chat":
            data = self._body()
            text = (data.get("message") or "").strip()
            if not text:
                self._json({"error": "消息为空"}, 400)
                return
            sid = data.get("session_id") or "anon"
            mem = chat_memory.setdefault(f"{user['username']}:{sid}", {})
            t0 = time.time()
            reply = agent.answer(text, mem)
            ms = int((time.time() - t0) * 1000)
            reply.trace["latency_ms"] = ms
            log_event({"event": "chat", "user": user["username"], "session": sid,
                       "message": text, "intent": reply.intent, "latency_ms": ms,
                       "sources": [s.get("name", "") for s in reply.sources]})
            self._json(reply.to_dict())
            return

        if path == "/api/plan":
            data = self._body()
            card = plan(int(data.get("days") or 2), data.get("theme") or "红色研学",
                        data.get("pace") or "标准")
            self._json(card)
            return

        if path == "/api/copy":
            data = self._body()
            self._json(build_copy(data.get("product") or "洛川苹果",
                                  data.get("channel") or "直播",
                                  data.get("audience") or "游客"))
            return

        if path == "/api/feedback":
            data = self._body()
            log_event({"event": "feedback", "user": user["username"],
                       "session": data.get("session_id"), "message": data.get("message"),
                       "intent": data.get("intent"), "helpful": bool(data.get("helpful")),
                       "reason": data.get("reason", "")})
            self._json({"ok": True})
            return

        self._json({"error": "not found"}, 404)

    def _admin_stats(self):
        rows = read_usage()
        chats = [r for r in rows if r.get("event") == "chat"]
        fb = [r for r in rows if r.get("event") == "feedback"]
        intents = Counter(r.get("intent", "-") for r in chats)
        lat = [r.get("latency_ms", 0) for r in chats] or [0]
        self._json({
            "total_chats": len(chats),
            "users": len({r.get("user") for r in chats}),
            "avg_latency_ms": int(sum(lat) / len(lat)),
            "intent_dist": intents.most_common(),
            "feedback": {"total": len(fb), "helpful": sum(1 for r in fb if r.get("helpful"))},
            "recent": [{"ts": r.get("ts"), "message": r.get("message"), "intent": r.get("intent")}
                       for r in chats[-8:]][::-1],
            "kb_docs": len(agent.kb.docs),
            "banned_terms": len(BANNED),
        })


def serve(port: int = 8770) -> None:
    httpd = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    cfg = agent.cfg
    cfg = agent.cfg
    print(f"红源智导已启动：http://127.0.0.1:{port}  （知识库 {len(agent.kb.docs)} 条）")
    print(f"生成模式：{cfg.mode}｜模型：{cfg.model if cfg.llm_enabled else '本地规则'}｜联网检索：{'开' if cfg.search_enabled else '关'}")
    print(f"生成模式：{cfg.mode}｜模型：{cfg.model if cfg.llm_enabled else '本地规则'}｜"
          f"联网检索：{'开' if cfg.search_enabled else '关'}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8770)))
    serve(ap.parse_args().port)
