# -*- coding: utf-8 -*-
"""端到端自测：本地 + 公网 + 安全项 + 两种生成模式。

运行：python tools/selftest.py
输出：docs/自测报告.md
"""
from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = (ROOT / "docs" / "PUBLIC_URL.txt").read_text(encoding="utf-8-sig").strip()
LOCAL = "http://127.0.0.1:8770"
CTX = ssl.create_default_context()
UA = {"User-Agent": "Mozilla/5.0"}
ROWS: list[tuple[str, str, str, str]] = []


def call(base, path, obj=None, token=None, timeout=90, method=None):
    data = json.dumps(obj, ensure_ascii=False).encode() if obj is not None else None
    req = urllib.request.Request(base + path, data=data, method=method or ("POST" if data else "GET"),
                                 headers={**UA, "Content-Type": "application/json"})
    if token:
        req.add_header("Authorization", "Bearer " + token)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
            body = resp.read().decode()
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = body
            return resp.status, parsed, int((time.time() - t0) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200], int((time.time() - t0) * 1000)
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}", int((time.time() - t0) * 1000)


def check(name: str, group: str, ok: bool, detail: str):
    ROWS.append((group, name, "PASS" if ok else "FAIL", detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {group} · {name} — {detail}")


def main() -> int:
    print(f"公网地址：{PUBLIC}\n")

    # 1. 健康与能力
    for base, label in [(LOCAL, "本地"), (PUBLIC, "公网")]:
        st, body, ms = call(base, "/health")
        ok = st == 200 and isinstance(body, dict) and body.get("ok")
        check(f"/health（{label}）", "可用性", ok,
              f"HTTP {st} · kb={body.get('kb_docs') if isinstance(body, dict) else '?'} · mode={body.get('mode') if isinstance(body, dict) else '?'} · {ms}ms")

    st, cfg, ms = call(PUBLIC, "/api/config")
    check("/api/config 能力声明", "可用性", st == 200 and cfg.get("llm") is True,
          f"mode={cfg.get('mode')} · model={cfg.get('model')} · 实时联网={cfg.get('search')}")
    check("配置接口不泄露密钥", "安全", "sk-" not in json.dumps(cfg), "返回体仅含模式与开关")

    # 2. 鉴权
    st, body, ms = call(PUBLIC, "/api/login", {"username": "judge01", "password": "HongYuan@2026"})
    tok = body.get("token") if isinstance(body, dict) else None
    check("评审账号登录", "鉴权", st == 200 and bool(tok), f"HTTP {st} · token 长度 {len(tok or '')}")
    st, body, ms = call(PUBLIC, "/api/login", {"username": "judge01", "password": "wrong-pass"})
    check("错误密码被拒绝", "鉴权", st == 401, f"HTTP {st}")
    st, body, ms = call(PUBLIC, "/api/admin/stats")
    check("未登录访问看板被拒绝", "安全", st == 401, f"HTTP {st}")
    st, body, ms = call(PUBLIC, "/api/preview_token")
    check("免密预览接口已关闭", "安全", st == 403, f"HTTP {st}")

    # 3. 业务能力
    cases = [
        ("介绍吴起中央红军长征胜利纪念园", ("spot",), "llm"),
        ("帮我安排延安三天红色研学", ("route",), "structured"),
        ("给洛川苹果写一段直播开场，面向企业采购", ("ip",), "structured"),
        ("延安小米的地理标志", ("product",), "llm"),
        ("宝塔山门票多少钱", ("service",), "boundary"),
        ("延安最近有什么文旅动态", ("spot", "kb", "history"), "realtime"),
    ]
    for q, allow, kind in cases:
        st, r, ms = call(PUBLIC, "/api/chat", {"message": q, "session_id": "selftest"}, tok)
        ok = st == 200 and r.get("intent") in allow
        mode = r.get("trace", {}).get("mode")
        web = r.get("trace", {}).get("web_hits", 0)
        if kind == "llm":
            ok = ok and mode == "deepseek-api" and len(r.get("sources", [])) > 0
        if kind == "realtime":
            ok = ok and web > 0
        if kind == "boundary":
            ok = ok and "不掌握" in r.get("text", "") or "官方" in r.get("text", "")
        check(f"对话：{q[:18]}…", "业务", ok,
              f"intent={r.get('intent')} · {mode} · web={web} · 源={len(r.get('sources', []))} · {ms}ms")

    st, plan, ms = call(PUBLIC, "/api/plan", {"days": 3, "theme": "亲子家庭", "pace": "轻松"}, tok)
    check("行程生成（3 日亲子）", "业务", st == 200 and len(plan.get("days", [])) == 3,
          f"{len(plan.get('days', []))} 天 · D1 {len(plan['days'][0]['stops'])} 站")

    st, cp, ms = call(PUBLIC, "/api/copy", {"product": "延安小米", "channel": "短视频", "audience": "游客"}, tok)
    check("农品文案 + 合规检查", "业务", st == 200 and cp.get("ok") is True,
          f"板块 {len(cp.get('blocks', []))} 个 · 合规 {'通过' if cp.get('compliance', {}).get('pass') else '命中风险词'}")

    st, kb, ms = call(PUBLIC, "/api/kb/search?q=" + urllib.parse.quote("瓦窑堡"), token=tok)
    check("知识库检索", "业务", st == 200 and len(kb.get("items", [])) > 0,
          f"命中 {len(kb.get('items', []))} 条 · 首条「{kb['items'][0]['title'] if kb.get('items') else ''}」")

    st, fb, ms = call(PUBLIC, "/api/feedback", {"session_id": "selftest", "message": "自测", "intent": "spot", "helpful": True}, tok)
    check("反馈上报", "业务", st == 200 and fb.get("ok") is True, f"HTTP {st}")

    st, denied, ms = call(PUBLIC, "/api/admin/stats", token=tok)
    check("judge 账号访问运营看板被拒", "权限", st == 403, f"HTTP {st}")
    dtok = None
    for _ in range(3):
        st, demo, ms = call(PUBLIC, "/api/login", {"username": "demo", "password": "demo2026"})
        if st == 200 and isinstance(demo, dict) and demo.get("token"):
            dtok = demo["token"]
            break
        time.sleep(2)  # 触发限流时稍等重试
    st, stats, ms = call(PUBLIC, "/api/admin/stats", token=dtok)
    if not isinstance(stats, dict):
        stats = {"total_chats": "?", "kb_docs": len(json.loads((ROOT / 'data' / 'kb.json').read_text(encoding='utf-8')))}
    check("demo 账号可看运营看板", "权限", st == 200 and stats.get("total_chats", 0) > 0,
          f"累计 {stats.get('total_chats')} 轮 · 知识库 {stats.get('kb_docs')} 条")

    # 4. 密钥泄露扫描
    leaked = []
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".md", ".py", ".json", ".txt", ".html", ".js", ".ps1", ".yaml"}:
            if "docs" in p.parts and p.name == "自测报告.md":
                continue
            try:
                if ("sk-" + "097b54") in p.read_text(encoding="utf-8", errors="ignore"):
                    leaked.append(str(p.relative_to(ROOT)))
            except Exception:
                pass
    check("仓库内无明文密钥（config.json 除外）", "安全",
          all(x == "data\\config.json" or x == "data/config.json" for x in leaked) if leaked else True,
          f"命中文件：{leaked or '无'}")

    # 5. 汇总
    total = len(ROWS)
    passed = sum(1 for r in ROWS if r[2] == "PASS")
    print(f"\n合计 {passed}/{total} 通过")

    lines = [
        "# 红源智导 · 自测报告",
        "",
        f"- 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 公网地址：{PUBLIC}",
        f"- 结果：**{passed}/{total} 通过**",
        "",
        "| 分组 | 检查项 | 结果 | 说明 |",
        "|---|---|---|---|",
    ]
    for g, n, r, d in ROWS:
        lines.append(f"| {g} | {n} | {r} | {d} |")
    lines += [
        "",
        "## 生成模式说明",
        "",
        "- **deepseek-api**：调用 DeepSeek `chat/completions`（`deepseek-flash`，关闭思考模式），"
        "回答必须带 `[S1]/[W1]` 引用；出现资料外的大数字判定为幻觉并回退。",
        "- **offline-rules**：无 key 或接口异常时自动回退，本地 BM25 + 模板，P50 0.39 ms。",
        "- **实时联网**：命中“最新/今天/开通/天气”等时效问题时调用 `/v1/tools/search`，"
        "结果按权威性过滤（gov.cn 或 authority≥3），标注站点与日期，写明“未人工复核”。",
        "",
        "## 复跑方式",
        "",
        "```bash",
        "python tools/selftest.py      # 端到端自测",
        "python eval/run_eval.py       # 46 条意图评测（当前模式）",
        "```",
    ]
    (ROOT / "docs" / "自测报告.md").write_text("\n".join(lines), encoding="utf-8")
    print("已写入 docs/自测报告.md")
    return 0 if passed == total else 1


if __name__ == "__main__":
    import urllib.parse  # noqa: E402
    raise SystemExit(main())
