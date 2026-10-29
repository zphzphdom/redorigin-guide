# -*- coding: utf-8 -*-
"""红源智导 · 检索与理解核心（零第三方依赖）

包含：
- 中文按字二元组（bigram）切分 + BM25 检索
- 意图识别（规则打分 + 上下文继承）
- 事实型回答组装（强制附带来源与时效标注）
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

PUNCT_RE = re.compile(r"[\s\u3000-\u303f\uff00-\uff0f\uff1a-\uff20\uff3b-\uff40\uff5b-\uff65"
                      r"!-/:-@\[-`{-~，。！？；：“”‘’、（）《》【】…—·]+")


def clean(text: str) -> str:
    return PUNCT_RE.sub(" ", text or "")


def tokens(text: str) -> list[str]:
    """中文 bigram + 英文/数字整词。"""
    out: list[str] = []
    for seg in clean(text).split():
        if not seg:
            continue
        if re.fullmatch(r"[A-Za-z0-9%.\-]+", seg):
            out.append(seg.lower())
            continue
        chars = list(seg)
        if len(chars) == 1:
            out.append(chars[0])
            continue
        for i in range(len(chars) - 1):
            out.append(chars[i] + chars[i + 1])
    return out


@dataclass
class Doc:
    id: str
    category: str
    title: str
    text: str
    keywords: list[str]
    source: dict[str, str]
    extra: dict[str, Any] = field(default_factory=dict)
    _tf: dict[str, int] = field(default_factory=dict, repr=False)
    _len: int = 0

    def build(self) -> "Doc":
        bag = tokens(self.title) * 3 + tokens(" ".join(self.keywords)) * 2 + tokens(self.text)
        for t in bag:
            self._tf[t] = self._tf.get(t, 0) + 1
        self._len = len(bag)
        return self


class KB:
    def __init__(self, path: Path | None = None):
        self.docs: list[Doc] = []
        self.by_id: dict[str, Doc] = {}
        self.load(path or (DATA_DIR / "kb.json"))

    def load(self, path: Path) -> None:
        raw = json.loads(path.read_text(encoding="utf-8"))
        for item in raw:
            d = Doc(
                id=item["id"], category=item["category"], title=item["title"],
                text=item["text"], keywords=item.get("keywords", []),
                source=item.get("source", {}), extra=item.get("extra", {}),
            ).build()
            self.docs.append(d)
            self.by_id[d.id] = d
        self._index()

    def _index(self) -> None:
        self.df: dict[str, int] = {}
        self.avgdl = sum(d._len for d in self.docs) / max(1, len(self.docs))
        for d in self.docs:
            for t in d._tf:
                self.df[t] = self.df.get(t, 0) + 1
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - v + 0.5) / (v + 0.5)) for t, v in self.df.items()}

    def search(self, query: str, k: int = 4, category: str | None = None) -> list[tuple[Doc, float]]:
        q_terms = tokens(query)
        if not q_terms:
            return []
        k1, b = 1.5, 0.75
        scored: list[tuple[Doc, float]] = []
        for d in self.docs:
            if category and d.category != category:
                continue
            s = 0.0
            for t in q_terms:
                tf = d._tf.get(t, 0)
                if not tf:
                    continue
                idf = self.idf.get(t, 0.0)
                s += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * d._len / self.avgdl))
            if s > 0:
                scored.append((d, s))
        scored.sort(key=lambda x: -x[1])
        return scored[:k]

    def get(self, doc_id: str) -> Doc | None:
        return self.by_id.get(doc_id)


INTENT_RULES: dict[str, list[tuple[str, int]]] = {
    "route": [("行程", 4), ("路线", 4), ("怎么玩", 4), ("规划", 3), ("几天", 3), ("一日", 3),
              ("两日", 3), ("三日", 3), ("安排", 2), ("攻略", 2), ("带父母", 2), ("带孩子", 2),
              ("研学", 2), ("自驾", 2), ("怎么走", 3)],
    "spot": [("介绍", 3), ("讲解", 3), ("是什么", 2), ("历史", 2), ("旧址", 3), ("纪念馆", 3),
             ("宝塔", 3), ("枣园", 3), ("杨家岭", 3), ("南泥湾", 3), ("壶口", 3), ("梁家河", 3),
             ("黄帝陵", 3), ("看点", 3), ("值不值得", 2)],
    "product": [("苹果", 3), ("小米", 2), ("红枣", 3), ("核桃", 2), ("花椒", 2), ("特产", 3),
                ("农产品", 3), ("买什么", 3), ("伴手礼", 3), ("地理标志", 3), ("品牌", 2),
                ("洛川", 3), ("助农", 3), ("合作社", 3), ("黄酒", 3), ("粉条", 3), ("蜂蜜", 3),
                ("荞麦醋", 3), ("豆腐", 2)],
    "ip": [("文案", 4), ("直播", 4), ("话术", 4), ("脚本", 4), ("短视频", 4), ("宣传", 3),
           ("卖点", 3), ("包装", 2), ("推广", 3), ("营销", 3), ("IP", 3), ("写一段", 3),
           ("朋友圈", 3), ("详情页", 3), ("采购", 3), ("企业", 2), ("介绍给", 3)],
    "policy": [("政策", 3), ("文件", 2), ("振兴", 3), ("支持", 2), ("国发", 3), ("规划", 2),
               ("行动", 2), ("革命老区", 2), ("补贴", 3), ("申请", 2), ("地理标志", 3)],
    "service": [("门票", 4), ("票价", 4), ("开放时间", 4), ("几点", 4), ("预约", 4), ("停车", 3),
                ("电话", 3), ("天气", 4), ("住宿", 3), ("酒店", 3), ("高铁", 4), ("机场", 3),
                ("怎么去", 3), ("交通", 2), ("厕所", 3), ("轮椅", 4), ("无障碍", 4), ("母婴", 3),
                ("寄存", 3), ("开门", 4), ("闭馆", 4), ("营业", 3), ("今天", 2), ("明天", 2)],
    "data": [("数据", 2), ("多少", 2), ("统计", 2), ("人次", 3), ("收入", 2), ("产值", 3),
             ("产量", 3), ("品牌价值", 4), ("GDP", 3)],
    "recommend": [("必去", 4), ("推荐", 3), ("好玩", 4), ("哪些景点", 4), ("值得去", 3),
                  ("有什么景点", 4), ("玩什么", 4), ("打卡", 3), ("经典", 2)],
    "about": [("你是谁", 4), ("你能做什么", 4), ("怎么用", 3), ("介绍一下你", 4), ("帮助", 2),
              ("功能", 3)],
}

GREETING_WORDS = ("你好", "您好", "hi", "hello", "在吗", "早上好", "下午好", "晚上好")


def detect_intent(text: str, ctx: dict[str, Any] | None = None) -> tuple[str, dict[str, int]]:
    t = text.strip()
    low = t.lower()
    if t and any(low == g or low.startswith(g) for g in GREETING_WORDS) and len(t) <= 8:
        return "greeting", {"greeting": 5}
    scores: dict[str, int] = {}
    for intent, rules in INTENT_RULES.items():
        s = sum(w for kw, w in rules if kw.lower() in low)
        if s:
            scores[intent] = s
    if not scores:
        # 指代继承：上一轮话题
        if ctx and ctx.get("last_entity"):
            return "followup", {"followup": 1}
        return "unknown", {}
    # 门票/时间等实时问题优先走服务边界
    best = max(scores, key=lambda k: scores[k])
    if "service" in scores and scores["service"] >= 3 and best != "route":
        return "service", scores
    # 数据型提问若同时指向具体农产品，按农产品处理（更贴近用户意图）
    if best == "data" and scores.get("product", 0) >= 3:
        return "product", scores
    return best, scores


@dataclass
class Reply:
    intent: str
    text: str
    sources: list[dict[str, str]] = field(default_factory=list)
    cards: list[dict[str, Any]] = field(default_factory=list)
    trace: dict[str, Any] = field(default_factory=dict)
    followups: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent, "text": self.text, "sources": self.sources,
            "cards": self.cards, "trace": self.trace, "followups": self.followups,
        }


def cite(source: dict[str, str]) -> str:
    name = source.get("name", "公开资料")
    doc = source.get("doc", "")
    date = source.get("date", "")
    bits = [name]
    if doc:
        bits.append(f"《{doc}》")
    if date:
        bits.append(date)
    return "·".join(bits)
