# -*- coding: utf-8 -*-
"""行程规划：基于结构化点位知识 + 片区聚类 + 节奏约束。

设计原则：
1. 只使用知识库中真实存在的点位，不虚构景点；
2. 时长/转场为"建议估算"，输出时明确标注，不冒充官方时刻表；
3. 按片区就近成团，避免同日在延安全市往返穿插。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

AREA_ORDER = ["城区", "南泥湾", "安塞", "延川", "宜川", "洛川", "黄陵", "子长", "志丹", "吴起"]

AREA_LABEL = {
    "城区": "宝塔区·城区（革命旧址群）",
    "南泥湾": "宝塔区·南泥湾",
    "延川": "延川县（梁家河·乾坤湾）",
    "宜川": "宜川县（壶口瀑布）",
    "黄陵": "黄陵县（黄帝陵）",
    "安塞": "安塞区（民间艺术）",
    "洛川": "洛川县（洛川会议·苹果）",
    "子长": "子长市（瓦窑堡）",
    "志丹": "志丹县（刘志丹烈士陵园）",
    "吴起": "吴起县（长征胜利纪念园）",
}

PACE = {"轻松": 3, "标准": 4, "紧凑": 5}


def load_spots() -> list[dict[str, Any]]:
    return json.loads((DATA_DIR / "spots.json").read_text(encoding="utf-8"))


def _fmt(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h:02d}:{m:02d}"


def plan(days: int, theme: str = "红色研学", pace: str = "标准") -> dict[str, Any]:
    spots = load_spots()
    per_day = PACE.get(pace, 4)
    days = max(1, min(days, 4))

    # 主题权重
    theme_tags = {
        "红色研学": {"红色", "旧址", "纪念馆", "研学"},
        "亲子家庭": {"亲子", "体验", "自然", "夜景"},
        "银发慢游": {"红色", "旧址", "纪念馆", "轻松"},
        "黄河摄影": {"自然", "摄影", "黄河"},
        "非遗民俗": {"非遗", "民俗", "体验"},
    }.get(theme, {"红色"})

    by_area: dict[str, list[dict[str, Any]]] = {}
    for s in spots:
        by_area.setdefault(s["area"], []).append(s)

    # 片区内的动线顺序由 order 字段人工编排（已按地理位置与参观节奏排好）
    for area, items in by_area.items():
        items.sort(key=lambda s: s.get("order", 99))

    # 选片区：第1天固定城区；之后按主题覆盖
    selected: list[str] = []
    if "城区" in by_area:
        selected.append("城区")
    rest = [a for a in AREA_ORDER if a in by_area and a != "城区"]
    if theme == "黄河摄影":
        rest = [a for a in ["宜川", "延川", "黄陵"] if a in rest] + [a for a in rest if a not in {"宜川", "延川", "黄陵"}]
    elif theme == "非遗民俗":
        rest = [a for a in ["安塞", "延川", "南泥湾"] if a in rest] + [a for a in rest if a not in {"安塞", "延川", "南泥湾"}]
    elif theme == "亲子家庭":
        rest = [a for a in ["南泥湾", "延川", "宜川"] if a in rest] + [a for a in rest if a not in {"南泥湾", "延川", "宜川"}]
    else:
        rest = [a for a in ["宜川", "延川", "安塞", "洛川", "黄陵", "子长", "志丹", "吴起"] if a in rest]
    selected += rest

    day_plans: list[dict[str, Any]] = []
    area_cursor = 0
    for d in range(days):
        areas_today = [selected[min(area_cursor, len(selected) - 1)]]
        area_cursor += 1
        stops_raw: list[dict[str, Any]] = []
        for a in areas_today:
            stops_raw.extend(by_area.get(a, [])[:per_day])
        # 城区第一天加一个晚间点位
        stops: list[dict[str, Any]] = []
        clock = 8 * 60 + 30
        lunch_done = False
        for i, s in enumerate(stops_raw):
            dur = int(s.get("minutes", 60))
            if not lunch_done and 11 * 60 + 30 <= clock <= 13 * 60 + 30 and i < len(stops_raw) - 1:
                stops.append({
                    "time": f"{_fmt(clock)}–{_fmt(clock + 60)}",
                    "name": "午餐 · 陕北风味（自理）",
                    "area": AREA_LABEL.get(areas_today[0], areas_today[0]),
                    "minutes": 60,
                    "note": "羊肉面、洋芋擦擦、黄馍馍等本地主食，就餐点自行选择",
                    "level": "",
                })
                clock += 60
                lunch_done = True
            stops.append({
                "time": f"{_fmt(clock)}–{_fmt(clock + dur)}",
                "name": s["name"],
                "area": AREA_LABEL.get(s["area"], s["area"]),
                "minutes": dur,
                "note": s.get("one_line", ""),
                "level": s.get("level", ""),
            })
            clock += dur
            if i < len(stops_raw) - 1:
                clock += 40  # 转场缓冲（估算）
            if clock > 17 * 60 + 30 and i < len(stops_raw) - 1:
                clock = 14 * 60  # 午后继续，晚饭前收束
        if len(stops_raw) <= 2:
            stops.append({
                "time": "其余时间",
                "name": "片区自由活动 / 返程",
                "area": AREA_LABEL.get(areas_today[0], areas_today[0]),
                "minutes": 0,
                "note": "该片区已核验点位较少，可安排民俗体验或返程，不虚构景点凑数",
                "level": "",
            })
        day_plans.append({
            "day": d + 1,
            "theme": f"{theme}·{AREA_LABEL.get(areas_today[0], areas_today[0])}",
            "stops": stops,
        })

    return {
        "title": f"{days}日{theme}路线（{pace}节奏）",
        "days": day_plans,
        "notes": [
            "游览时长为建议估算值，非官方时刻表；开放时间与预约要求请以景区当日公告为准。",
            "同一天的景点均在同一片区，减少往返；跨县区建议预留整段车程。",
            "行程由知识库点位生成，未收录的景点不会出现在路线中。",
        ],
    }
