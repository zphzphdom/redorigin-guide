# -*- coding: utf-8 -*-
"""本地 Mock DeepSeek API，用于在没有真实 key 时验证接入链路。

启动：python tools/mock_deepseek.py --port 8899
覆盖：
  POST /chat/completions   返回一段带 [S1] 引用的中文回答
  POST /v1/tools/search    返回 3 条带日期/站点/URL 的结果
  POST /v1/tools/fetch     返回 Markdown 正文
特殊行为（便于测试护栏）：
  query 含 "幻觉测试" 时，chat 返回含资料外大数字的文本（预期被回退）
  query 含 "报错测试" 时，chat 返回 HTTP 500（预期触发重试后回退）
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CALLS = {"chat": 0, "search": 0, "fetch": 0}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
        except Exception:
            payload = {}
        text = json.dumps(payload, ensure_ascii=False)

        if self.path.endswith("/chat/completions"):
            CALLS["chat"] += 1
            if "报错测试" in text:
                self._json({"error": {"message": "mock upstream error"}}, 500)
                return
            if "幻觉测试" in text:
                content = "延安去年接待游客 99999 万人次，同比增长 38.7%。[S1]"
            else:
                content = ("延安革命纪念馆 1950 年建馆，馆藏文物 3.5 万余件，是延安革命纪念地景区（5A）核心景点之一。[S1] "
                           "门票免费，开放时间以官方当日公告为准。[S1]")
            self._json({"choices": [{"message": {"role": "assistant", "content": content}}]})
            return

        if self.path.endswith("/v1/tools/search"):
            CALLS["search"] += 1
            q = payload.get("query", "")
            self._json({"results": [
                {"rerank_score": 2.6, "title": "延安市 2026 年国庆假期文旅数据发布",
                 "url": "https://example.gov.cn/yanan/2026-10-08", "site_name": "延安市人民政府",
                 "snippet": "假期接待游客同比增长，重点景区实行预约限流。",
                 "summary": "延安市文旅局发布假期数据：重点景区实行分时预约，宝塔山、杨家岭等实施限流。",
                 "date": "2026-10-08T00:00:00+00:00", "authority": 3, "content": ""},
                {"rerank_score": 2.1, "title": "西延高铁增开周末列车",
                 "url": "https://example.com/rail/2026-10-20", "site_name": "铁路12306",
                 "snippet": "周末增开西安北—延安动车组列车。",
                 "summary": "为应对周末客流，西延高铁增开 4 对动车组，具体以 12306 为准。",
                 "date": "2026-10-20T00:00:00+00:00", "authority": 2, "content": ""},
                {"rerank_score": 1.8, "title": "洛川苹果采收季启动",
                 "url": "https://example.com/apple/2026-10-15", "site_name": "陕西日报",
                 "snippet": "洛川苹果进入采收期。",
                 "summary": "洛川县苹果进入采收期，合作社开启线上销售。",
                 "date": "2026-10-15T00:00:00+00:00", "authority": 2, "content": ""},
            ][: int(payload.get("count") or 3)]})
            return

        if self.path.endswith("/v1/tools/fetch"):
            CALLS["fetch"] += 1
            self._json({"title": "Mock 页面", "content": "# Mock\n\n正文内容。"})
            return

        self._json({"error": "not found"}, 404)

    def do_GET(self):
        if self.path == "/stats":
            self._json(CALLS)
            return
        self._json({"ok": True})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8899)
    args = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"mock DeepSeek API on http://127.0.0.1:{args.port}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
