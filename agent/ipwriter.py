# -*- coding: utf-8 -*-
"""农产品 IP 内容工厂 + 广告法合规检查。

所有事实槽位来自 data/products.json（每条均带来源），模板只负责组织语言，
不引入知识库之外的数字、荣誉或功效表述。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# 《广告法》第九条相关绝对化用语 + 常见违规表述（示例集，可扩展）
BANNED = [
    "国家级", "最高级", "最佳", "最好", "最优", "最强", "第一品牌", "全网第一", "销量第一",
    "绝无仅有", "独一无二", "史上最低", "最便宜", "顶级", "极品", "王牌", "冠军",
    "纯天然", "无任何副作用", "包治", "治疗", "降血压", "降血糖", "抗癌", "增强免疫力",
    "100%", "永久", "万能",
]


def load_products() -> list[dict[str, Any]]:
    return json.loads((DATA_DIR / "products.json").read_text(encoding="utf-8"))


def find_product(name: str) -> dict[str, Any] | None:
    """按匹配长度取最优：完整产品名优先于泛化别名（如“苹果”），避免把延安苹果认成洛川苹果。"""
    best, best_score = None, 0
    for p in load_products():
        score = 0
        if p["name"] in name:
            score = 100 + len(p["name"])
        else:
            for a in p.get("aliases", []):
                if a in name:
                    score = max(score, len(a))
        if score > best_score:
            best, best_score = p, score
    return best


def compliance_check(text: str) -> dict[str, Any]:
    hits = [w for w in BANNED if w in text]
    return {
        "pass": not hits,
        "hits": hits,
        "rule": "《中华人民共和国广告法》第九条、第二十八条（绝对化用语与虚假宣传风险）",
        "advice": "已命中高风险表述，建议改为可验证的事实描述（如产地、品种、检测指标、获奖年份）。"
        if hits else "未命中绝对化用语词表；仍建议投放前由人工复核事实与授权。",
    }


def _fact(p: dict[str, Any], key: str, default: str = "") -> str:
    v = p.get("facts", {}).get(key)
    return str(v) if v else default


def build_copy(product_name: str, channel: str = "直播", audience: str = "游客") -> dict[str, Any]:
    p = find_product(product_name)
    if not p:
        return {"ok": False, "reason": f"知识库未收录「{product_name}」，为避免编造，暂不生成。",
                "available": [x["name"] for x in load_products()]}

    name = p["name"]
    origin = _fact(p, "origin", p.get("region", ""))
    gi = _fact(p, "gi", "地理标志信息待补充")
    area = _fact(p, "area", "")
    output = _fact(p, "output", "")
    value = _fact(p, "brand_value", "")
    output_value = _fact(p, "value", "")
    value_label = "" if output_value.startswith("产值") else "产值"
    value_phrase = (value_label + output_value + "，") if output_value else ""
    taste = _fact(p, "taste", "")
    story = _fact(p, "story", "")

    blocks: list[tuple[str, str]] = []
    blocks.append(("品牌主张", f"{name}：把黄土高原的阳光，装进一颗果子。" if "苹果" in name
                   else f"{name}：老区水土养出来的实在味道。"))
    blocks.append(("一句话介绍", f"{name}产自{origin}。{('种植面积' + area + '，' ) if area else ''}"
                                f"{('年产量' + output + '，') if output else ''}"
                                f"{value_phrase}"
                                f"{('品牌价值' + value + '。') if value else ''}{gi}。"))
    blocks.append(("三条卖点", "\n".join([
        f"1. 产地可核验：{origin}，{gi}。",
        f"2. 品质有据：{taste}。" if taste else "2. 品质描述以官方检测与分级标准为准。",
        f"3. 助农可追溯：{story}" if story else "3. 支持产地直发，合作社与农户信息可在包装溯源码查询。",
    ])))

    if channel == "直播":
        blocks.append(("30 秒直播开场", (
            f"家人们，今天这款{name}，产地是{origin}。"
            f"{('它的种植面积是' + area + '，') if area else ''}"
            f"{('年产量' + output + '，') if output else ''}"
            f"这些数字都写在产地公开资料里，我不夸大。"
            f"{('口感上，' + taste + '。') if taste else ''}"
            f"想尝鲜的，先看溯源信息，再决定买不买。")))
    elif channel == "短视频":
        blocks.append(("短视频分镜（15 秒）", (
            "镜头1（0-3s）：果园仰拍，字幕「黄土高原，海拔千米以上的日照」；\n"
            f"镜头2（4-9s）：切开特写，字幕「{taste or '果肉细脆，汁水充足'}」；\n"
            f"镜头3（10-15s）：合作社打包现场，字幕「{origin} · 产地直发」＋溯源二维码。")))
    elif channel == "电商详情页":
        blocks.append(("详情页首屏", (
            f"主标题：{name}\n副标题：{origin} · {gi}\n"
            f"信任背书：{('品牌价值' + value + '；') if value else ''}"
            f"{('种植面积' + area + '；') if area else ''}{('年产量' + output + '。') if output else ''}")))
    else:
        blocks.append(("朋友圈文案", (
            f"从{origin}寄来的一箱{name}。{taste or ''}"
            f"{('这里的苹果种植面积有' + area + '，') if area else ''}每一颗都能查到产地。"
            "老区的果子，值得被更多人看见。")))

    if audience == "企业采购":
        blocks.append(("企业采购话术", (
            f"{name}可作为员工福利/商务礼赠：{gi}；"
            f"{('产地年产量' + output + '，') if output else ''}支持定制包装与产地溯源信息随箱。")))

    full_text = "\n".join(v for _, v in blocks)
    check = compliance_check(full_text)
    return {
        "ok": True,
        "product": {"name": name, "region": origin, "gi": gi, "source": p.get("source", {})},
        "blocks": [{"label": k, "content": v} for k, v in blocks],
        "compliance": check,
        "disclaimer": "文案由知识库事实槽位生成；投放前请核对授权、检测报告与最新价格，价格类信息本智能体不生成。",
    }


def match_ip_request(text: str) -> tuple[str, str, str]:
    channel = "直播"
    if "短视频" in text or "分镜" in text:
        channel = "短视频"
    elif "详情页" in text or "电商" in text:
        channel = "电商详情页"
    elif "朋友圈" in text:
        channel = "朋友圈"
    audience = "企业采购" if ("企业" in text or "采购" in text or "福利" in text) else "游客"
    prod = find_product(text)
    return (prod["name"] if prod else "洛川苹果"), channel, audience


def list_products() -> list[dict[str, str]]:
    return [{"name": p["name"], "region": p.get("region", ""), "gi": p.get("facts", {}).get("gi", "")}
            for p in load_products()]
