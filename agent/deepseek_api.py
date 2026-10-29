# -*- coding: utf-8 -*-
"""DeepSeek API 客户端（标准库 urllib，零第三方依赖）。

覆盖三个官方接口：
- POST /chat/completions  对话生成（OpenAI 兼容）
- POST /v1/tools/search   自研搜索引擎，按次计费
- POST /v1/tools/fetch    单页抓取为 Markdown

设计原则：任何失败都返回 None / []，由上层回退到本地规则，绝不因外部接口故障
导致整个智能体不可用。
"""
from __future__ import annotations

import http.client
import json
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

from .config import Config


class DeepSeek:
    def __init__(self, cfg: Config | None = None):
        self.cfg = cfg or Config()
        self.last_error = ""
        self._local = threading.local()
        self._lock = threading.Lock()
        self._shared = None
        u = urlparse(self.cfg.base_url)
        self._scheme = u.scheme or "https"
        self._host = u.hostname or "api.deepseek.com"
        self._port = u.port or (443 if self._scheme == "https" else 80)
        self._prefix = (u.path or "").rstrip("/")

    # ---------- 基础 ----------
    def _conn(self) -> http.client.HTTPConnection:
        """进程内共享一个长连接（低并发场景），把 TLS 握手从每次请求降到一次。"""
        if self._shared is None:
            cls = http.client.HTTPSConnection if self._scheme == "https" else http.client.HTTPConnection
            self._shared = cls(self._host, self._port, timeout=self.cfg.timeout)
        return self._shared

    def _reset(self) -> None:
        if self._shared is not None:
            try:
                self._shared.close()
            except Exception:
                pass
        self._shared = None

    def _post(self, path: str, payload: dict, timeout: float | None = None) -> dict | None:
        if not self.cfg.api_key:
            self.last_error = "no api key"
            return None
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Accept": "application/json",
        }
        for attempt in range(2):
            try:
                self._lock.acquire()
                conn = self._conn()
                conn.timeout = timeout or self.cfg.timeout
                conn.request("POST", self._prefix + path, body=body, headers=headers)
                resp = conn.getresponse()
                raw = resp.read()
                if resp.status != 200:
                    self.last_error = f"HTTP {resp.status}: {raw[:300].decode('utf-8', 'ignore')}"
                    self._reset()
                    if resp.status in (429, 500, 502, 503, 504) and attempt == 0:
                        time.sleep(1.2)
                        continue
                    return None
                return json.loads(raw.decode("utf-8"))
            except Exception as e:  # 超时、连接断开、DNS 等
                self.last_error = f"{type(e).__name__}: {e}"
                self._reset()
                if attempt == 0:
                    time.sleep(0.4)
                    continue
                return None
            finally:
                try:
                    self._lock.release()
                except Exception:
                    pass
        return None

    # ---------- 对话 ----------
    def chat(self, system: str, user: str, temperature: float = 0.2, max_tokens: int = 700) -> str | None:
        if not self.cfg.llm_enabled:
            return None
        payload = {
            "model": self.cfg.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            # 导览类回答不需要长链思考：关闭后更快、更省 token
            "thinking": {"type": "disabled"},
        }
        res = self._post("/chat/completions", payload, timeout=min(self.cfg.timeout, 16))
        if not res:
            return None
        try:
            return (res["choices"][0]["message"]["content"] or "").strip() or None
        except Exception:
            self.last_error = f"bad response: {str(res)[:200]}"
            return None

    # ---------- 联网检索 ----------
    @staticmethod
    def _clean_site(name: str) -> str:
        """官方接口有时把站点名返回成十六进制（如 79616e616e2e676f762e636e）。"""
        import re as _re
        if name and len(name) >= 6 and len(name) % 2 == 0 and _re.fullmatch(r"[0-9a-f]+", name):
            try:
                dec = bytes.fromhex(name).decode("utf-8")
                if dec.isprintable():
                    return dec
            except Exception:
                pass
        return name or ""

    def search(self, query: str, count: int = 4, need_content: bool = False,
               ori_question: str = "") -> list[dict]:
        if not self.cfg.search_enabled:
            return []
        payload = {"query": query[:128], "count": max(1, min(50, count)), "need_content": need_content}
        if ori_question:
            payload["ori_question"] = ori_question[:128]
        res = self._post("/v1/tools/search", payload)
        if not res:
            return []
        out = []
        for r in (res.get("results") or []):
            out.append({
                "title": r.get("title") or "",
                "url": r.get("url") or "",
                "snippet": r.get("snippet") or "",
                "summary": r.get("summary") or "",
                "content": r.get("content") or "",
                "site": self._clean_site(r.get("site_name") or ""),
                "date": (r.get("date") or "")[:10],
                "authority": r.get("authority", -1),
                "score": r.get("rerank_score", 0),
            })
        return out

    # ---------- 抓取 ----------
    def fetch(self, url: str) -> dict | None:
        if not self.cfg.search_enabled:
            return None
        res = self._post("/v1/tools/fetch", {"url": url})
        if not res:
            return None
        return {"title": res.get("title", ""), "content": res.get("content", "")}
