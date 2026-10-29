# -*- coding: utf-8 -*-
"""回答编排：意图路由 → 检索/规划/文案 → 来源与时效标注 → 追问建议。"""
from __future__ import annotations

import re
import time
from typing import Any

from .config import VERSION, Config
from .core import KB, Reply, cite, detect_intent
from .deepseek_api import DeepSeek
from .ipwriter import build_copy, list_products, match_ip_request
from .planner import load_spots, plan

CN_NUM = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5}

TICKET_SOURCE = {
    "name": "延安市文化和旅游局",
    "doc": "延安市A级旅游景区基本信息表",
    "date": "2026-10-26",
    "url": "https://yanan.gov.cn/gk/fdzdgknr/shgy/wtly/wlyw/gsgg/2114647785526538241.html",
}

WELCOME = (
    "我是**红源智导**，服务革命老区延安的 AI 导览智能体。\n"
    "我能做四件事：\n"
    "1. 讲景点——宝塔山、杨家岭、枣园、延安革命纪念馆、南泥湾、壶口瀑布等，讲解均标注资料来源；\n"
    "2. 排行程——按 1–4 天、研学/亲子/银发/摄影等主题生成路线；\n"
    "3. 推农品——洛川苹果等老区特产的产地事实、买点与助农渠道；\n"
    "4. 写文案——把农产品卖点变成直播话术、短视频脚本、详情页文案，并做广告法合规检查。\n"
    "门票、开放时间、天气等实时信息我**不猜**，会告诉你官方查询入口。"
)

ABOUT = (
    f"**红源智导 {VERSION}** 是一个面向革命老区文旅与农产品推广的检索增强（RAG）智能体。\n"
    "· 知识来源：延安市政府统计公报、延安革命纪念地管理局、洛川县政府与陕西省果业中心等公开资料，逐条标注来源与时间；\n"
    "· 能力边界：不生成未收录的事实，不提供实时票价/天气/库存，不承诺疗效与收益；\n"
    "· 适用对象：来延游客、研学团队、果农与合作社、县域文旅运营方。\n"
    "可以直接问我「帮我安排延安两天红色研学」「介绍枣园」「给洛川苹果写一段直播话术」。"
)

SERVICE_TEMPLATE = (
    "关于「{topic}」的**实时信息我不掌握**，也不做猜测。\n"
    "原因：门票价格、开放时间、预约名额、天气与交通管制会随时调整，任何固定答案都可能误导出行。\n"
    "{official}"
    "我可以先提供这些稳定信息：\n{facts}"
    "需要的话，我可以按你的日期与人数排一版行程，到官方渠道核对时间即可。"
)

# —— 接入 DeepSeek API 后的生成约束（System Prompt）——
LLM_SYSTEM = (
    "你是“红源智导”，服务陕西延安革命老区的导览助手。必须遵守：\n"
    "1) 只能依据【资料】作答，不得引入资料之外的数字、日期、价格、人名；\n"
    "2) 每处关键事实后用 [S1] / [W1] 标注资料编号，最多 3 处；\n"
    "3) 资料不足就直说“知识库未收录”，不要猜；门票/开放时间等易变信息结尾提示“以官方当日公告为准”；\n"
    "4) 中文口语，先给结论再给依据，总长不超过 220 字；不要输出表格；\n"
    "5) 不要提“根据资料”“作为AI”之类的话，直接回答。"
)

REALTIME_WORDS = ("最新", "最近", "今年", "现在", "目前", "刚刚", "开通", "新增",
                  "变化", "实时", "天气", "客流", "今天", "明天", "票价", "公告")



class Agent:
    def __init__(self) -> None:
        self.kb = KB()
        self.spots = load_spots()
        self.spot_names = [s["name"] for s in self.spots]
        self.cfg = Config()
        self.ds = DeepSeek(self.cfg)
        self._web_cache: dict[str, tuple[float, list[dict]]] = {}
        self._llm_cache: dict[str, tuple[float, str]] = {}

    # ---------- 工具 ----------
    def _should_realtime(self, intent: str, text: str, docs_scored: list) -> bool:
        if not self.cfg.search_enabled:
            return False
        # 结构化输出（行程/文案/推荐）不需要联网，避免浪费检索次数与时延
        if intent in ("route", "ip", "recommend", "greeting", "about"):
            return False
        if intent in ("service", "transport"):
            return True
        if any(w in text for w in REALTIME_WORDS):
            return True
        if intent == "unknown" or not docs_scored or docs_scored[0][1] < 2.4:
            return True
        return False

    def _web(self, text: str, limit: int) -> list[dict]:
        # 5 分钟查询缓存：演示时同一问题重复问不再消耗检索次数
        now = time.time()
        hit = self._web_cache.get(text)
        if hit and now - hit[0] < 300:
            return hit[1]
        try:
            raw = self.ds.search(text, count=max(limit, 6), ori_question=text)
        except Exception:
            return []
        # 权威性过滤：优先 gov.cn / authority>=3，剔除营销站；不足 2 条时再放宽
        good = [w for w in raw if w.get("authority", -1) >= 3 or ".gov.cn" in w.get("url", "")]
        picked = (good or raw)[:limit]
        self._web_cache[text] = (now, picked)
        return picked

    def _compose_with_llm(self, question: str, docs: list, web: list, max_tokens: int = 320) -> str | None:
        if not self.cfg.llm_enabled:
            return None
        ctx = []
        # 只带最相关的 2 条知识 + 2 条实时结果，控制 prompt 长度以降低时延
        for i, d in enumerate(docs[:2], 1):
            ctx.append(f"[S{i}] {d.title}｜{cite(d.source)}\n{d.text[:260]}")
        for j, w in enumerate(web[:2], 1):
            body = (w.get("summary") or w.get("snippet") or "")[:220]
            ctx.append(f"[W{j}] {w.get('title', '')}｜{w.get('site', '')} {w.get('date', '')}\n{body}\nURL: {w.get('url', '')}")
        if not ctx:
            return None
        key = question + "|" + ",".join(d.id for d in docs[:2]) + "|" + ",".join(w.get("url", "") for w in web[:2])
        now = time.time()
        cached = self._llm_cache.get(key)
        if cached and now - cached[0] < 600:
            return cached[1]
        user = "【资料】\n" + "\n\n".join(ctx) + "\n\n【问题】" + question
        out = self.ds.chat(LLM_SYSTEM, user, max_tokens=max_tokens)
        if not out or len(out) < 12:
            return None
        # 轻量校验：不允许出现资料里没有的四位以上数字串（防幻觉）
        numbers = set(re.findall(r"\d+(?:\.\d+)?", "".join(ctx)))
        for n in re.findall(r"\d+(?:\.\d+)?", out):
            if len(n) >= 4 and n not in numbers:
                return None  # 出现资料外的大数字，判定为幻觉，回退本地答案
        self._llm_cache[key] = (now, out)
        return out

    def _web_block(self, web: list[dict], lead: str = "**联网补充（实时检索，未人工复核）**") -> str:
        lines = ["", "---", lead]
        for w in web[:3]:
            lines.append(f"- {w.get('title', '')}（{w.get('site', '')} {w.get('date', '')}）{w.get('url', '')}")
        lines.append("以上为实时检索结果，与知识库口径可能不同；以官方最新公告为准。")
        return "\n".join(lines)

    def _comment_with_llm(self, intent: str, question: str, context: str) -> str | None:
        """行程/文案的结构化结果不交给模型改，只让它补一段不重复的点评。"""
        if not self.cfg.llm_enabled:
            return None
        key = f"{intent}:{question}:{context[:80]}"
        now = time.time()
        cached = self._llm_cache.get(key)
        if cached and now - cached[0] < 600:
            return cached[1]
        if intent == "route":
            system = ("你是延安本地向导。用两句话、不超过 70 字，点评这份行程的节奏与注意事项，"
                      "不要复述站点名称与时间，不要编造车程或票价。")
        else:
            system = ("你是农产品品牌顾问。用两句话、不超过 70 字，给出这条推广文案的投放建议，"
                      "不要重复文案里的句子，不要承诺销量或价格。")
        out = self.ds.chat(system, f"问题：{question}\n\n已有内容摘要：{context}", max_tokens=140)
        if not out or len(out) < 10:
            return None
        out = out.strip().replace("\n", " ")
        self._llm_cache[key] = (now, out)
        return out

    def _dedupe_sources(self, sources: list[dict]) -> list[dict]:
        seen, out = set(), []
        for s in sources:
            key = s.get("url") or (s.get("name", ""), s.get("doc", ""))
            if key in seen:
                continue
            seen.add(key)
            out.append(s)
        return out

    @staticmethod
    def _dedupe_lines(text: str) -> str:
        """去掉连续重复行与重复的来源行，保证回答不重复。"""
        out, prev = [], None
        for line in text.split("\n"):
            key = line.strip()
            if key and key == prev:
                continue
            out.append(line)
            if key:
                prev = key
        return "\n".join(out)

    def _enrich(self, reply: Reply, question: str, intent: str, docs: list, docs_scored: list) -> None:
        """在本地答案基础上：按需联网检索，再决定是否用 DeepSeek 重写表达。"""
        web: list[dict] = []
        if self._should_realtime(intent, question, docs_scored):
            web = self._web(question, self.cfg.max_web_results)

        llm_used = False
        if web and intent in ("service", "transport"):
            # 实时信息：保留本地结构化答案，联网结果作为“补充”附后，避免模型改错价格
            reply.text += self._web_block(web)
        elif intent in ("route", "ip"):
            # 行程与文案的结构化结果保持不变，只追加一段不重复的 AI 点评
            context = ""
            if reply.cards:
                c0 = reply.cards[0]
                if c0.get("type") == "plan":
                    context = "；".join(
                        f"D{d['day']}:" + "、".join(s["name"] for s in d["stops"]) for d in c0.get("days", [])
                    )[:260]
                elif c0.get("type") == "product":
                    context = f"{c0.get('product', {}).get('name', '')} 的推广文案"
            context = context or question
            comment = self._comment_with_llm(intent, question, context)
            if comment:
                title = "路线说明" if intent == "route" else "投放建议"
                reply.text += f"\n\n**{title}**：{comment}"
                llm_used = True
        elif self.cfg.llm_enabled:
            out = self._compose_with_llm(question, docs, web)
            if out:
                reply.text = out
                llm_used = True
            elif web:
                if intent in ("unknown", "kb"):
                    reply.text = "知识库没有直接收录这个问题，下面是实时联网检索到的结果：" + self._web_block(web, lead="**实时检索结果（未人工复核）**")
                else:
                    reply.text += self._web_block(web)
        elif web:
            reply.text += self._web_block(web)

        if web:
            for w in web[:3]:
                reply.sources.append({"name": w.get("site") or "实时检索", "doc": w.get("title", ""),
                                      "date": w.get("date", ""), "url": w.get("url", "")})

        # 去重：来源按 URL / 名称+文件，正文去掉连续重复行，避免同一内容出现两次
        reply.sources = self._dedupe_sources(reply.sources)
        reply.text = self._dedupe_lines(reply.text)
        reply.followups = list(dict.fromkeys(reply.followups or []))[:4]

        reply.trace.update({
            "mode": "deepseek-api" if llm_used else "offline-rules",
            "model": self.cfg.model if llm_used else "local-bm25",
            "realtime": bool(web),
            "web_hits": len(web),
            "api_error": self.ds.last_error if (self.cfg.api_key and not llm_used and not web) else "",
        })

    def _find_spot(self, text: str) -> dict[str, Any] | None:
        for s in self.spots:
            if s["name"] in text or any(a in text for a in s.get("aliases", [])):
                return s
        return None

    def _parse_days(self, text: str) -> int:
        m = re.search(r"([1-5一二两三四五])\s*(天|日)", text)
        if m:
            return CN_NUM.get(m.group(1), 2)
        if "一日" in text or "一天" in text:
            return 1
        if "周末" in text:
            return 2
        return 2

    def _parse_theme(self, text: str) -> str:
        if any(k in text for k in ("孩子", "亲子", "小学", "家庭")):
            return "亲子家庭"
        if any(k in text for k in ("父母", "老人", "银发", "长辈")):
            return "银发慢游"
        if any(k in text for k in ("摄影", "拍照", "黄河", "壶口")):
            return "黄河摄影"
        if any(k in text for k in ("非遗", "民俗", "剪纸", "腰鼓", "安塞")):
            return "非遗民俗"
        return "红色研学"

    def _parse_pace(self, text: str) -> str:
        if any(k in text for k in ("轻松", "慢", "不赶", "老人")):
            return "轻松"
        if any(k in text for k in ("紧凑", "特种兵", "尽量多")):
            return "紧凑"
        return "标准"

    def _dedup_sources(self, docs: list) -> list[dict[str, str]]:
        seen, out = set(), []
        for d in docs:
            key = (d.source.get("name", ""), d.source.get("doc", ""))
            if key in seen:
                continue
            seen.add(key)
            out.append(d.source)
        return out

    def _followups(self, docs: list) -> list[str]:
        pool = [d.title for d in docs if d.category != "policy"]
        ideas = ["这些景点怎么串成两天行程", "洛川苹果有什么可核验的产地数据", "写一段洛川苹果的直播开场"]
        return (pool[:2] + ideas)[:4]

    # ---------- 主流程 ----------
    def answer(self, text: str, session: dict[str, Any]) -> Reply:
        t0 = time.time()
        intent, scores = detect_intent(text, session)
        docs: list = []
        docs_scored: list = []
        reply: Reply

        if intent == "greeting":
            reply = Reply("greeting", WELCOME, followups=["帮我安排延安两天红色研学", "介绍枣园", "洛川苹果直播话术"])

        elif intent == "about":
            reply = Reply("about", ABOUT, followups=["帮我安排延安两天红色研学", "延安有哪些必去的红色景点"])

        elif intent == "route":
            days = self._parse_days(text)
            theme = self._parse_theme(text)
            pace = self._parse_pace(text)
            card = plan(days, theme, pace)
            lines = [f"按**{card['title']}**排了一版，点位全部来自知识库，未收录的景点不会出现：", ""]
            for d in card["days"]:
                lines.append(f"**D{d['day']}｜{d['theme']}**")
                for s in d["stops"]:
                    lines.append(f"- {s['time']}　{s['name']}（{s['minutes']} 分钟）— {s['note']}")
                lines.append("")
            lines.append("说明：时长为建议估算，非官方时刻表；开放与预约以景区当日公告为准。")
            reply = Reply("route", "\n".join(lines), cards=[{"type": "plan", **card}],
                          followups=["把第二天换成壶口瀑布", "再给一版亲子轻松的", "这些地方要预约吗"])

        elif intent == "ip":
            name, channel, audience = match_ip_request(text)
            result = build_copy(name, channel, audience)
            if not result.get("ok"):
                reply = Reply("ip", result["reason"] + "\n可生成的产品：" + "、".join(result["available"]),
                              followups=["给洛川苹果写直播话术"])
            else:
                parts = [f"基于知识库事实，为**{result['product']['name']}**生成{channel}文案："]
                for b in result["blocks"]:
                    parts.append(f"\n**{b['label']}**\n{b['content']}")
                parts.append(f"\n**合规检查**：{'通过' if result['compliance']['pass'] else '命中风险词 ' + '、'.join(result['compliance']['hits'])}"
                             f"（{result['compliance']['rule']}）")
                parts.append(f"\n_{result['disclaimer']}_")
                reply = Reply("ip", "\n".join(parts),
                              sources=[result["product"]["source"]],
                              cards=[{"type": "product", "product": result["product"],
                                      "compliance": result["compliance"]}],
                              followups=["改成短视频分镜", "换成电商详情页文案", "洛川苹果有哪些可核验数据"])

        elif intent == "recommend":
            must = [s for s in self.spots if s.get("must")]
            lines = ["按**主题代表性 + 片区分布**，延安值得优先安排的是这些（点位信息均来自知识库）：", ""]
            for s in must:
                lines.append(f"- **{s['name']}**（{s.get('level', '')}）— {s.get('one_line', '')}")
            lines.append("")
            lines.append("它们分布在城区、南泥湾、延川、宜川、黄陵五个片区，一天跑完不现实；告诉我天数，我再排路线。")
            reply = Reply("recommend", "\n".join(lines),
                          cards=[{"type": "spot_list", "items": [
                              {"name": s["name"], "area": s["area"], "level": s.get("level", ""),
                               "one_line": s.get("one_line", "")} for s in must]}],
                          followups=["排一个两天行程", "介绍延安革命纪念馆", "壶口瀑布怎么安排"])

        elif intent == "product":
            docs = [d for d, _ in self.kb.search(text, k=4, category="product")] or \
                   [self.kb.get(i) for i in ("product_luochuan_apple",) if self.kb.get(i)]
            intro = "\n\n".join(f"**{d.title}**\n{d.text}" for d in docs)
            plist = "、".join(p["name"] for p in list_products())
            text_out = f"{intro}\n\n可生成推广文案的产品：{plist}。想直接写成直播/短视频/详情页文案，告诉我渠道即可。"
            reply = Reply("product", text_out, sources=self._dedup_sources(docs),
                          cards=[{"type": "product_list", "items": list_products()}],
                          followups=["写一段洛川苹果直播开场", "洛川苹果品牌价值是多少", "延安还有哪些地理标志农产品"])

        elif intent == "service":
            spot = self._find_spot(text)
            if spot is None and session.get("last_spot"):
                spot = next((s for s in self.spots if s["id"] == session["last_spot"]), None)
            transport = any(k in text for k in ("高铁", "机场", "怎么去", "交通", "动车", "火车"))
            docs_scored = self.kb.search(text, k=3, category="transport") if transport else []
            facility = any(k in text for k in ("轮椅", "无障碍", "厕所", "母婴", "寄存", "停车", "休息", "餐饮"))
            day_time = any(k in text for k in ("今天", "明天", "后天", "现在", "周末", "节假日", "开门", "闭馆", "营业"))
            if spot and facility:
                lines = [f"**{spot['name']}** 的无障碍与服务设施信息，知识库未收录，我不做推测。",
                         f"- 官方渠道：{spot['official']}",
                         f"- 建议直接咨询：{spot.get('phone') or '景区官方渠道'}",
                         "- 可先参考的稳定信息：门票与开放时间见下一条，历史与看点我可以完整讲解。"]
                reply = Reply("service", "\n".join(lines), sources=[TICKET_SOURCE],
                              followups=[f"{spot['name']}门票和开放时间", f"介绍{spot['name']}"])
            elif spot and day_time:
                lines = [f"**{spot['name']}**",
                         f"- 官方公示开放时间：{spot['open_time']}",
                         f"- 门票：{spot['ticket']}　预约：{spot['booking']}",
                         "- 但“明天是否正常开放、是否临时闭馆”属于实时信息，我不掌握；",
                         f"  请出发前查看官方渠道：{spot['official']}" + (f"，或致电 {spot['phone']}。" if spot.get("phone") else "。"),
                         "\n需要的话，我可以把这个点排进当天的行程。"]
                reply = Reply("service", "\n".join(lines), sources=[TICKET_SOURCE],
                              followups=[f"介绍{spot['name']}", "把明天的行程排一下", "还有哪些免费景点"])
            elif spot:
                lines = [f"**{spot['name']}** 的公开信息（延安市文化和旅游局《延安市A级旅游景区基本信息表》，2026-10-26）：",
                         f"- 门票：{spot['ticket']}",
                         f"- 开放时间：{spot['open_time']}",
                         f"- 预约：{spot['booking']}",
                         f"- 等级：{spot['level']}"]
                if spot.get("phone"):
                    lines.append(f"- 咨询电话：{spot['phone']}")
                lines.append("\n以上为官方表所列内容；节假日或临时调整，以景区当日公告为准。")
                reply = Reply("service", "\n".join(lines), sources=[TICKET_SOURCE],
                              followups=[f"介绍{spot['name']}", f"把{spot['name']}排进行程", "还有哪些免费景点"])
            elif docs_scored:
                docs = [d for d, _ in docs_scored]
                body = "\n\n".join(f"**{d.title}**\n{d.text}" for d in docs)
                reply = Reply("transport", body + "\n\n（班次、票价与运行图请以 12306 / 航司官方渠道当日查询为准。）",
                              sources=self._dedup_sources(docs),
                              followups=["延安市区怎么串景点", "帮我排两天行程"])
            else:
                reply = Reply("service", SERVICE_TEMPLATE.format(
                    topic="这项实时信息", official="",
                    facts="- 景点门票、开放时间、预约渠道与咨询电话我可以按官方公示回答；\n- 景区历史与看点可以完整讲解；\n"),
                    followups=["介绍宝塔山", "宝塔山门票和开放时间", "帮我排一版行程"])

        else:
            docs_scored = self.kb.search(text, k=4)
            if not docs_scored or docs_scored[0][1] < 2.0:
                reply = Reply("unknown",
                              "这个问题我没有足够的可靠资料，**不编造**。\n"
                              "可以换个问法，或从下面几个方向问我：\n"
                              "· 延安红色景点讲解（宝塔山/杨家岭/枣园/南泥湾…）\n"
                              "· 1–4 天行程规划\n· 洛川苹果等老区农产品的产地事实与推广文案\n· 革命老区振兴相关政策",
                              followups=["延安有哪些必去的红色景点", "介绍一下延安革命纪念馆", "洛川苹果品牌价值"])
            else:
                docs = [d for d, _ in docs_scored]
                primary = docs[0]
                body = [f"**{primary.title}**", primary.text]
                related_cats = {primary.category}
                if primary.category in ("spot", "history"):
                    related_cats |= {"spot", "history", "policy"}
                extra = [d for d in docs[1:] if d.category in related_cats][:2]
                if extra:
                    body.append("相关背景：")
                    for d in extra:
                        body.append(f"- **{d.title}**：{d.text}")
                if primary.extra.get("volatile"):
                    body.append("（该项信息可能调整，出行前请以官方公告为准。）")
                label = primary.category if primary.category in ("spot", "history", "policy", "transport", "product") else "kb"
                reply = Reply(label,
                              "\n\n".join(body), sources=self._dedup_sources(docs),
                              followups=self._followups(docs))

        # 上下文记忆
        spot = self._find_spot(text)
        if spot:
            session["last_entity"] = spot.get("kb_id", "")
            session["last_spot"] = spot.get("id")
        session["last_intent"] = reply.intent

        reply.trace = {
            "intent": reply.intent,
            "scores": scores,
            "retrieved": [{"id": d.id, "title": d.title, "score": round(s, 2)} for d, s in docs_scored],
            "mode": "offline-rules",
            "model": "local-bm25",
            "realtime": False,
            "web_hits": 0,
        }
        # DeepSeek API 增强（未配置 key 时自动跳过，行为与纯离线完全一致）
        try:
            self._enrich(reply, text, reply.intent, docs, docs_scored)
        except Exception as e:  # 外部接口异常不得影响主流程
            reply.trace["api_error"] = f"{type(e).__name__}: {e}"
        reply.trace["latency_ms"] = int((time.time() - t0) * 1000)
        return reply
