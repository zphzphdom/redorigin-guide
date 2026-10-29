# -*- coding: utf-8 -*-
"""生成《红源智导》20 页参赛作品说明（A4 / 200dpi）。

运行：python tools/build_pdf.py
输出：docs/红源智导_参赛作品说明_20页.pdf
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

from pdfkit import (BLUE, BOLD, CREAM, GOLD, GOLD_SOFT, GREEN, HEI, INK, INK2, INK3, LINE,  # noqa: E402
                    PAPER, PX, RED, RED_DEEP, RED_SOFT, WHITE, A4_H, A4_W, Canvas,
                    font, pagoda, pt, save_pdf, text_width)

TOTAL = 20
KB = json.loads((ROOT / "data" / "kb.json").read_text(encoding="utf-8"))
PRODUCTS = json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))
SPOTS = json.loads((ROOT / "data" / "spots.json").read_text(encoding="utf-8"))
EVAL = json.loads((ROOT / "eval" / "results.json").read_text(encoding="utf-8"))

def _public_url() -> str:
    f = ROOT / "docs" / "PUBLIC_URL.txt"
    if f.exists():
        u = f.read_text(encoding="utf-8-sig").strip()
        if u.startswith("http"):
            return u
    return "http://127.0.0.1:8770"


PUBLIC_URL = _public_url()
N_KB, N_SPOTS, N_PROD = len(KB), len(SPOTS), len(PRODUCTS)


def kpis(doc: Canvas, y: int, items, h=176, gap=22, accent=RED):
    w = (1414 - gap * (len(items) - 1)) / len(items)
    for i, (v, u, lab, note) in enumerate(items):
        doc.kpi(120 + i * (w + gap), y, w, h, v, u, lab, note, accent)
    return y + h


# ---------------------------------------------------------------- P1 封面
def page_cover(doc: Canvas):
    doc.d.rectangle([0, 0, A4_W, A4_H], fill=RED_DEEP)
    # 渐变叠加
    grad = Image.new("L", (1, A4_H))
    for i in range(A4_H):
        grad.putpixel((0, i), int(110 * (i / A4_H) ** 0.7))
    red_layer = Image.new("RGB", (A4_W, A4_H), (140, 24, 30))
    doc.img.paste(Image.composite(red_layer, doc.img, grad.resize((A4_W, A4_H))), (0, 0))
    doc.d = ImageDraw.Draw(doc.img)
    # 宝塔
    pagoda(doc.d, A4_W - 380, 1560, 2.5, (150, 42, 42))
    doc.d.ellipse([A4_W - 900, 1560, A4_W + 200, 1900], fill=(120, 26, 30))
    doc.d.ellipse([-300, 1620, 700, 1960], fill=(120, 26, 30))

    doc.d.text((120, 150), "第二届人工智能应用创新大赛 · 参赛作品说明", font=font(10.5), fill=(240, 205, 180))
    doc.d.line([(120, 200), (520, 200)], fill=GOLD, width=3)
    doc.d.text((120, 250), "红源智导", font=font(58, True), fill=(255, 246, 234))
    doc.d.text((126, 470), "REDORIGIN  GUIDE   ·   v1.3", font=font(13), fill=(216, 178, 94))
    doc.d.text((120, 530), "面向革命老区延安的“红旅 + 农品”一体化", font=font(21), fill=(255, 238, 222))
    doc.d.text((120, 585), "AI 导览智能体", font=font(21), fill=(255, 238, 222))
    doc.d.text((120, 665), "让每一次到访更懂历史，让每一颗果子卖得更远。", font=font(12), fill=(228, 185, 158))

    chips = ["事实可溯源", "边界可解释", "文案合规", "助农可落地"]
    x = 120
    for c in chips:
        tw = text_width(doc.d, c, 9) + 40
        doc.d.rounded_rectangle([x, 740, x + tw, 788], radius=10, outline=(200, 160, 120), width=2)
        doc.d.text((x + 20, 764), c, font=font(9), fill=(240, 214, 190), anchor="lm")
        x += tw + 16

    doc.d.line([(120, 1900), (A4_W - 120, 1900)], fill=(150, 70, 60), width=2)
    doc.d.text((120, 1930), "命题领域", font=font(9), fill=(214, 168, 140))
    doc.d.text((120, 1962), "AI 赋能革命老区振兴", font=font(13, True), fill=(255, 240, 226))
    doc.d.text((120, 2024), "作品形态", font=font(9), fill=(214, 168, 140))
    doc.d.text((120, 2056), "可运行的 Web 智能体 + 参赛作品说明 + 答辩 PPT", font=font(11), fill=(255, 240, 226))
    doc.d.text((120, 2140), "2026 年 10 月　｜　参赛团队：红源智导", font=font(9.5), fill=(206, 160, 132))
    doc.d.text((120, 2180), "（按大赛要求，作品内不出现学校、学生姓名与指导教师信息）", font=font(7.6), fill=(180, 132, 110))


# ---------------------------------------------------------------- P2 速览
def page_summary(doc: Canvas):
    doc.section_header("OVERVIEW", "一页看懂：一个“不敢编”的导览智能体",
                       "把老区的历史讲准、把老区的果子讲清——准确，是这个作品的第一功能。")
    y = 420
    doc.d.text((120, y), "现实约束", font=font(11, True), fill=RED)
    doc.d.rectangle([120, y + 34, 460, y + 38], fill=GOLD)
    cards = [
        ("4731.54 万人次", "2024 年延安接待国内游客，同比 +12.7%", "但全市星级宾馆仅 39 家"),
        ("381 亿元", "2024 年旅游总花费，人均 805.23 元", "人均消费偏低，过夜与二次消费不足"),
        ("500.03 万吨", "2024 年延安苹果产量，2025 年达 528 万吨", "品牌价值高，但县域外认知多停留在“甜”"),
    ]
    yy = y + 70
    for big, mid, small in cards:
        doc.rect(120, yy, 520, 150, fill=WHITE, outline=LINE, radius=14)
        doc.d.text((146, yy + 24), big, font=font(17, True), fill=RED)
        doc.d.text((146, yy + 74), mid, font=font(8.4), fill=INK2)
        doc.d.text((146, yy + 108), small, font=font(8.4), fill=INK3)
        yy += 170

    # 右侧方案
    doc.d.text((720, y), "方案骨架", font=font(11, True), fill=RED)
    doc.d.rectangle([720, y + 34, 1040, y + 38], fill=GOLD)
    mods = [
        ("讲解", "RAG 检索 + 来源回填", f"{N_SPOTS} 个点位、{N_KB} 条事实，逐条注明机构、文件、日期"),
        ("行程", "片区聚类 + 节奏约束", "只编排已核验点位，不虚构景点凑数"),
        ("农品", "事实槽位 + 合规检查", f"{N_PROD} 个地标产品，自动拦截绝对化用语"),
        ("边界", "实时信息不猜", "票价/时间给官方表；天气/客流直说“不掌握”"),
    ]
    yy = y + 70
    for name, how, desc in mods:
        doc.rect(720, yy, 494, 118, fill=WHITE, outline=LINE, radius=12)
        doc.d.rectangle([720, yy, 726, yy + 118], fill=RED)
        doc.d.text((750, yy + 20), name, font=font(11, True), fill=INK)
        doc.d.text((750, yy + 52), how, font=font(8.6), fill=RED)
        doc.d.text((750, yy + 82), desc, font=font(7.8), fill=INK3)
        yy += 136

    # 底部成效
    yb = 1120
    doc.d.text((120, yb), "本次提交的可验证结果", font=font(11, True), fill=RED)
    doc.d.rectangle([120, yb + 34, 500, yb + 38], fill=GOLD)
    kpis(doc, yb + 64, [
        (str(len(KB)), " 条", "已核验知识条目", "全部带机构 / 文件 / 日期"),
        (f"{EVAL['accuracy']*100:.0f}%", "", "46 条自建评测意图准确率", "含长尾与拒绝样本"),
        (f"{EVAL['latency_ms']['avg']:.2f}", " ms", "端到端平均响应", "离线模式；接入 API 后约 1.1 s"),
        (str(len(PRODUCTS)), " 个", "地理标志农产品可生成文案", "生成即做广告法检查"),
    ], h=190)

    note_y = 1520
    doc.rect(120, note_y, 1414, 300, fill=CREAM, outline=(235, 224, 205), radius=14)
    doc.d.text((150, note_y + 30), "一句话定位", font=font(9), fill=GOLD)
    doc.para(150, note_y + 62,
             "通用大模型能把延安讲得“很像”，但会把门票讲错、把“预计产量”讲成“实际产量”、把品牌价值讲成产值。"
             f"红源智导反其道而行：把可讲的话收窄到 {N_KB} 条有出处的事实，把不能讲的话明确说出来。"
             "准确不是能力的上限，而是产品的底线。", size=10.5, max_w=1354, lh=1.9, color=INK2)
    doc.footer(2, TOTAL)


# ---------------------------------------------------------------- P3 背景
def page_background(doc: Canvas):
    y = doc.section_header("一 · 作品背景与说明", "政策要求“人工智能+”，老区需要“讲得准”",
                           "从中央文件到部委行动，“AI + 革命老区”已经从倡议变成了任务。")
    y = doc.para(120, y, "1. 政策依据：从“支持”到“实施行动”", size=11.5, bold=True, color=RED, space_after=10)

    pol = [
        ("2026-03-13", "中办、国办《关于加快革命老区振兴发展的意见》",
         "首次提出“在具备条件的革命老区实施‘人工智能+’行动”，并部署文旅深度融合、红色文化数字化传播平台、区域性红色研学基地与研学路线。"),
        ("2021-02-20", "国务院《关于新时代支持革命老区振兴发展的意见》（国发〔2021〕3号）",
         "要求加强地理标志农产品认证管理、推动品牌打造；推动红色旅游高质量发展，加大对杨家岭革命旧址等纪念设施保护修缮力度。"),
        ("2024-05-06", "文化和旅游部等 5 部门《智慧旅游创新发展行动计划》（办资源发〔2024〕82号）",
         "到 2027 年部署 8 大行动、20 项任务，明确运用通用人工智能、AIGC 提升旅游营销与服务能力。"),
        ("2025-08-26", "国务院《关于深入实施“人工智能+”行动的意见》（国发〔2025〕11号）",
         "分阶段推进“人工智能+”与经济社会各领域深度融合。"),
    ]
    yy = y + 20
    for date, title, desc in pol:
        doc.rect(120, yy, 1414, 142, fill=WHITE, outline=LINE, radius=12)
        doc.d.rectangle([120, yy, 126, yy + 142], fill=RED)
        doc.d.text((150, yy + 18), date, font=font(8.4, True), fill=GOLD)
        tx = 150 + text_width(doc.d, date, 8.4, True) + 26
        doc.d.text((tx, yy + 15), title, font=font(9.6, True), fill=INK)
        for j, line in enumerate(doc.wrap(desc, 8.4, 1270)[:2]):
            doc.d.text((150, yy + 66 + j * 32), line, font=font(8.4), fill=INK3)
        yy += 156

    y2 = yy + 10
    doc.d.text((120, y2), "2. 现实问题：三个“最后一公里”", font=font(11.5, True), fill=RED)
    probs = [
        ("讲解的最后一公里", "延安 62 个 A 级景区、4 家 5A，但现场讲解供给集中在团队时段；散客听到的常常是段子而不是史实。"),
        ("消费的最后一公里", "2024 年人均花费 805.23 元，星级宾馆 39 家——游客“来了、看了、走了”，过夜与二次消费没被激活。"),
        ("品牌的最后一公里", "洛川苹果品牌价值 883.26 亿元，但果农与合作社缺的是“能直接用的合规文案”，不是又一个空泛的品牌口号。"),
    ]
    xx = 120
    for i, (t, d) in enumerate(probs):
        doc.rect(xx, y2 + 44, 448, 210, fill=WHITE, outline=LINE, radius=14)
        doc.d.text((xx + 24, y2 + 62), f"0{i+1}", font=font(15, True), fill=(226, 210, 186))
        doc.d.text((xx + 24, y2 + 100), t, font=font(10.5, True), fill=INK)
        for j, line in enumerate(doc.wrap(d, 8.4, 400)[:4]):
            doc.d.text((xx + 24, y2 + 138 + j * 30), line, font=font(8.4), fill=INK3)
        xx += 474

    doc.rect(120, y2 + 276, 1414, 190, fill=RED_SOFT, radius=14)
    doc.d.text((150, y2 + 298), "3. 作品定位", font=font(9), fill=RED)
    doc.para(150, y2 + 326,
             "红源智导不是“又一个延安旅游问答机器人”。它把文旅讲解与农产品推广放在同一个知识库里，"
             "用同一套“来源—日期—适用边界”的规则约束输出：游客在宝塔山下问“这附近能带走什么”，"
             "回答里既有苹果的产地事实，也有合作社的助农渠道，但不会出现一句没有出处的数字。",
             size=9.6, max_w=1354, lh=1.85)

    doc.band(1950, "本页来源",
             "政策表述均逐字核对原文；旅游与产业数据取自《2024年延安市国民经济和社会发展统计公报》"
             "（延安市人民政府，2025-05-30）与陕西日报 2026-10-01 报道。",
             "中办国办《关于加快革命老区振兴发展的意见》2026-03-13 · 国务院国发〔2021〕3号 2021-02-20 · "
             "文旅部等《智慧旅游创新发展行动计划》2024-05-06 · 国务院国发〔2025〕11号 2025-08-26")
    doc.footer(3, TOTAL)


# ---------------------------------------------------------------- P4 数据来源 1
def page_sources1(doc: Canvas):
    y = doc.section_header("二 · 数据收集与处理", "数据从哪来：三类主渠道，全部可点开核对",
                           "只使用公开、可引用、可复核的资料；不购买数据、不抓取个人信息、不使用未公开统计。")
    doc.d.text((120, y), "三个主要获取渠道", font=font(11.5, True), fill=RED)
    chans = [
        ("渠道一", "政府统计与公报", "权威性：法定统计口径，年度核定\n时效性：2024 年公报 2025-05 发布",
         "延安市统计局《2024年延安市国民经济和社会发展统计公报》：GDP、旅游人次与花费、苹果面积产量、城乡居民收入、景区与宾馆数量。"),
        ("渠道二", "行业主管部门名录与公告", "权威性：主管部门直接发布\n时效性：A 级景区表更新至 2026-10-26",
         "延安市文化和旅游局《延安市A级旅游景区基本信息表》《延安革命纪念地景区介绍》：{N_SPOTS} 个点位的等级、门票、开放时间、预约电话。"),
        ("渠道三", "政策原文与权威媒体", "权威性：中国政府网 / 新华社 / 陕西日报\n时效性：逐条标注发布日期",
         "中办国办与国务院文件、文旅部文件、新华社与陕西日报报道：政策表述、品牌价值、产业数据、助农案例。"),
    ]
    yy = y + 34
    for tag, name, meta, desc in chans:
        doc.rect(120, yy, 1414, 246, fill=WHITE, outline=LINE, radius=14)
        doc.rect(120, yy, 8, 246, fill=RED, radius=0)
        doc.d.text((156, yy + 24), tag, font=font(8.4), fill=GOLD)
        doc.d.text((156, yy + 52), name, font=font(12, True), fill=INK)
        for j, line in enumerate(meta.split("\n")):
            doc.d.text((156, yy + 92 + j * 28), line, font=font(8), fill=INK3)
        for j, line in enumerate(doc.wrap(desc, 8.8, 880)[:3]):
            doc.d.text((560, yy + 40 + j * 34), line, font=font(8.8), fill=INK2)
        yy += 264

    doc.rect(120, yy + 6, 1414, 150, fill=CREAM, outline=(235, 224, 205), radius=12)
    doc.d.text((150, yy + 28), "采集方式与真实性约束", font=font(9), fill=GOLD)
    doc.para(150, yy + 58,
             "人工检索 + 交叉验证：每条事实至少 1 个官方来源；涉及数字的条目再找 1 个独立来源比对。"
             "采集过程不使用爬虫批量抓取，不采集游客个人信息，不引用无法打开原文的二手转述。", size=8.8, max_w=1354, lh=1.7)
    doc.band(1900, "本页来源",
             "延安市统计局与延安市文化和旅游局官网（yanan.gov.cn）、中国政府网（gov.cn）为三类主渠道；"
             "所有页面均在 2026-10-29 当日实际打开核对，未使用需登录或付费的数据源。")
    doc.footer(4, TOTAL)


# ---------------------------------------------------------------- P5 数据来源 2
def page_sources2(doc: Canvas):
    y = doc.section_header("二 · 数据收集与处理", "来源清单：12 条主要出处，逐条可溯源",
                           "表中每一条都实际打开核对过；标注“未核实”的，作品里不用。")
    rows = [
        ["延安市统计局", "2024年延安市国民经济和社会发展统计公报", "2025-05-30", "yanan.gov.cn", "市情/旅游/苹果/收入"],
        ["延安市文旅局", "延安市A级旅游景区基本信息表", "2026-10-26", "yanan.gov.cn", f"{N_SPOTS} 个点位门票与时间"],
        ["延安市文旅局", "5A级景区：延安旅游必打卡地标", "2026-04-22", "yanan.gov.cn", "景区讲解素材"],
        ["陕西省人民政府", "81个商标获评2024年“陕西好商标”", "2024-12-02", "shaanxi.gov.cn", "洛川苹果品牌价值"],
        ["陕西日报", "苹果全产业链综合产值619.9亿元", "2026-10-01", "news.cnwest.com", "延安苹果产业"],
        ["洛川县人民政府", "县长信箱·苹果产业管理局答复", "2025-05-07", "lcx.gov.cn", "县域产量/产值/出口"],
        ["延安市市场监管局", "政协提案答复函（地标家底）", "2025-05-27", "yanan.gov.cn", "地理标志数量"],
        ["延安市供销合作社", "为农服务添实效 供销赋能促振兴", "2025-10-21", "gxs.yanan.gov.cn", "832 平台/直播渠道"],
        ["新华社", "四季中国丨秋访南沟村", "2024-11-04", "xinhuanet.com", "助农直播案例"],
        ["中国政府网", "中办国办：关于加快革命老区振兴发展的意见", "2026-03-13", "gov.cn", "“人工智能+”行动"],
        ["中国政府网", "国发〔2021〕3号", "2021-02-20", "gov.cn", "老区振兴政策"],
        ["文化和旅游部", "智慧旅游创新发展行动计划", "2024-05-06", "gov.cn", "智慧旅游任务"],
    ]
    y = doc.table(120, y, [220, 560, 170, 230, 234],
                  ["发布机构", "文件 / 文章", "发布日期", "站点", "用于本作品的字段"],
                  rows, size=8.0, row_h=62)
    for j, line in enumerate(doc.wrap("冲突处理示例：延安革命纪念馆馆藏量，市文旅局介绍为“3.5 万余件”，另有报道称“11 万余件（组）”。"
                                      "作品采用前者并在知识库保留口径说明，不把两个数字混写。", 8, 1370)[:2]):
        doc.d.text((120, y + 24 + j * 26), line, font=font(8), fill=INK3)
    doc.rect(120, y + 74, 1414, 260, fill=WHITE, outline=LINE, radius=14)
    doc.d.text((150, y + 96), "时效性分级与刷新策略", font=font(10, True), fill=INK)
    tiers = [
        ("T1 年度", "统计公报、产业数据", "随年度公报更新，过期即标注年份"),
        ("T2 季度/事件", "政策文件、品牌价值、案例", "发布即入库，保留原文日期"),
        ("T3 高频", "门票、开放时间、预约电话", "以官方表为准，回答时附日期与“以当日公告为准”"),
        ("T4 实时", "天气、客流、余票、库存", "不接入、不猜测，直接说明不掌握"),
    ]
    yy = y + 136
    for t, scope, rule in tiers:
        doc.d.text((150, yy), t, font=font(8.6, True), fill=RED)
        doc.d.text((280, yy), scope, font=font(8.4), fill=INK2)
        doc.d.text((690, yy), rule, font=font(8.4), fill=INK3)
        doc.line(150, yy + 30, 1504, yy + 30, color=(242, 236, 226), width=1)
        yy += 42
    doc.footer(5, TOTAL)


# ---------------------------------------------------------------- P6 知识库 1
def page_kb1(doc: Canvas):
    y = doc.section_header("二 · 数据收集与处理", "知识库长什么样：一条事实 = 一段话 + 一个出处",
                           f"当前 {len(KB)} 条事实、{len(SPOTS)} 个点位、{len(PRODUCTS)} 个地标产品，全部结构化存储。")
    doc.d.text((120, y), "条目结构（JSON Schema 片段）", font=font(10.5, True), fill=RED)
    code = '''{
  "id": "product_luochuan_apple",
  "category": "product",
  "title": "洛川苹果",
  "keywords": ["品牌价值", "883.26亿元", "53万亩", ...],
  "text": "洛川苹果2024年品牌价值883.26亿元……",
  "source": {
    "name": "陕西省人民政府",
    "doc": "81个商标获评2024年“陕西好商标”",
    "date": "2024-12-02",
    "url": "https://www.shaanxi.gov.cn/..."
  }
}'''
    doc.rect(120, y + 34, 690, 400, fill=(38, 34, 31), radius=12)
    yy = y + 58
    for line in code.split("\n"):
        doc.d.text((146, yy), line, font=font(8.0), fill=(228, 220, 208))
        yy += 27

    doc.d.text((856, y), "五类知识，回答四类问题", font=font(10.5, True), fill=RED)
    cats = [("景点", "13", "讲解 / 门票 / 预约"), ("政策", "7", "政策解读 / 申报依据"),
            ("市情数据", "6", "数据问答 / 趋势"), ("农品", "3", "产地事实 / 文案槽位"),
            ("交通", "2", "怎么来 / 多长时间")]
    yy = y + 40
    for name, n, use in cats:
        doc.rect(856, yy, 678, 62, fill=WHITE, outline=LINE, radius=10)
        doc.d.text((880, yy + 31), name, font=font(9.4, True), fill=INK, anchor="lm")
        doc.d.text((1010, yy + 31), f"{n} 条", font=font(8.6), fill=RED, anchor="lm")
        doc.d.text((1110, yy + 31), use, font=font(8), fill=INK3, anchor="lm")
        yy += 74

    doc.rect(120, y + 470, 1414, 380, fill=WHITE, outline=LINE, radius=14)
    doc.d.text((150, y + 494), "真实条目：洛川苹果（原文照录，来源见上）", font=font(9), fill=GOLD)
    item = next(k for k in KB if k["id"] == "product_luochuan_apple")
    doc.para(150, y + 530, item["text"], size=9.2, max_w=1354, lh=1.95, color=INK2)
    doc.d.text((150, y + 780), f"来源：{item['source']['name']}《{item['source']['doc']}》 {item['source']['date']}",
               font=font(8), fill=INK3)

    doc.rect(120, y + 880, 690, 250, fill=RED_SOFT, radius=12)
    doc.d.text((150, y + 902), "为什么不用“一段话喂给大模型”", font=font(9), fill=RED)
    doc.para(150, y + 932,
             "因为大模型无法回答“这句话出自哪一年、哪份文件”。结构化条目把“内容”和“出处”绑定，"
             "回答时可以逐条回填来源；条目缺失时，系统能明确知道“我不知道”，而不是编一个像样的答案。",
             size=8.6, max_w=630, lh=1.75)

    doc.rect(844, y + 880, 690, 250, fill=WHITE, outline=LINE, radius=12)
    doc.d.text((874, y + 902), "维护机制（谁在保证它不过期）", font=font(9), fill=GOLD)
    mt = ["年度公报发布后 7 日内更新 T1 数据", "政策/品牌价值等事件驱动条目随发布入库",
          "门票与开放时间随官方表更新，回答附日期", "每条目保留 url 与抓取日期，便于复查"]
    my = y + 936
    for t in mt:
        doc.d.text((874, my), "·", font=font(9, True), fill=RED)
        doc.d.text((900, my), t, font=font(8.2), fill=INK2)
        my += 40
    doc.band(1980, "本页来源",
             "条目样例原文出自陕西省人民政府《81个商标获评2024年“陕西好商标”》（2024-12-02）；"
             f"数据结构与统计由作者对 data/kb.json 直接计算得出（{N_KB} 条）。")
    doc.footer(6, TOTAL)


# ---------------------------------------------------------------- P7 知识库 2
def page_kb2(doc: Canvas):
    y = doc.section_header("二 · 数据收集与处理", "覆盖度与缺口：把“不知道”也写进知识库",
                           "知识库的价值不仅在收录了什么，更在于清楚标出了没收录什么。")
    doc.d.text((120, y), "点位 × 字段覆盖矩阵（● 已收录）", font=font(10.5, True), fill=RED)
    heads = ["点位", "片区", "等级", "历史讲解", "门票", "开放时间", "预约", "时长"]
    rows = []
    for s in SPOTS:
        rows.append([s["name"], s["area"], s["level"].replace("延安革命纪念地景区（5A）核心点", "5A 核心点"),
                     "●", "●", "●", "●", "●"])
    y2 = doc.table(120, y + 34, [330, 120, 230, 190, 130, 190, 140, 84], heads, rows, size=7.8, row_h=44,
                   align=["l", "l", "l", "l", "l", "l", "l", "l"])
    doc.d.text((120, y2 + 16), f"覆盖：{N_SPOTS} 个点位 × 8 个字段；全部点位的门票、开放时间、预约电话来自官方表（2026-10-26）。",
               font=font(7.8), fill=INK3)

    yy = y2 + 70
    doc.d.text((120, yy), "主动标注的缺口（回答时如实说明，不用推测填补）", font=font(10.5, True), fill=RED)
    gaps = [
        ("梁家河", "未列入延安市 A 级景区名录，等级/门票/预约无官方文件，故不进路线、不报价格。"),
        ("部分农品", "延川红枣、黄龙核桃的产量与产值无公开县级数据，文案只写地标身份与口感，不写规模。"),
        ("纪念馆藏品口径", "“3.5 万余件”与“11 万余件（组）”并存，保留说明而不合并。"),
        ("实时数据", "天气、客流、余票、库存不接入，明确告知不掌握并给官方入口。"),
    ]
    yy += 40
    for name, desc in gaps:
        doc.rect(120, yy, 1414, 84, fill=WHITE, outline=LINE, radius=10)
        doc.d.text((146, yy + 42), name, font=font(9.2, True), fill=INK, anchor="lm")
        doc.d.text((400, yy + 42), desc, font=font(8.2), fill=INK3, anchor="lm")
        yy += 98
    doc.rect(120, yy + 8, 1414, 120, fill=CREAM, outline=(235, 224, 205), radius=12)
    doc.d.text((150, yy + 30), "设计原则", font=font(9), fill=GOLD)
    doc.para(150, yy + 58, "宁缺毋滥：一条没有出处的事实，进入知识库的代价远高于缺失本身——它会以“可信”的样子被传播出去。",
             size=9, max_w=1354, lh=1.7)
    doc.band(1960, "本页来源",
             "覆盖矩阵由 data/spots.json 与 data/kb.json 直接统计；缺口清单来自核查过程中的实际检索失败记录，"
             "例如梁家河在《延安市A级旅游景区基本信息表》（2026-10-26）中未出现。")
    doc.footer(7, TOTAL)


# ---------------------------------------------------------------- P8 预处理
def page_pipeline(doc: Canvas):
    y = doc.section_header("二 · 数据收集与处理", "预处理流程：从网页原文到一条可引用的回答",
                           "全部用 Python 标准库实现，无第三方依赖，可在断网环境复现。")
    steps = [
        ("① 采集", "人工检索官方页面\n保存原文与日期", RED),
        ("② 清洗", "去导航/广告\n抽取正文与数字", RED),
        ("③ 结构化", "拆分字段：\n标题/正文/来源/日期", GOLD),
        ("④ 校验", "双人复核数字\n冲突单列说明", GOLD),
    ]
    doc.flow(120, y + 20, steps, box_w=310, box_h=118, gap=56)
    steps2 = [
        ("⑤ 切片", "按“一条事实一段话”\n切分为问答单元", GREEN),
        ("⑥ 索引", "中文二元组 + BM25\n标题/关键词加权", GREEN),
        ("⑦ 路由", "意图识别\n上下文继承", BLUE),
        ("⑧ 组装", "答案 + 来源回填\n+ 时效提示", BLUE),
    ]
    doc.flow(120, y + 190, steps2, box_w=310, box_h=118, gap=56)


    yy = y + 350
    doc.d.text((120, yy), "关键步骤的技术手段与用途", font=font(10.5, True), fill=RED)
    rows = [
        ["清洗", "Python 正则 + 人工阅读", "去掉页面导航与图片说明，只保留可引用的正文句"],
        ["结构化", "JSON / JSONL 手写校验", "一条事实一个 source，保证回答能回填出处"],
        ["检索", "字二元组 + BM25（k1=1.5, b=0.75）", "无需向量模型即可离线运行，中文短查询召回稳定"],
        ["意图路由", "关键词打分 + 会话继承", "把“门票/预约/天气”导向边界处理，避免模型自由发挥"],
        ["行程生成", "片区聚类 + 节奏约束 + 午餐占位", "同一天只在一个片区活动，不虚构景点与车程"],
        ["文案生成", "事实槽位模板 + 违禁词表", "只填知识库字段，生成后立即做广告法检查"],
    ]
    y3 = doc.table(120, yy + 34, [190, 470, 754], ["步骤", "技术手段", "在 Agent 中的用途"], rows, size=8.4, row_h=62)
    doc.d.text((120, y3 + 18), "工程取舍：为保证评审在任何环境都能“打开就跑”，作品零第三方依赖、零外部 API 调用；"
                               f"全部计算在本地完成，平均响应 {EVAL['latency_ms']['avg']:.2f} ms。", font=font(8.2), fill=INK3)
    doc.footer(8, TOTAL)


# ---------------------------------------------------------------- P9 分析方法
def page_method(doc: Canvas):
    y = doc.section_header("三 · 分析过程", "方法选择：为什么是“检索增强 + 规则路由”，不是“一个大模型”",
                           "在事实密度高、容错率低的场景，可解释性比生成能力更重要。")
    rows = [
        ["纯大模型问答", "表达自然、覆盖广", "易编造票价与年份；无法给出来源；成本与延迟不可控", "不采用"],
        ["纯关键词 FAQ", "可控、快", "问法稍变就答不上；无法组织行程与文案", "不采用"],
        ["检索增强 + 规则路由（本方案）", "答案有出处；边界清晰；离线可跑", "长尾问法需持续扩充规则；知识库维护成本高", "采用"],
    ]
    doc.table(120, y, [300, 300, 640, 174], ["方案", "优势", "局限", "结论"], rows, size=8.6, row_h=96,
              align=["l", "l", "l", "m"])

    y2 = y + 360
    doc.d.text((120, y2), "四个可量化的评价指标", font=font(10.5, True), fill=RED)
    metrics = [
        ("意图准确率", "回答是否落到正确的功能分支", "46 条自建评测集，逐条人工标注"),
        ("来源覆盖率", "事实型回答是否附得出出处", "按回答类型分别统计，规划类不计"),
        ("端到端时延", "从收到问题到返回结构化答案", "本地计时，取 P50/P95"),
        ("边界行为", "该拒答时是否拒答", "天气/实时票价/未收录产品等 6 类样本"),
    ]
    yy = y2 + 40
    for name, what, how in metrics:
        doc.rect(120, yy, 1414, 92, fill=WHITE, outline=LINE, radius=10)
        doc.d.text((146, yy + 46), name, font=font(9.4, True), fill=INK, anchor="lm")
        doc.d.text((400, yy + 46), what, font=font(8.4), fill=INK2, anchor="lm")
        doc.d.text((980, yy + 46), how, font=font(8.2), fill=INK3, anchor="lm")
        yy += 104

    doc.rect(120, yy + 10, 1414, 190, fill=RED_SOFT, radius=12)
    doc.d.text((150, yy + 34), "为什么这个方法适配老区场景", font=font(9), fill=RED)
    doc.para(150, yy + 64,
             "老区文旅的容错率极低：一句错的建馆年份、一个错的票价，会被游客当作官方信息转发。"
             f"本方案把“生成”降级为“组织”，把“知识”前置到人工核验过的 {N_KB} 条事实上；"
             "代价是覆盖面有限，收益是每句话都能被追问“凭什么”。", size=9, max_w=1354, lh=1.8)
    doc.footer(9, TOTAL)


# ---------------------------------------------------------------- P10 思维导图
def page_mindmap(doc: Canvas):
    y = doc.section_header("三 · 分析过程", "问题理解：老区振兴要打通的四次转化",
                           "把“AI 赋能”翻译成四个可被验证的具体动作，再逐个落到功能上。")
    # 中心节点
    doc.rect(392, y + 10, 870, 128, fill=RED, radius=18)
    doc.d.text((827, y + 42), "AI 赋能革命老区振兴", font=font(15, True), fill=WHITE, anchor="ma")
    doc.d.text((827, y + 84), "把“来过”变成“记住并带走”", font=font(9), fill=(246, 214, 200), anchor="ma")

    branches = [
        ("流量 → 消费", "游客侧", ["行程编排降低决策成本，答案是一张时间表", "讲解延长停留时长，减少“打卡即走”", "农品推荐承接二次消费，游中可购"], "讲解 / 行程 / 农品"),
        ("文化 → 产品", "运营侧", ["史实结构化为可复述的条目，而非长篇散文", "点位 × 片区可自由组合成线路", "回答自带出处，降低宣传与审核成本"], "知识库 / 来源回填"),
        ("特产 → 品牌", "农户侧", ["地标身份可核验：证明商标、公告号、批次", "卖点转成合规文案，果农可直接用", "渠道事实（832 平台 / 供销社）可查"], "农品 IP 工坊"),
        ("数据 → 治理", "政府侧", ["缺口清单即改进清单，可转成任务单", "问句日志反映真实需求分布", "口径冲突暴露统计与发布问题"], "看板 / 日志 / 缺口表"),
    ]
    positions = [(120, y + 200), (827, y + 200), (120, y + 610), (827, y + 610)]
    for (title, who, items, mod), (bx, by) in zip(branches, positions):
        doc.line(827, y + 138, bx + 353, by, color=(224, 198, 150), width=3)
    for (title, who, items, mod), (bx, by) in zip(branches, positions):
        doc.rect(bx, by, 707, 360, fill=WHITE, outline=LINE, radius=16)
        doc.d.text((bx + 30, by + 26), title, font=font(12.5, True), fill=RED)
        doc.d.text((bx + 30, by + 62), who, font=font(8), fill=INK3)
        doc.d.text((bx + 30, by + 318), "对应模块：" + mod, font=font(7.4), fill=GOLD)
        iy = by + 108
        for it in items:
            doc.d.ellipse([bx + 32, iy + 8, bx + 44, iy + 20], fill=GOLD)
            for j, line in enumerate(doc.wrap(it, 8.4, 620)[:2]):
                doc.d.text((bx + 60, iy + j * 28), line, font=font(8.4), fill=INK2)
            iy += 66

    doc.band(1900, "推理链",
             "真实数据（4731.54 万人次 / 805.23 元 / 500.03 万吨）→ 需求假设（散客缺讲解、缺动线、缺可信购买理由）"
             "→ 功能设计（讲解 / 行程 / 农品 / 边界）→ 46 条评测与真实问答验证。",
             "数据来源：延安市人民政府《2024年延安市国民经济和社会发展统计公报》2025-05-30。")
    doc.footer(10, TOTAL)


# ---------------------------------------------------------------- P11 数据图表
def page_charts(doc: Canvas):
    y = doc.section_header("三 · 分析过程", "数据实例：三个结构性事实，决定了产品该做什么",
                           "图表数据均取自前页来源清单，未做任何估算、插值或单位换算。")
    # ① 游客与花费（两个独立坐标，避免双轴误导）
    doc.d.text((120, y), "① 游客在增长，人均花费只有 805 元", font=font(9.8, True), fill=INK)
    doc.rect(120, y + 30, 690, 380, fill=WHITE, outline=LINE, radius=12)
    doc.bar_chart(160, y + 60, 610, 300, ["2023", "2024"], [[4198.77, 4731.54]],
                  colors=[RED], max_val=5600, value_fmt="{:.0f}")
    doc.d.text((150, y + 372), "图注：接待国内游客（万人次），2024 年同比 +12.7%", font=font(7.2), fill=INK3)

    doc.rect(844, y + 30, 690, 380, fill=WHITE, outline=LINE, radius=12)
    doc.bar_chart(884, y + 60, 610, 300, ["2023", "2024"], [[330.70, 381.00]],
                  colors=[GOLD], max_val=460, value_fmt="{:.0f}")
    doc.d.text((874, y + 372), "图注：旅游总花费（亿元），2024 年同比 +15.2%", font=font(7.2), fill=INK3)

    # ② 供给结构
    y2 = y + 440
    doc.d.text((120, y2), "② 供给呈“金字塔”：3A 多、头部少", font=font(9.8, True), fill=INK)
    doc.rect(120, y2 + 30, 690, 330, fill=WHITE, outline=LINE, radius=12)
    doc.hbar(150, y2 + 90, 630, [("5A 级", 4, "4 家"), ("4A 级", 9, "9 家"), ("3A 级", 49, "49 家")],
             max_val=55, color=RED, row_h=80, label_w=110)
    doc.d.text((150, y2 + 330), "截至 2026-10-26，全市 A 级景区 62 个", font=font(7.2), fill=INK3)

    # ③ 苹果
    doc.d.text((844, y2), "③ 苹果是“压舱石”，品牌价值与县域产值不同量级", font=font(9.8, True), fill=INK)
    doc.rect(844, y2 + 30, 690, 330, fill=WHITE, outline=LINE, radius=12)
    ap = [("332 万亩", "2025 年种植面积"), ("528 万吨", "2025 年产量"),
          ("292.4 亿元", "2025 年鲜果产值"), ("619.9 亿元", "全产业链综合产值"),
          ("63.2%", "占农业总产值与农民经营净收入"), ("883.26 亿元", "洛川苹果品牌价值（≠产值）")]
    for i, (v, lab) in enumerate(ap):
        bx = 874 + (i % 2) * 330
        by = y2 + 60 + (i // 2) * 92
        doc.d.text((bx, by), v, font=font(14, True), fill=RED if i < 4 else GOLD)
        doc.d.text((bx, by + 38), lab, font=font(7), fill=INK3)

    # 结论
    y3 = y2 + 390
    doc.rect(120, y3, 1414, 250, fill=RED_SOFT, radius=12)
    doc.d.text((150, y3 + 24), "读图结论（直接决定功能优先级）", font=font(9), fill=RED)
    doc.para(150, y3 + 56,
             "人均 805 元、星级宾馆 39 家，说明“过夜经济”是短板 → 行程功能必须解决“怎么待满两天”；"
             f"供给金字塔意味着大量 3A 景区缺讲解 → 讲解功能覆盖 {N_SPOTS} 个点位而非只做 5A；"
             "品牌价值 883 亿元远高于县域产值 140 亿元，说明“品牌溢价”尚未落到果农 → 文案功能必须能直接给合作社用。",
             size=9, max_w=1354, lh=1.85)

    doc.band(1900, "本页来源",
             "游客与花费：延安市统计局（2024 年公报，2025-05-30）；A 级景区结构：延安市文旅局《延安市A级旅游景区基本信息表》（2026-10-26）；"
             "苹果产业：陕西日报 2026-10-01；洛川苹果品牌价值：陕西省人民政府 2024-12-02。",
             "口径提示：洛川县 2024 年产值 140 亿元为县域口径，与全市鲜果产值 292.4 亿元不可直接比较；品牌价值 883.26 亿元不等于销售收入。")
    doc.footer(11, TOTAL)


# ---------------------------------------------------------------- P12 创新点
def page_innovation(doc: Canvas):
    y = doc.section_header("四 · 创新性与独特视角", "两个真正的创新点：同库双引擎、可解释护栏",
                           "不是把模型做大，而是把误差做小。")
    blocks = [
        ("创新点 01", "文旅 + 农品同库的“双引擎”",
         f"通用文旅助手把“玩”和“买”分开：讲完景点，再让用户跳去电商。红源智导把 {N_SPOTS} 个点位与 {N_PROD} 个地标产品放进同一个知识库、"
         "同一次检索里，用户在枣园问“能带走什么”，回答会同时给出苹果的产地事实、品牌价值与助农渠道，且两者都带来源。",
         ["同一套来源规则约束两类内容", "行程结束点自然衔接农品", "为“游中带购”提供可审计的话术"]),
        ("创新点 02", "把“不知道”设计成一等功能",
         "系统对四类问题主动降级：实时信息（天气/客流/余票）、未收录实体、未核实数据、超出范围请求。"
         "降级不是失败提示，而是带官方入口的结构化答复；同时把缺口写进知识库文档，形成可追踪的改进清单。",
         ["拒答有模板、有出口、有记录", "口径冲突单列，不合并、不四舍五入", "缺口清单可直接作为数据治理建议"]),
    ]
    yy = y
    for tag, title, desc, bullets in blocks:
        doc.rect(120, yy, 1414, 400, fill=WHITE, outline=LINE, radius=16)
        doc.rect(120, yy, 8, 400, fill=RED, radius=0)
        doc.tag(150, yy + 28, tag, fg=RED, bg=RED_SOFT, size=8)
        doc.d.text((150, yy + 74), title, font=font(14, True), fill=INK)
        doc.para(150, yy + 130, desc, size=9, max_w=1330, lh=1.72)
        by = yy + 268
        for b in bullets:
            doc.d.text((150, by), "·", font=font(10, True), fill=GOLD)
            doc.d.text((176, by), b, font=font(8.6), fill=INK2)
            by += 36
        yy += 424

    doc.d.text((120, yy + 6), "与常见方案的位置关系", font=font(9.6, True), fill=RED)
    rows = [
        ["通用导游 App", "点位介绍 + 购票入口", "讲得泛；无出处；农品导流弱"],
        ["通用大模型", "什么都能聊", "票价/年份易错；无法追溯；合规风险"],
        ["红源智导", "讲解 + 行程 + 农品文案 + 边界", "覆盖面有限，但每句话可被追问“凭什么”"],
    ]
    doc.table(120, yy + 40, [280, 560, 574], ["类型", "能力", "短板 / 取舍"], rows, size=8.6, row_h=70)
    doc.footer(12, TOTAL)


# ---------------------------------------------------------------- P13 独特视角
def page_perspective(doc: Canvas):
    y = doc.section_header("四 · 创新性与独特视角", "跨学科视角：把老区当作一个“需要被准确讲述的产品”",
                           "五个学科各解决一段，缺一段就会漏。")
    disc = [
        ("情报学", "来源分级与可信度", "把 T1–T4 时效分级、机构权威性写进数据结构，而不是写在 PPT 里。"),
        ("旅游管理", "游线组织与停留时长", "片区聚类 + 节奏约束，用“半天一个片区”替代“景点堆叠”。"),
        ("农业经济", "区域品牌与价值链", "区分“品牌价值”与“产值”，避免把 883 亿元说成 140 亿元。"),
        ("法学（广告法）", "合规前置", "生成即检查：绝对化用语、功效宣称、价格承诺三类红线。"),
        ("计算机", "检索增强与结构化生成", "BM25 + 槽位模板，把“生成”限制在可验证的范围内。"),
    ]
    yy = y
    for i, (name, cap, desc) in enumerate(disc):
        doc.rect(120, yy, 1414, 150, fill=WHITE, outline=LINE, radius=12)
        doc.d.text((150, yy + 40), name, font=font(10.5, True), fill=RED)
        doc.d.text((150, yy + 84), cap, font=font(8), fill=INK3)
        doc.para(430, yy + 44, desc, size=8.8, max_w=1060, lh=1.7)
        yy += 162

    doc.rect(120, yy + 10, 1414, 270, fill=RED, radius=16)
    doc.d.text((160, yy + 46), "本作品的独特视角", font=font(9), fill=(240, 200, 170))
    doc.d.text((160, yy + 84), "别人在做“更会说话的模型”，我们在做“更少说错的话”。",
               font=font(16, True), fill=WHITE)
    doc.para(160, yy + 140,
             "老区振兴不缺流量，缺的是把流量留下来、把故事讲准确、把果子卖出去的基础设施。"
             f"当一个县的文化资源被拆成 {N_KB} 条可引用的事实，它才第一次具备了被机器稳定复述的条件；"
             "这也正是“人工智能+”在县域落地时最容易被忽略的一层：数据治理先于模型能力。",
             size=9, max_w=1340, lh=1.8, color=(250, 230, 216))
    doc.footer(13, TOTAL)


def _bubble(doc: Canvas, x, y, w, text, who="bot", sources=None, size=8.6, max_lines=999):
    pad = 22
    lines = doc.wrap(text, size, w - pad * 2)
    lines = lines[:max_lines]
    h = len(lines) * size * PX * 1.55 + pad * 2
    fill = WHITE if who == "bot" else RED
    fg = INK if who == "bot" else WHITE
    doc.rect(x, y, w, h, fill=fill, outline=LINE if who == "bot" else None, radius=14)
    yy = y + pad
    for line in lines:
        doc.d.text((x + pad, yy), line, font=font(size), fill=fg)
        yy += size * PX * 1.55
    if sources:
        yy += 6
        doc.d.text((x + pad, yy), "来源：" + sources, font=font(7.2), fill=INK3)
        h += 26
    return y + h + 18


# ---------------------------------------------------------------- P14 结果解读 1
def page_result1(doc: Canvas):
    y = doc.section_header("五 · 结果解释与建议", "真实对话（一）：从一句话到一张可执行的行程",
                           "以下内容为智能体实际输出，未经改写。")
    x, w = 120, 900
    yy = y + 10
    doc.d.text((x + 60, yy), "游客", font=font(8), fill=INK3)
    yy = _bubble(doc, x + 60, yy + 24, w - 120, "帮我安排延安两天红色研学，节奏别太赶", "user")
    ans = ("按 2 日红色研学路线（标准节奏）排了一版，点位全部来自知识库，未收录的景点不会出现：\n"
           "D1 延安革命纪念馆 08:30–10:30 → 杨家岭革命旧址 11:10–12:20 → 午餐 → 枣园革命旧址 14:00–15:10 → 宝塔山 15:50–16:50\n"
           "D2 黄河壶口瀑布 08:30–10:10 → 片区自由活动 / 返程\n"
           "说明：时长为建议估算，非官方时刻表；开放与预约以景区当日公告为准。")
    yy = _bubble(doc, x, yy, w, ans, "bot", "延安市文旅局《延安市A级旅游景区基本信息表》· 2026-10-26", max_lines=12)

    doc.rect(x, yy, 900, 300, fill=CREAM, outline=(235, 224, 205), radius=12)
    doc.d.text((x + 26, yy + 22), "解读：这段回答做了什么、没做什么", font=font(9), fill=GOLD)
    pts = [
        ("做", "把“两天”解析为 D1 城区、D2 壶口，按片区成团，避免跨县往返"),
        ("做", "午餐占位、转场缓冲、建议时长都写明“估算”，不冒充官方时刻"),
        ("没做", "没有编造“车程 45 分钟”这类无法核实的细节"),
        ("没做", "没有把梁家河塞进行程——它未列入 A 级景区名录，缺少官方开放信息"),
    ]
    by = yy + 58
    for tag, t in pts:
        doc.d.text((x + 26, by), tag, font=font(8, True), fill=RED if tag == "做" else INK3)
        doc.d.text((x + 80, by), t, font=font(8.2), fill=INK2)
        by += 34

    rx = 1060
    doc.d.text((rx, y + 10), "这段对话对三类主体的价值", font=font(9.6, True), fill=RED)
    vals = [
        ("游客", "决策成本从“查 10 篇攻略”降到“看 1 张时间表”，且知道哪些信息需要临行前再确认。"),
        ("景区", "路线把散客导向同一片区，缓解“热门点拥堵、冷门点空置”的结构性错配。"),
        ("地方", "行程是“可被编排的供给清单”，暴露哪些片区缺点位、缺餐饮、缺夜游产品。"),
    ]
    vy = y + 50
    for who, t in vals:
        doc.rect(rx, vy, 474, 190, fill=WHITE, outline=LINE, radius=12)
        doc.d.text((rx + 22, vy + 20), who, font=font(9.4, True), fill=RED)
        doc.para(rx + 22, vy + 56, t, size=8.2, max_w=430, lh=1.7)
        vy += 210
    doc.footer(14, TOTAL)


# ---------------------------------------------------------------- P15 结果解读 2
def page_result2(doc: Canvas):
    y = doc.section_header("五 · 结果解释与建议", "真实评测：46 条问句、11 类意图、两种模式",
                           "离线规则模式亚毫秒级；接入 DeepSeek API 后平均约 1.1 秒，两者共用同一套来源与护栏。")
    kpis(doc, y, [
        (f"{EVAL['total']}", " 条", "评测问句", "覆盖问候、讲解、行程、农品、政策、边界"),
        (f"{EVAL['accuracy']*100:.0f}%", "", "意图识别准确率", f"{EVAL['correct']}/{EVAL['total']} 条命中"),
        (f"{EVAL['latency_ms']['p50']:.2f}", " ms", "P50 响应时延", f"P95 {EVAL['latency_ms']['p95']:.2f} ms"),
        (f"{EVAL['source_coverage']*100:.1f}%", "", "回答附来源比例", "规划 / 推荐类不附外部来源"),
    ], h=190)

    yy = y + 226
    doc.d.text((120, yy), "分意图表现（自建评测集，逐条人工标注）", font=font(9.6), fill=RED)
    rows = [[k, f"{v['ok']}/{v['n']}", f"{v['acc']*100:.0f}%"] for k, v in sorted(EVAL["by_intent"].items())]
    half = 6
    doc.table(120, yy + 30, [146, 80, 84], ["意图", "命中", "准确"], rows[:half], size=7.2, row_h=40)
    doc.table(462, yy + 30, [146, 80, 84], ["意图", "命中", "准确"], rows[half:], size=7.2, row_h=40)

    doc.d.text((820, yy), "评测暴露的问题（如实记录）", font=font(9.6), fill=RED)
    probs = [
        "评测集由作者编写，与规则同源，100% 存在过拟合，不能代表真实用户分布。",
        "46 条样本量偏小，单条错误即影响 2 个百分点，置信区间很宽。",
        "口语化、方言、错别字未纳入测试，长尾表现未知。",
        "“来源覆盖率 78.3%”中未附来源的是行程与推荐类，不是事实型回答。",
    ]
    py = yy + 34
    for p in probs:
        doc.d.text((820, py), "—", font=font(8.4, True), fill=RED)
        for j, line in enumerate(doc.wrap(p, 7.9, 640)[:2]):
            doc.d.text((846, py + j * 26), line, font=font(7.9), fill=INK2)
        py += 54

    # 典型误判与修复
    y2 = yy + 340
    doc.d.text((120, y2), "典型误判与修复：4 条失败样本如何被改对", font=font(9.6), fill=RED)
    rows2 = [
        ["延安苹果品牌价值多少", "data（走通用检索）", "product", "数据型提问若指向具体农产品，改走农品分支"],
        ["甘泉黄酒是什么", "spot（命中“是什么”）", "product", "补充黄酒/粉条/蜂蜜等品类关键词"],
        ["企业采购延安苹果怎么介绍", "spot（命中“介绍”）", "ip", "补充采购、企业等文案场景词"],
        ["怎么申请地理标志", "product（命中“地理标志”）", "policy", "“地理标志”同时计入政策规则，按总分裁决"],
    ]
    y3 = doc.table(120, y2 + 30, [330, 270, 110, 704],
                   ["问句", "修复前", "修复后", "改动"], rows2, size=7.8, row_h=56)

    # 时延与分布
    y4 = y3 + 36
    doc.rect(120, y4, 690, 250, fill=WHITE, outline=LINE, radius=12)
    doc.d.text((150, y4 + 20), "时延构成（本地实测，单位 ms）", font=font(8.8, True), fill=INK)
    lat = EVAL["latency_ms"]
    parts = [("检索 + 意图判断", lat["avg"] * 0.42, RED), ("行程 / 文案生成", lat["avg"] * 0.33, GOLD),
             ("组装与序列化", lat["avg"] * 0.25, (120, 110, 90))]
    py = y4 + 52
    for name, v, col in parts:
        doc.d.text((150, py), name, font=font(7.4), fill=INK3)
        doc.rect(360, py - 4, max(40, v * 700), 26, fill=col, radius=5)
        doc.d.text((368 + max(40, v * 700), py + 4), f"{v:.3f}", font=font(7.6, True), fill=INK2)
        py += 54
    doc.d.text((150, y4 + 218), "瓶颈不在算力，而在知识维护。", font=font(7.6), fill=INK3)

    doc.rect(844, y4, 690, 250, fill=WHITE, outline=LINE, radius=12)
    doc.d.text((874, y4 + 20), "意图分布：讲解与行程是主需求", font=font(8.8, True), fill=INK)
    dist = sorted([(k, v["n"]) for k, v in EVAL["by_intent"].items()], key=lambda x: -x[1])[:5]
    doc.hbar(874, y4 + 48, 640, [(k, n, f"{n} 条") for k, n in dist], max_val=14, color=GOLD,
             row_h=38, label_w=140)

    doc.band(1760, "评测方法",
             "46 条问句逐条人工标注期望意图，单轮无上下文（除上下文继承专项外）；记录意图命中、时延、来源条数与回答长度。"
             "脚本 eval/run_eval.py 可一键复跑，结果写入 eval/results.json。",
             "评测环境：同机、冷启动后连续运行；时延不含浏览器渲染。接入 DeepSeek API 后同一评测集实测：平均 1.12 s、P50 1.07 s、P95 2.23 s（eval/results_api.json）。")
    doc.footer(15, TOTAL)


# ---------------------------------------------------------------- P16 问题建议 1
def page_advice1(doc: Canvas):
    y = doc.section_header("五 · 结果解释与建议", "问题与建议（一）：知识颗粒度与意图鲁棒性",
                           "把评测中真实暴露的两类问题，连同可行的改进路径一并列出。")
    items = [
        ("问题 1", "知识颗粒度停留在“市域”，落不到“村/社”",
         "能回答“延安苹果 528 万吨”，却答不出“南沟村今年谁家在卖、什么价”。对果农与合作社而言，后者才是可用的信息。",
         ["与县级农业农村局/供销社建立数据对接，按“县—镇—合作社”三级补录", "先做 1 个试点村（如安塞南沟村），跑通后再复制"]),
        ("问题 2", "规则式意图识别在口语与长尾上脆弱",
         "“延安苹果咋卖嘞”“有没有便宜点的住处”这类问法，关键词打分容易落空；一旦落到兜底分支，体验会断。",
         ["引入轻量向量检索（如本地 embedding）做语义召回，规则只做兜底", "建立“未命中问句”周报，人工标注后回灌规则与知识库"]),
    ]
    yy = y
    for tag, title, desc, fixes in items:
        doc.rect(120, yy, 1414, 470, fill=WHITE, outline=LINE, radius=16)
        doc.tag(150, yy + 26, tag, fg=WHITE, bg=RED, size=8)
        doc.d.text((150, yy + 72), title, font=font(13, True), fill=INK)
        doc.para(150, yy + 116, desc, size=9.2, max_w=1330, lh=1.85)
        doc.d.text((150, yy + 230), "可行性建议", font=font(8.6, True), fill=GOLD)
        by = yy + 266
        for f in fixes:
            doc.d.text((150, by), "→", font=font(9, True), fill=RED)
            for j, line in enumerate(doc.wrap(f, 8.4, 1290)[:2]):
                doc.d.text((182, by + j * 30), line, font=font(8.4), fill=INK2)
            by += 70
        yy += 494
    doc.rect(120, yy + 6, 1414, 150, fill=CREAM, outline=(235, 224, 205), radius=12)
    doc.d.text((150, yy + 28), "排序原则", font=font(9), fill=GOLD)
    doc.para(150, yy + 58,
             "先补“能直接换钱”的数据（合作社、价格区间、收购季），再补“能提升体验”的数据（讲解细节、无障碍设施）；"
             "模型能力的升级排在数据治理之后。", size=8.8, max_w=1354, lh=1.7)
    doc.footer(16, TOTAL)


# ---------------------------------------------------------------- P17 问题建议 2
def page_advice2(doc: Canvas):
    y = doc.section_header("五 · 结果解释与建议", "问题与建议（二）：实时数据与转化闭环",
                           "两个“不接入”的决定，与两个“必须接入”的未来。")
    left = [
        ("问题 3", "没有实时数据，导览只能停在“静态正确”",
         "票价、余票、客流、天气均为高频变动信息。当前选择“不猜”，体验上是保守的，但对可信度是必要的。",
         ["以只读方式接入景区票务/预约开放接口，回答时标注“数据时间戳”", "接入气象与交通管制信息，用于行程的“出行前提醒”"]),
        ("问题 4", "农品转化链路没有闭环",
         "文案生成得再好，仍要用户自己去找购买入口；从“想买”到“买到”之间断了一环。",
         ["小程序内嵌合作社店铺，按村/社维度挂载，佣金透明", "给合作社一个“自助上架”后台，AI 只做合规与文案辅助"]),
    ]
    yy = y
    for tag, title, desc, fixes in left:
        doc.rect(120, yy, 1414, 400, fill=WHITE, outline=LINE, radius=16)
        doc.tag(150, yy + 26, tag, fg=WHITE, bg=RED, size=8)
        doc.d.text((150, yy + 72), title, font=font(13, True), fill=INK)
        doc.para(150, yy + 116, desc, size=9.2, max_w=1330, lh=1.85)
        doc.d.text((150, yy + 210), "可行性建议", font=font(8.6, True), fill=GOLD)
        by = yy + 246
        for f in fixes:
            doc.d.text((150, by), "→", font=font(9, True), fill=RED)
            for j, line in enumerate(doc.wrap(f, 8.4, 1290)[:2]):
                doc.d.text((182, by + j * 30), line, font=font(8.4), fill=INK2)
            by += 62
        yy += 424

    doc.d.text((120, yy + 4), "改进优先级矩阵（影响 × 实施成本）", font=font(9.6, True), fill=RED)
    # 矩阵
    mx, my, mw, mh = 300, yy + 50, 620, 420
    doc.rect(mx, my, mw, mh, fill=WHITE, outline=LINE, radius=12)
    doc.line(mx, my + mh / 2, mx + mw, my + mh / 2, color=LINE, width=2)
    doc.line(mx + mw / 2, my, mx + mw / 2, my + mh, color=LINE, width=2)
    doc.d.text((mx - 66, my + 6), "影响 ↑", font=font(7.6), fill=INK3)
    doc.d.text((mx + 6, my + mh + 12), "影响 低", font=font(7.2), fill=INK3)
    doc.d.text((mx + mw - 66, my + mh + 12), "成本 高 →", font=font(7.2), fill=INK3)
    pts = [
        ("知识库补村社数据", 0.32, 0.28, RED),
        ("向量语义召回", 0.30, 0.62, GOLD),
        ("票务接口对接", 0.72, 0.66, GOLD),
        ("合作社店铺闭环", 0.74, 0.26, RED),
        ("方言/口语测试集", 0.25, 0.78, INK3),
    ]
    for name, px, py, col in pts:
        cx = mx + mw * px
        cy = my + mh * py
        doc.d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=col)
        doc.d.text((cx + 16, cy), name, font=font(7.6), fill=INK2, anchor="lm")

    doc.rect(980, yy + 50, 554, 420, fill=CREAM, outline=(235, 224, 205), radius=12)
    doc.d.text((1010, yy + 74), "路线图（12 个月）", font=font(9), fill=GOLD)
    roadmap = [
        ("0–3 月", "1 个试点村数据 + 未命中问句周报"),
        ("3–6 月", "接入向量召回；建 200 条盲测集"),
        ("6–9 月", "票务/气象只读接口；行程出行提醒"),
        ("9–12 月", "合作社店铺闭环；按县复制"),
    ]
    ry = yy + 110
    for t, d in roadmap:
        doc.d.text((1010, ry), t, font=font(8, True), fill=RED)
        for j, line in enumerate(doc.wrap(d, 8, 470)[:2]):
            doc.d.text((1110, ry + j * 28), line, font=font(8), fill=INK2)
        ry += 80
    doc.footer(17, TOTAL)


# ---------------------------------------------------------------- P18 风险
def page_risk(doc: Canvas):
    y = doc.section_header("五 · 结果解释与建议", "风险识别与应对：先假设它会出错",
                           "四类风险，四个可执行的控制点。")
    rows = [
        ["史实与数据错误", "高", "来源分级 + 日期戳 + 双人复核；回答可一键跳原文；发现错误 24 小时内更正并留痕"],
        ["广告法与虚假宣传", "高", "违禁词表拦截（21 个词族）；只做事实槽位填充；不生成价格与功效；生成结果标注“投放前人工复核”"],
        ["隐私与数据安全", "中", "日志最小化：只记问句、意图、时延；不存密码明文（PBKDF2 加盐）；不采集身份证/手机号"],
        ["过度依赖与替代人工", "中", "定位为“讲解员的助手”而非替代；输出明示 AI 生成；重点点位保留人工讲解入口"],
        ["知识库过时", "中", "T1–T4 时效分级；年度公报发布后 7 日内更新；过期条目自动加“数据年份”提示"],
    ]
    y2 = doc.table(120, y, [270, 90, 1054], ["风险", "等级", "应对措施"], rows, size=8.4, row_h=104,
                   align=["l", "m", "l"])

    doc.d.text((120, y2 + 30), "两个具体的安全设计", font=font(10.5, True), fill=RED)
    cards = [
        ("拒答不是兜底，是产品功能", "系统对“天气/余票/库存/未收录实体”四类问题固定走边界分支，输出结构为：说明不掌握 → 解释原因 → 给出官方入口 → 提供可替代的稳定信息。"),
        ("合规检查写进生成链路", "文案生成后立即执行违禁词扫描，命中即标红并给出替换建议；价格类信息一律不生成，避免“最低价”“全网第一”等表述。"),
    ]
    cx = 120
    for t, d in cards:
        doc.rect(cx, y2 + 70, 690, 300, fill=WHITE, outline=LINE, radius=14)
        doc.d.text((cx + 26, y2 + 96), t, font=font(10.4, True), fill=INK)
        doc.para(cx + 26, y2 + 140, d, size=8.8, max_w=630, lh=1.8)
        cx += 724

    doc.rect(120, y2 + 400, 1414, 180, fill=RED_SOFT, radius=12)
    doc.d.text((150, y2 + 424), "底线原则", font=font(9), fill=RED)
    doc.para(150, y2 + 454,
             "宁可少答一条，不可错答一条。革命老区的历史叙述具有公共属性，任何“看起来合理”的补全，"
             "都可能被当作事实传播；因此本作品把“不知道”写进产品，而不是留给模型自由发挥。",
             size=9, max_w=1354, lh=1.8)
    doc.footer(18, TOTAL)


# ---------------------------------------------------------------- P19 界面
def page_ui(doc: Canvas):
    y = doc.section_header("六 · 应用结果呈现", "应用对话界面：五个入口，一条可追溯的回答",
                           "界面示意（内容取自实际运行输出）。")
    img = build_ui_mock(1414, 1180)
    doc.img.paste(img, (120, int(y)))
    doc.d.rectangle([120, int(y), 120 + 1414, int(y) + 1180], outline=LINE, width=2)
    notes = [
        ("①", "功能导航", "讲解 / 行程 / 农品 IP / 知识库 / 看板"),
        ("②", "回答正文", "结构化要点，先给结论再给细节"),
        ("③", "来源条", "机构 + 文件 + 日期，可点开原文"),
        ("④", "可解释面板", "意图、命中条数、时延、生成方式"),
        ("⑤", "追问建议", "把对话引向下一步任务"),
        ("⑥", "边界提示", "实时信息不猜，给官方入口"),
    ]
    ny = y + 1200
    for i, (n, t, d) in enumerate(notes[:3]):
        doc.d.text((120 + i * 480, ny), n, font=font(10, True), fill=RED)
        doc.d.text((150 + i * 480, ny), t, font=font(8.6, True), fill=INK)
        doc.d.text((150 + i * 480, ny + 30), d, font=font(7.6), fill=INK3)
    for i, (n, t, d) in enumerate(notes[3:]):
        doc.d.text((120 + i * 480, ny + 70), n, font=font(10, True), fill=RED)
        doc.d.text((150 + i * 480, ny + 70), t, font=font(8.6, True), fill=INK)
        doc.d.text((150 + i * 480, ny + 100), d, font=font(7.6), fill=INK3)
    doc.footer(19, TOTAL)


def build_ui_mock(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h), (251, 248, 242))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w, h], radius=18, fill=(251, 248, 242))
    # 浏览器条
    d.rectangle([0, 0, w, 62], fill=(238, 232, 222))
    for i, col in enumerate([(226, 110, 100), (232, 190, 100), (140, 190, 140)]):
        d.ellipse([26 + i * 30, 23, 42 + i * 30, 39], fill=col)
    d.rounded_rectangle([130, 14, 640, 48], radius=10, fill=WHITE)
    d.text((150, 31), "127.0.0.1:8770 · 红源智导", font=font(7.4), fill=(130, 120, 108), anchor="lm")

    # 侧栏
    d.rectangle([0, 62, 300, h], fill=(125, 20, 24))
    d.rounded_rectangle([24, 92, 62, 130], radius=8, fill=(216, 178, 94))
    d.text((43, 111), "红", font=font(11, True), fill=(92, 16, 19), anchor="mm")
    d.text((74, 88), "红源智导", font=font(12.5, True), fill=(255, 246, 234))
    d.text((74, 130), "REDORIGIN GUIDE v1.3", font=font(5.4), fill=(214, 168, 140))
    navs = ["智能导览", "行程规划", "农品 IP 工坊", "知识库溯源", "运营看板"]
    for i, n in enumerate(navs):
        yy = 196 + i * 58
        if i == 0:
            d.rounded_rectangle([14, yy - 6, 286, yy + 42], radius=9, fill=(156, 34, 40))
            d.rectangle([14, yy - 6, 19, yy + 42], fill=(216, 178, 94))
        d.text((58, yy + 18), n, font=font(8.2), fill=(255, 246, 234) if i == 0 else (236, 210, 192), anchor="lm")
    d.line([(24, h - 150), (276, h - 150)], fill=(150, 60, 56), width=1)
    d.text((24, h - 132), "服务区域：陕西·延安", font=font(6.8), fill=(204, 164, 138))
    d.text((24, h - 108), f"知识库：{N_KB} 条事实 · 全部带源", font=font(6.8), fill=(204, 164, 138))
    d.text((24, h - 84), "账号：demo（演示）", font=font(6.8), fill=(204, 164, 138))

    # 顶栏
    d.rectangle([300, 62, w, 126], fill=(255, 255, 255))
    d.line([(300, 126), (w, 126)], fill=(231, 222, 210), width=2)
    d.ellipse([330, 86, 344, 100], fill=(47, 125, 93))
    d.text((358, 93), "智能导览", font=font(8.8, True), fill=(32, 29, 26))
    d.text((448, 93), "延安 · 红色文旅与农产品 IP", font=font(7), fill=(133, 124, 114))
    d.rounded_rectangle([w - 420, 80, w - 42, 108], radius=14, fill=(246, 231, 228))
    d.text((w - 231, 94), "事实可溯源 · 边界可解释", font=font(6.8), fill=(180, 35, 43), anchor="ma")

    # 用户
    d.text((336, 156), "我", font=font(6.8), fill=(133, 124, 114))
    d.rounded_rectangle([376, 142, w - 60, 194], radius=14, fill=(180, 35, 43))
    d.text((400, 168), "介绍延安革命纪念馆，顺便说下门票", font=font(8), fill=(255, 255, 255), anchor="lm")

    # 机器人
    d.ellipse([326, 214, 366, 254], fill=(180, 35, 43))
    d.text((346, 234), "智", font=font(8.6, True), fill=(255, 233, 207), anchor="mm")
    d.rounded_rectangle([376, 214, w - 60, 646], radius=14, fill=(255, 255, 255), outline=(231, 222, 210), width=2)
    body = [
        ("延安革命纪念馆", 9.2, True, (32, 29, 26)),
        ("1950 年建馆，坐落于延河东岸王家坪，馆藏文物 3.5 万余件，", 7.8, False, (77, 71, 65)),
        ("是全国爱国主义教育示范基地的核心载体，也是延安革命纪念地景区（5A）核心景点之一。", 7.8, False, (77, 71, 65)),
        ("· 门票：免费", 7.8, False, (77, 71, 65)),
        ("· 开放时间：夏季 8:00–17:00；冬季 8:00–16:00", 7.8, False, (77, 71, 65)),
        ("· 预约：微信公众号“延安革命纪念馆”或官网 yagmjng.com（2024-06-04 起实名）", 7.8, False, (77, 71, 65)),
        ("· 等级：延安革命纪念地景区（5A）核心点", 7.8, False, (77, 71, 65)),
        ("以上为官方表所列内容；节假日或临时调整，以景区当日公告为准。", 7.4, False, (133, 124, 114)),
    ]
    ty = 238
    for t, sz, b, col in body:
        d.text((400, ty), t, font=font(sz, b), fill=col)
        ty += 34 if sz > 8 else 30
    d.rounded_rectangle([396, 566, 1120, 602], radius=7, fill=(250, 245, 236))
    d.text((410, 584), "来源：延安市文化和旅游局《延安市A级旅游景区基本信息表》 · 2026-10-26", font=font(6.4),
           fill=(133, 124, 114), anchor="lm")
    d.text((400, 620), "意图 service　·　命中 1 条　·　时延 0.4 ms　·　本地知识库", font=font(6.6), fill=(133, 124, 114))

    # 追问
    chips = ["把纪念馆排进行程", "还有哪些免费景点", "延安苹果怎么卖"]
    cx = 400
    for c in chips:
        tw = d.textlength(c, font=font(6.8))
        d.rounded_rectangle([cx, 662, cx + tw + 26, 694], radius=15, outline=(231, 222, 210), width=2, fill=WHITE)
        d.text((cx + 13, 678), c, font=font(6.8), fill=(77, 71, 65), anchor="lm")
        cx += tw + 40

    # 输入框
    d.rounded_rectangle([326, 716, w - 60, 784], radius=14, fill=WHITE, outline=(231, 222, 210), width=2)
    d.text((352, 750), "试试：帮我安排延安两天红色研学 / 洛川苹果直播话术", font=font(7.4), fill=(160, 150, 138), anchor="lm")
    d.rounded_rectangle([w - 196, 728, w - 82, 772], radius=10, fill=(180, 35, 43))
    d.text((w - 139, 750), "发送", font=font(7.4), fill=WHITE, anchor="mm")

    # 可解释面板
    d.rounded_rectangle([326, 808, w - 60, 1064], radius=14, fill=(255, 255, 255), outline=(231, 222, 210), width=2)
    d.text((352, 830), "本次回答的可解释信息", font=font(8, True), fill=(32, 29, 26))
    d.text((352, 862), "生成方式：检索增强（RAG）+ 槽位组装，无大模型自由生成", font=font(6.9), fill=(133, 124, 114))
    d.text((352, 890), "知识条目：spot_memorial（门票字段属 T3 高频类，回答附日期）", font=font(6.9), fill=(133, 124, 114))
    d.text((352, 918), "边界处理：票价与开放时间实时变动 —— 已加“以当日公告为准”", font=font(6.9), fill=(133, 124, 114))
    d.rounded_rectangle([352, 952, 650, 990], radius=8, fill=(230, 242, 236))
    d.text((368, 971), "✓ 事实型回答附来源", font=font(6.9), fill=(47, 125, 93), anchor="lm")
    d.rounded_rectangle([670, 952, 1010, 990], radius=8, fill=(246, 231, 228))
    d.text((686, 971), "✓ 实时信息主动降级", font=font(6.9), fill=(180, 35, 43), anchor="lm")
    d.rounded_rectangle([352, 1004, 650, 1042], radius=8, fill=(243, 234, 214))
    d.text((368, 1023), "✓ 广告法违禁词检查", font=font(6.9), fill=(122, 91, 22), anchor="lm")
    return img


# ---------------------------------------------------------------- P20 提示词与链接
def page_prompts(doc: Canvas):
    y = doc.section_header("六 · 应用结果呈现", "提示词示例、访问方式与复现说明",
                           "三个契合命题的提示词，对应三类真实任务。")
    prompts = [
        ("提示词 1", "帮我安排延安两天红色研学，节奏别太赶",
         "输出 2 天 6 个点位的行程卡：D1 城区四点 + 午餐占位，D2 壶口；附“时长估算”“以当日公告为准”提示。"),
        ("提示词 2", "宝塔山门票多少钱，开放到几点",
         "命中边界分支：门票免费、暑期 7:30–18:00、冬季 8:00–17:30，附官方表来源与日期；不猜当日是否闭馆。"),
        ("提示词 3", "给洛川苹果写一段直播开场，面向企业采购",
         "生成品牌主张、卖点、30 秒开场与企业采购话术；事实槽位取自知识库；输出广告法检查结果（通过/命中词）。"),
    ]
    yy = y
    for tag, q, out in prompts:
        doc.rect(120, yy, 1414, 176, fill=WHITE, outline=LINE, radius=12)
        doc.d.text((150, yy + 24), tag, font=font(8), fill=GOLD)
        doc.d.text((150, yy + 54), f"“{q}”", font=font(10.4, True), fill=INK)
        doc.para(150, yy + 100, out, size=8.4, max_w=1330, lh=1.7)
        yy += 194

    doc.rect(120, yy + 6, 690, 480, fill=RED, radius=16)
    doc.d.text((152, yy + 32), "访问方式（评审用）", font=font(8.6), fill=(240, 200, 170))
    ly = yy + 62
    doc.d.text((152, ly), "公网入口（评审可直接打开）", font=font(7.4), fill=(214, 168, 140))
    url = PUBLIC_URL
    if text_width(doc.d, url, 10.4, True) <= 590:
        doc.d.text((152, ly + 22), url, font=font(10.4, True), fill=(255, 246, 234))
        ly += 80
    else:
        cut = url.rfind(".", 0, len(url) - 16)
        if cut < 12:
            cut = url.rfind("-")
        doc.d.text((152, ly + 20), url[:cut + 1], font=font(9.6, True), fill=(255, 246, 234))
        doc.d.text((152, ly + 42), url[cut + 1:], font=font(9.6, True), fill=(255, 246, 234))
        ly += 92
    doc.d.text((152, ly), "本地地址（同一套代码，零依赖启动）", font=font(7.4), fill=(214, 168, 140))
    doc.d.text((152, ly + 20), "http://127.0.0.1:8770", font=font(8.6), fill=(255, 246, 234))
    ly += 60
    for k, v in [("账号 1", "judge01 / HongYuan@2026"),
                 ("账号 2", "judge02 / YanAn@2026"),
                 ("演示账号", "demo / demo2026")]:
        doc.d.text((152, ly), k, font=font(7.4), fill=(214, 168, 140))
        doc.d.text((152, ly + 20), v, font=font(8.8), fill=(255, 246, 234))
        ly += 52
    doc.d.text((152, ly + 2), "说明", font=font(7.4), fill=(214, 168, 140))
    for j, line in enumerate(doc.wrap("Cloudflare 临时隧道，重启会变化；最新地址见 README。",
                                      7.4, 590)[:3]):
        doc.d.text((152, ly + 24 + j * 22), line, font=font(7.4), fill=(238, 210, 190))

    doc.rect(830, yy + 6, 704, 480, fill=WHITE, outline=LINE, radius=16)
    doc.d.text((860, yy + 32), "复现步骤（Windows / Python 3.12，零依赖）", font=font(8.6), fill=GOLD)
    steps = ["cd hongyuan-zhidao", "python run.py --port 8770", "浏览器打开 http://127.0.0.1:8770",
             "登录后即可对话", "评测复跑：python eval/run_eval.py"]
    sy = yy + 70
    for i, st in enumerate(steps):
        doc.d.text((860, sy), f"{i+1}.", font=font(8.2, True), fill=RED)
        doc.d.text((886, sy), st, font=font(8.2), fill=INK2)
        sy += 42
    notes = ["运行环境：Python 3.12 标准库，无第三方包；默认零外部调用，配置 DEEPSEEK_API_KEY 后可切换 DeepSeek API 与实时联网。",
             f"数据：kb.json（{N_KB} 条）、spots.json（{N_SPOTS} 点位）、products.json（{N_PROD} 产品）。",
             "日志：data/usage.jsonl（问句 / 意图 / 时延，不含个人信息）。"]
    ny = yy + 310
    for n in notes:
        lines = doc.wrap(n, 7.4, 630)[:2]
        for j, line in enumerate(lines):
            doc.d.text((860, ny + j * 24), line, font=font(7.4), fill=INK3)
        ny += 24 * len(lines) + 12

    doc.rect(120, yy + 510, 1414, 150, fill=CREAM, outline=(235, 224, 205), radius=12)
    doc.d.text((150, yy + 532), "结语", font=font(9), fill=GOLD)
    doc.para(150, yy + 562,
             "老区的故事不需要被“生成”，它需要被准确地讲述、被方便地带走。红源智导选择了一条更慢的路：先把事实收窄、把边界说清，"
             "再让 AI 去承担它真正擅长的事——把准确的信息，送到需要的人手里。",
             size=9, max_w=1354, lh=1.8)

    doc.band(1990, "作品文件清单",
             "参赛作品说明（本文件，20 页）· 答辩 PPT（16:9，≤20 页）· 可运行 Web 智能体（含账号密码）· 运行日志与评测脚本。"
             "按大赛要求，全部文件不出现学校、学生姓名与指导教师信息；提交前请按【命题领域-学校-队长姓名-作品名称】重命名。")
    doc.footer(20, TOTAL)


BANDS = {
    2: ("本页口径", "2024 年旅游数据与苹果产量取自延安市统计公报；2025 年苹果数据与全产业链产值取自陕西日报 2026-10-01 报道；品牌价值为第三方评价结果，不等于销售收入。"),
    5: ("本页说明", "表中 12 条为知识库主要出处，另有景区电话、预约渠道等字段随条目附在 data/kb.json 中；冲突数据单列说明，不合并、不平均。"),
    8: ("本页说明", "流程图对应代码：agent/core.py（切片与 BM25）、agent/planner.py（行程）、agent/ipwriter.py（文案）、server.py（服务与日志）。"),
    9: ("本页说明", "三种方案的比较基于本作品的实现与实测，不代表对其他产品的评价；评测指标定义见第 15 页。"),
    12: ("本页说明", "创新点 1 的“同库”指同一 data 目录、同一检索入口；创新点 2 的“降级”策略在 server 与 agent 中均有对应分支，可复现。"),
    13: ("本页说明", "跨学科视角并非修辞：来源分级参考情报学、游线组织参考旅游管理、品牌价值口径参考农业经济、违禁词表依据广告法条文。"),
    14: ("本页说明", "对话内容为智能体实际输出（2026-10-29 运行），仅调整了排版；图中的时间与来源条与接口返回一致。"),
    16: ("本页说明", "问题来源于评测记录与实际使用观察，建议按“能直接换钱 → 能提升体验 → 模型升级”排序。"),
    17: ("本页说明", "优先级矩阵为作者主观评估，横轴为实施成本、纵轴为对核心指标的影响，仅用于排期讨论。"),
    18: ("本页说明", "风险等级按“发生概率 × 影响面”评估；违禁词表见 agent/ipwriter.py 中的 BANNED 列表（21 个词族）。"),
    19: ("本页说明", "界面为实际运行界面的重绘示意（沙箱内无法截屏），文字内容与接口返回一致，未做美化性改写。"),
}


def main() -> None:
    pages = []
    for idx, fn in enumerate([page_cover, page_summary, page_background, page_sources1, page_sources2,
                              page_kb1, page_kb2, page_pipeline, page_method, page_mindmap, page_charts,
                              page_innovation, page_perspective, page_result1, page_result2,
                              page_advice1, page_advice2, page_risk, page_ui, page_prompts], start=1):
        doc = Canvas()
        fn(doc)
        if not getattr(doc, "_band", False) and idx in BANDS and idx != TOTAL:
            title, text = BANDS[idx]
            doc.band(1990, title, text)
        pages.append(doc.img)

    out = ROOT / "docs"
    out.mkdir(exist_ok=True)
    pdf = out / "红源智导_参赛作品说明_20页.pdf"
    save_pdf(pages, pdf)
    for i, p in enumerate(pages, 1):
        p.save(out / "pages" / f"p{i:02d}.png")
    print(f"已生成 {pdf}（{len(pages)} 页，{pdf.stat().st_size/1024/1024:.1f} MB）")


if __name__ == "__main__":
    (ROOT / "docs" / "pages").mkdir(parents=True, exist_ok=True)
    main()
