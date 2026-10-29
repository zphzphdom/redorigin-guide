# -*- coding: utf-8 -*-
"""生成答辩用 PPT（16:9，18 页）。

运行：python tools/build_pptx.py
输出：docs/红源智导_答辩PPT_16-9.pptx
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

from build_pdf import build_ui_mock  # noqa: E402

KB = json.loads((ROOT / "data" / "kb.json").read_text(encoding="utf-8"))
SPOTS = json.loads((ROOT / "data" / "spots.json").read_text(encoding="utf-8"))
PRODUCTS = json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))
EVAL = json.loads((ROOT / "eval" / "results.json").read_text(encoding="utf-8"))

def public_url() -> str:
    f = ROOT / "docs" / "PUBLIC_URL.txt"
    if f.exists():
        u = f.read_text(encoding="utf-8-sig").strip()
        if u.startswith("http"):
            return u
    return "http://127.0.0.1:8770"


PUBLIC_URL = public_url()
N_KB, N_SPOTS, N_PROD = len(KB), len(SPOTS), len(PRODUCTS)

RED = RGBColor(0xB4, 0x23, 0x2B)
DEEP = RGBColor(0x7D, 0x14, 0x18)
GOLD = RGBColor(0xC1, 0x9A, 0x3F)
GOLD_L = RGBColor(0xF3, 0xEA, 0xD6)
INK = RGBColor(0x20, 0x1D, 0x1A)
INK2 = RGBColor(0x4D, 0x47, 0x41)
INK3 = RGBColor(0x85, 0x7C, 0x72)
LINE = RGBColor(0xE7, 0xDE, 0xD2)
PAPER = RGBColor(0xFB, 0xF8, 0xF2)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREEN = RGBColor(0x2F, 0x7D, 0x5D)

W, H = Inches(13.333), Inches(7.5)
FONT = "微软雅黑"


def set_font(run, size=16, bold=False, color=INK, italic=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = FONT
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", FONT)


def slide_bg(slide, color=PAPER):
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = color


def textbox(slide, x, y, w, h, text, size=16, bold=False, color=INK, align=PP_ALIGN.LEFT,
            line_spacing=1.4, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        run = p.add_run()
        run.text = line
        set_font(run, size, bold, color)
    return box


def rect(slide, x, y, w, h, fill=WHITE, line=None, radius=0.08, shadow=False):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
                                   x, y, w, h)
    if radius:
        try:
            shape.adjustments[0] = radius
        except Exception:
            pass
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(1)
    shape.shadow.inherit = shadow
    shape.text_frame.text = ""
    return shape


def header(slide, kicker, title, sub=""):
    rect(slide, 0, 0, W, Inches(0.075), fill=RED, radius=0)
    textbox(slide, Inches(0.62), Inches(0.34), Inches(8), Inches(0.3), kicker, 11, False, RED)
    textbox(slide, Inches(0.6), Inches(0.6), Inches(12.1), Inches(0.75), title, 30, True, INK)
    if sub:
        textbox(slide, Inches(0.62), Inches(1.34), Inches(12.1), Inches(0.4), sub, 12.5, False, INK3)
    rect(slide, Inches(0.62), Inches(1.78 if sub else 1.55), Inches(12.1), Emu(9525), fill=LINE, radius=0)
    return Inches(1.95) if sub else Inches(1.72)


def footer(slide, page, total=18):
    textbox(slide, Inches(0.62), Inches(6.98), Inches(5), Inches(0.3), "红源智导 · 答辩演示", 9, False, INK3)
    textbox(slide, Inches(5.4), Inches(6.98), Inches(3), Inches(0.3), "命题：AI赋能革命老区振兴", 9, False, INK3,
            PP_ALIGN.CENTER)
    textbox(slide, Inches(11.9), Inches(6.98), Inches(0.8), Inches(0.3), f"{page:02d}", 9, False, INK3, PP_ALIGN.RIGHT)


def note(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def kpi(slide, x, y, w, h, value, unit, label, accent=RED):
    rect(slide, x, y, w, h, fill=WHITE, line=LINE, radius=0.1)
    rect(slide, x, y, Inches(0.055), h, fill=accent, radius=0)
    textbox(slide, x + Inches(0.22), y + Inches(0.16), w - Inches(0.4), Inches(0.55), value, 34, True, accent)
    textbox(slide, x + Inches(0.22), y + Inches(0.72), w - Inches(0.3), Inches(0.7), label, 12, False, INK2)
    if unit:
        textbox(slide, x + w - Inches(0.55), y + Inches(0.42), Inches(0.5), Inches(0.3), unit, 10, False, INK3,
                PP_ALIGN.RIGHT)


def table(slide, x, y, w, data, widths=None, font_size=11, row_h=0.42, header_fill=GOLD_L):
    rows, cols = len(data), len(data[0])
    shape = slide.shapes.add_table(rows, cols, x, y, w, Inches(row_h * rows))
    tb = shape.table
    for c in range(cols):
        tb.columns[c].width = Inches(widths[c]) if widths else Inches(w.inches / cols)
    for r in range(rows):
        tb.rows[r].height = Inches(row_h)
        for c in range(cols):
            cell = tb.cell(r, c)
            cell.text = str(data[r][c])
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.05)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = header_fill if r == 0 else (WHITE if r % 2 else RGBColor(0xFD, 0xFA, 0xF4))
            for p in cell.text_frame.paragraphs:
                for run in p.runs:
                    set_font(run, font_size, r == 0, INK2 if r == 0 else INK)
    return shape


def bar_chart(slide, x, y, w, h, categories, values, color=RED, title="", fmt="#,##0"):
    cd = CategoryChartData()
    cd.categories = categories
    cd.add_series(title or "数值", values)
    gf = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, w, h, cd)
    ch = gf.chart
    ch.has_legend = False
    ch.has_title = False
    plot = ch.plots[0]
    plot.gap_width = 90
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.font.size = Pt(11)
    dl.font.bold = True
    dl.font.color.rgb = INK2
    dl.number_format = fmt
    dl.number_format_is_linked = False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    ser = plot.series[0]
    ser.format.fill.solid()
    ser.format.fill.fore_color.rgb = color
    ca = ch.category_axis
    ca.format.line.color.rgb = LINE
    ca.tick_labels.font.size = Pt(11)
    ca.tick_labels.font.color.rgb = INK2
    ca.has_major_gridlines = False
    va = ch.value_axis
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = RGBColor(0xF0, 0xEA, 0xE0)
    va.format.line.fill.background()
    va.tick_labels.font.size = Pt(9)
    va.tick_labels.font.color.rgb = INK3
    return gf


def new_deck():
    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H
    return prs


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


# ------------------------------------------------------------------ 01 封面
def s01(prs):
    s = blank(prs)
    slide_bg(s, DEEP)
    # 装饰
    rect(s, Inches(8.4), Inches(0), Inches(4.9), Inches(7.5), fill=RGBColor(0x8C, 0x1A, 0x20), radius=0)
    rect(s, Inches(0), Inches(6.9), Inches(13.333), Inches(0.6), fill=RGBColor(0x6B, 0x11, 0x15), radius=0)
    textbox(s, Inches(0.9), Inches(0.85), Inches(8), Inches(0.35), "第二届人工智能应用创新大赛 · 答辩", 13, False,
            RGBColor(0xEF, 0xC9, 0xB2))
    rect(s, Inches(0.9), Inches(1.28), Inches(1.6), Emu(28575), fill=GOLD, radius=0)
    textbox(s, Inches(0.86), Inches(1.55), Inches(8), Inches(1.2), "红源智导", 66, True, RGBColor(0xFF, 0xF6, 0xEA))
    textbox(s, Inches(0.9), Inches(2.85), Inches(8), Inches(0.4), "REDORIGIN  GUIDE   ·   v1.3", 15, False, RGBColor(0xD8, 0xB2, 0x5E))
    textbox(s, Inches(0.9), Inches(3.35), Inches(8.2), Inches(1.0),
            "面向革命老区延安的“红旅 + 农品”\n一体化 AI 导览智能体", 25, False, RGBColor(0xFF, 0xEE, 0xDE), line_spacing=1.35)
    textbox(s, Inches(0.9), Inches(4.6), Inches(8), Inches(0.4),
            "让每一次到访更懂历史，让每一颗果子卖得更远。", 14, False, RGBColor(0xE4, 0xB9, 0x9E))
    chips = [("事实可溯源", 0.9), ("边界可解释", 2.5), ("文案合规", 4.1), ("助农可落地", 5.6)]
    for text, x in chips:
        shape = rect(s, Inches(x), Inches(5.12), Inches(1.45), Inches(0.42), fill=DEEP, line=RGBColor(0xC8, 0xA0, 0x78), radius=0.4)
        tf = shape.text_frame
        tf.word_wrap = False
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = text
        set_font(run, 10.5, False, RGBColor(0xF0, 0xD6, 0xC2))
    textbox(s, Inches(0.9), Inches(6.15), Inches(7.6), Inches(0.4), "2026 年 10 月　｜　参赛团队：红源智导", 11,
            False, RGBColor(0xCE, 0xA0, 0x84))
    # 右侧大字
    textbox(s, Inches(8.9), Inches(2.2), Inches(3.9), Inches(1.6), str(N_KB), 96, True, RGBColor(0x9C, 0x2A, 0x2E))
    textbox(s, Inches(9.05), Inches(3.95), Inches(3.6), Inches(0.5), "条有出处的事实", 16, False, RGBColor(0xC8, 0x8E, 0x6E))
    textbox(s, Inches(9.05), Inches(4.55), Inches(3.6), Inches(1.2),
            "这是我们敢让 AI 开口的\n全部底气。", 14, False, RGBColor(0xB0, 0x7E, 0x64), line_spacing=1.5)
    note(s, "开场 20 秒：我们只做一件事——让 AI 在革命老区把话说准。这不只是一个导览工具，"
            "而是一套把‘可引用的史实’和‘可卖出去的农品’放进同一个知识库的方法。")
    footer(s, 1)


# ------------------------------------------------------------------ 02 问题
def s02(prs):
    s = blank(prs)
    y = header(s, "01 · 为什么做", "老区不缺流量，缺的是把流量留下来",
               "2024 年延安的数据，三个数字指向同一个问题：停留太短、消费太浅。")
    items = [("4731.54 万人次", "2024 年接待国内游客，同比 +12.7%", "人来了"),
             ("805.23 元", "游客人均花费，同比 +2.2%", "钱没留下"),
             ("39 家", "全市星级宾馆，其中四星 10 家", "住不下来")]
    x = Inches(0.62)
    for v, d, tag in items:
        rect(s, x, y, Inches(3.85), Inches(2.0), fill=WHITE, line=LINE, radius=0.08)
        textbox(s, x + Inches(0.28), y + Inches(0.22), Inches(3.3), Inches(0.3), tag, 11, True, GOLD)
        textbox(s, x + Inches(0.28), y + Inches(0.58), Inches(3.4), Inches(0.6), v, 30, True, RED)
        textbox(s, x + Inches(0.28), y + Inches(1.28), Inches(3.3), Inches(0.6), d, 11, False, INK3)
        x += Inches(4.12)

    y2 = y + Inches(2.3)
    textbox(s, Inches(0.62), y2, Inches(12), Inches(0.4), "三个“最后一公里”", 18, True, RED)
    probs = [("讲解", "散客听到的常是段子，不是史实；讲解供给集中在团队时段。"),
             ("消费", "看完就走，缺少把“看”变成“待一天、买一箱”的动线。"),
             ("品牌", "洛川苹果品牌价值 883.26 亿元，果农却拿不到能直接用的文案。")]
    x = Inches(0.62)
    for name, text in probs:
        rect(s, x, y2 + Inches(0.5), Inches(3.9), Inches(1.55), fill=WHITE, line=LINE, radius=0.08)
        rect(s, x, y2 + Inches(0.5), Inches(0.05), Inches(1.55), fill=RED, radius=0)
        textbox(s, x + Inches(0.22), y2 + Inches(0.66), Inches(3.4), Inches(0.3), name, 14, True, INK)
        textbox(s, x + Inches(0.22), y2 + Inches(1.02), Inches(3.45), Inches(0.9), text, 11, False, INK3, line_spacing=1.35)
        x += Inches(4.12)
    note(s, "三个数字分别对应‘人来了、钱没留下、住不下来’。这三个问题不是靠一个聊天机器人能解决的，"
            "它们需要的是‘准确的信息 + 可执行的动线 + 能卖货的话术’，这正是我们要做的三件事。")
    footer(s, 2)


# ------------------------------------------------------------------ 03 政策
def s03(prs):
    s = blank(prs)
    y = header(s, "01 · 为什么是现在", "“人工智能+老区”已经不是倡议，是任务",
               "2026 年 3 月的中办、国办文件，第一次把“人工智能+”写进革命老区振兴。")
    quote = ("在具备条件的革命老区实施“人工智能+”行动，优化数字经济发展环境。")
    rect(s, Inches(0.62), y, Inches(12.1), Inches(1.45), fill=RGBColor(0x7D, 0x14, 0x18), radius=0.06)
    textbox(s, Inches(0.95), y + Inches(0.2), Inches(11.4), Inches(0.5),
            "中共中央办公厅、国务院办公厅《关于加快革命老区振兴发展的意见》", 12, False, RGBColor(0xE8, 0xC0, 0xA6))
    textbox(s, Inches(0.95), y + Inches(0.58), Inches(11.4), Inches(0.6), quote, 20, True, WHITE)

    y2 = y + Inches(1.75)
    rows = [
        ["2026-03-13", "中办、国办《关于加快革命老区振兴发展的意见》", "“人工智能+”行动；红色文化数字化传播平台；区域红色研学基地"],
        ["2021-02-20", "国务院 国发〔2021〕3号", "地理标志农产品认证与品牌打造；红色旅游高质量发展"],
        ["2024-05-06", "文旅部等 5 部门《智慧旅游创新发展行动计划》", "到 2027 年 8 大行动、20 项任务；通用 AI、AIGC 提升服务"],
        ["2025-08-26", "国务院 国发〔2025〕11号", "“人工智能+”与经济社会各领域深度融合"],
    ]
    table(s, Inches(0.62), y2, Inches(12.1), [["时间", "文件", "与本作品直接相关的表述"]] + rows,
          widths=[1.35, 4.4, 6.35], font_size=11, row_h=0.62)
    textbox(s, Inches(0.62), y2 + Inches(3.4), Inches(12), Inches(0.4),
            "我们的判断：政策给了方向，但落地缺的是“可被机器稳定复述的县域知识”。", 13, True, RED)
    note(s, "这一页只讲一个点：2026 年 2 月 13 日中办、国办文件明确写了“在具备条件的革命老区实施人工智能+行动”。"
            "政策已经到位，真正的瓶颈在数据和知识——这正是我们切入的位置。")
    footer(s, 3)


# ------------------------------------------------------------------ 04 方案
def s04(prs):
    s = blank(prs)
    y = header(s, "02 · 我们做了什么", "一个不敢编的导览智能体",
               "四个模块，共用一套“来源—日期—边界”的规则。")
    mods = [("讲解", "RAG 检索 + 来源回填", f"{N_SPOTS} 个点位、{N_KB} 条事实，逐条注明机构、文件、日期", RED),
            ("行程", "片区聚类 + 节奏约束", "只编排已核验点位；同一天只在一个片区活动", GOLD),
            ("农品", "事实槽位 + 合规检查", f"{N_PROD} 个地标产品；生成即做广告法风险词扫描", RGBColor(0x8A, 0x6A, 0x2A)),
            ("边界", "实时信息不猜", "票价/时间给官方表；天气/客流直说“不掌握”", RGBColor(0x4A, 0x4A, 0x4A))]
    x = Inches(0.62)
    for name, how, desc, col in mods:
        rect(s, x, y, Inches(2.9), Inches(2.35), fill=WHITE, line=LINE, radius=0.08)
        rect(s, x, y, Inches(2.9), Inches(0.07), fill=col, radius=0)
        textbox(s, x + Inches(0.24), y + Inches(0.3), Inches(2.4), Inches(0.4), name, 20, True, INK)
        textbox(s, x + Inches(0.24), y + Inches(0.82), Inches(2.5), Inches(0.3), how, 10.5, True, RED)
        textbox(s, x + Inches(0.24), y + Inches(1.2), Inches(2.45), Inches(1.0), desc, 10.5, False, INK3, line_spacing=1.35)
        x += Inches(3.08)

    y2 = y + Inches(2.65)
    textbox(s, Inches(0.62), y2, Inches(6.0), Inches(0.4), "它不是“问答机器人”", 17, True, RED)
    pts = ["游客在枣园问“能带走什么”，回答里既有洛川苹果的产地事实，也有助农渠道；",
           "同一条回答里，两类内容都带来源，都能被追问“凭什么”；",
           "不能回答的（天气、余票、未收录产品），明确说“不掌握”并给官方入口。"]
    yy = y2 + Inches(0.45)
    for p in pts:
        textbox(s, Inches(0.62), yy, Inches(0.3), Inches(0.3), "·", 16, True, GOLD)
        textbox(s, Inches(0.85), yy, Inches(6.1), Inches(0.55), p, 12, False, INK2, line_spacing=1.35)
        yy += Inches(0.55)
    rect(s, Inches(7.35), y2, Inches(5.35), Inches(2.2), fill=GOLD_L, radius=0.06)
    textbox(s, Inches(7.62), y2 + Inches(0.22), Inches(4.9), Inches(0.3), "一句话", 10, False, RGBColor(0x7A, 0x5B, 0x16))
    textbox(s, Inches(7.62), y2 + Inches(0.55), Inches(4.85), Inches(1.5),
            f"把可讲的话收窄到 {N_KB} 条\n有出处的事实，把不能\n讲的话明确说出来。", 17, True, INK, line_spacing=1.45)
    note(s, "四个模块不是四个功能，而是同一套规则的四个出口。讲解解决‘听得懂’，行程解决‘待得住’，"
            "农品解决‘带得走’，边界解决‘不出错’。")
    footer(s, 4)


# ------------------------------------------------------------------ 05 数据来源
def s05(prs):
    s = blank(prs)
    y = header(s, "03 · 数据怎么来", "三类主渠道，全部可点开核对",
               "不用未公开数据、不买数据、不抓个人信息。")
    chans = [("渠道一", "政府统计与公报", "延安市统计局《2024年延安市国民经济和社会发展统计公报》\n2025-05-30", "GDP、游客与花费、苹果产量、居民收入"),
             ("渠道二", "主管部门名录", "延安市文旅局《延安市A级旅游景区基本信息表》\n2026-10-26", f"{N_SPOTS} 个点位的等级、门票、开放时间、预约电话"),
             ("渠道三", "政策与权威媒体", "中国政府网 / 新华社 / 陕西日报 / 陕西省人民政府网\n逐条标注发布日期", "政策原文、品牌价值、产业数据、助农案例")]
    yy = y
    for tag, name, src, use in chans:
        rect(s, Inches(0.62), yy, Inches(12.1), Inches(1.28), fill=WHITE, line=LINE, radius=0.06)
        rect(s, Inches(0.62), yy, Inches(0.06), Inches(1.28), fill=RED, radius=0)
        textbox(s, Inches(0.9), yy + Inches(0.14), Inches(0.9), Inches(0.3), tag, 10, True, GOLD)
        textbox(s, Inches(1.75), yy + Inches(0.1), Inches(3.0), Inches(0.4), name, 15, True, INK)
        textbox(s, Inches(1.75), yy + Inches(0.52), Inches(4.6), Inches(0.7), src, 9.5, False, INK3, line_spacing=1.3)
        textbox(s, Inches(6.6), yy + Inches(0.36), Inches(5.9), Inches(0.7), use, 11.5, False, INK2)
        yy += Inches(1.45)

    rect(s, Inches(0.62), yy + Inches(0.05), Inches(12.1), Inches(0.95), fill=GOLD_L, radius=0.06)
    textbox(s, Inches(0.9), yy + Inches(0.22), Inches(11.6), Inches(0.6),
            "校验：每条事实至少 1 个官方来源；数字类再找 1 个独立来源比对；冲突单列说明，不合并、不平均。",
            12, True, RGBColor(0x6B, 0x50, 0x14))
    note(s, "数据来源是评审最容易质疑的地方，所以我们把‘能不能点开原文’当成硬指标。"
            "12 条主要出处全部在作品说明第 5 页列了机构、文件名、日期和站点。")
    footer(s, 5)


# ------------------------------------------------------------------ 06 知识库
def s06(prs):
    s = blank(prs)
    y = header(s, "03 · 数据怎么用", "一条事实 = 一段话 + 一个出处",
               f"{N_KB} 条事实、{N_SPOTS} 个点位、{N_PROD} 个地标产品，全部结构化存储。")
    rect(s, Inches(0.62), y, Inches(6.2), Inches(2.75), fill=RGBColor(0x26, 0x22, 0x1F), radius=0.04)
    code = [
        '{',
        '  "id": "product_luochuan_apple",',
        '  "category": "product",',
        '  "title": "洛川苹果",',
        '  "text": "2024 年品牌价值 883.26 亿元……",',
        '  "source": {',
        '    "name": "陕西省人民政府",',
        '    "doc": "81个商标获评2024年陕西好商标",',
        '    "date": "2024-12-02",',
        '    "url": "https://www.shaanxi.gov.cn/..."',
        '  }',
        '}',
    ]
    tb = s.shapes.add_textbox(Inches(0.85), y + Inches(0.2), Inches(5.8), Inches(2.4))
    tf = tb.text_frame
    tf.word_wrap = False
    for i, line in enumerate(code):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.15
        run = p.add_run()
        run.text = line
        set_font(run, 10.5, False, RGBColor(0xE4, 0xDC, 0xD0))

    cats = [("景点", len([k for k in KB if k["category"] == "spot"]), "讲解 / 门票 / 预约"),
            ("政策", len([k for k in KB if k["category"] == "policy"]), "政策解读 / 申报依据"),
            ("市情数据", len([k for k in KB if k["category"] == "history"]), "数据问答 / 趋势"),
            ("农品", len([k for k in KB if k["category"] == "product"]), "产地事实 / 文案槽位"),
            ("交通", len([k for k in KB if k["category"] == "transport"]), "怎么来 / 多长时间")]
    yy = y
    for name, n, use in cats:
        rect(s, Inches(7.15), yy, Inches(5.55), Inches(0.44), fill=WHITE, line=LINE, radius=0.2)
        textbox(s, Inches(7.38), yy + Inches(0.09), Inches(1.2), Inches(0.3), name, 11, True, INK)
        textbox(s, Inches(8.6), yy + Inches(0.09), Inches(0.6), Inches(0.3), f"{n} 条", 10, True, RED)
        textbox(s, Inches(9.35), yy + Inches(0.09), Inches(3.2), Inches(0.3), use, 9.5, False, INK3)
        yy += Inches(0.55)

    rect(s, Inches(0.62), y + Inches(3.0), Inches(6.2), Inches(1.5), fill=WHITE, line=LINE, radius=0.06)
    textbox(s, Inches(0.85), y + Inches(3.15), Inches(5.7), Inches(0.3), "真实条目（原文照录）", 9.5, False, GOLD)
    textbox(s, Inches(0.85), y + Inches(3.45), Inches(5.75), Inches(1.0),
            "洛川苹果 2024 年品牌价值 883.26 亿元，位居陕西商标品牌价值榜首；"
            "种植面积稳定 53 万亩，2024 年产量 112 万吨、产值 140 亿元。", 9.5, False, INK2, line_spacing=1.35)

    rect(s, Inches(7.15), y + Inches(3.0), Inches(5.55), Inches(1.5), fill=GOLD_L, radius=0.06)
    textbox(s, Inches(7.38), y + Inches(3.15), Inches(5.1), Inches(0.3), "为什么不用“一大段话喂模型”", 9.5, False,
            RGBColor(0x7A, 0x5B, 0x16))
    textbox(s, Inches(7.38), y + Inches(3.45), Inches(5.1), Inches(0.95),
            "模型说不清“这句话出自哪一年哪份文件”。结构化把内容与出处绑定，"
            "缺条目时系统知道“我不知道”。", 9.5, False, INK2, line_spacing=1.35)
    note(s, "这一页是作品的技术核心：知识不是一段大文本，而是‘内容 + 出处’的最小单元。"
            "只有这样才能在回答里逐条回填来源，也才能在缺少数据时说出‘不知道’。")
    footer(s, 6)


# ------------------------------------------------------------------ 07 流程
def s07(prs):
    s = blank(prs)
    y = header(s, "03 · 预处理", "从网页原文到一条可引用的回答",
               "全部 Python 标准库实现，无第三方依赖，可断网复现。")
    steps = [("① 采集", "检索官方页面\n保存原文与日期"), ("② 清洗", "去导航 / 广告\n抽取正文与数字"),
             ("③ 结构化", "拆字段：标题 / 正文\n来源 / 日期"), ("④ 校验", "双人复核\n冲突单列说明"),
             ("⑤ 切片", "一条事实一段话\n切为问答单元"), ("⑥ 索引", "中文二元组 + BM25\n标题关键词加权"),
             ("⑦ 路由", "意图识别\n上下文继承"), ("⑧ 组装", "答案 + 来源回填\n+ 时效提示")]
    x0, y0 = Inches(0.62), y
    bw, bh, gap = Inches(2.72), Inches(1.02), Inches(0.24)
    for i, (t, d) in enumerate(steps):
        col = i // 4
        row = i % 4
        x = x0 + row * (bw + gap)
        yb = y0 + col * (bh + Inches(0.32))
        rect(s, x, yb, bw, bh, fill=WHITE, line=LINE, radius=0.06)
        rect(s, x, yb, bw, Inches(0.05), fill=RED if col == 0 else (GREEN if col == 1 else RGBColor(0x36, 0x5C, 0x8A)), radius=0)
        textbox(s, x + Inches(0.16), yb + Inches(0.12), bw - Inches(0.3), Inches(0.3), t, 12, True, INK)
        textbox(s, x + Inches(0.16), yb + Inches(0.4), bw - Inches(0.28), Inches(0.6), d, 9.5, False, INK3, line_spacing=1.25)
        if row < 3:
            textbox(s, x + bw + Inches(0.02), yb + Inches(0.34), Inches(0.2), Inches(0.3), "›", 16, True, GOLD)

    y2 = y0 + Inches(2.62)
    textbox(s, Inches(0.62), y2, Inches(12), Inches(0.35), "关键取舍", 14, True, RED)
    rows = [["检索", "字二元组 + BM25（k1=1.5, b=0.75）", "无需向量模型即可离线运行，中文短查询召回稳定"],
            ["路由", "关键词打分 + 会话继承", "把门票/预约/天气导向边界处理，避免自由发挥"],
            ["行程", "片区聚类 + 节奏约束 + 午餐占位", "同一天只在一个片区活动，不虚构景点与车程"],
            ["文案", "事实槽位模板 + 违禁词表", "只填知识库字段，生成后立即做广告法检查"]]
    table(s, Inches(0.62), y2 + Inches(0.36), Inches(12.1), [["环节", "技术手段", "在 Agent 中的用途"]] + rows,
          widths=[1.2, 5.0, 5.9], font_size=10, row_h=0.36)
    note(s, "八个步骤里，真正决定质量的是第四步‘校验’和第三步‘结构化’。"
            "我们刻意不上向量库、不接大模型 API，是为了让评审在任何一台电脑上都能 30 秒跑起来。")
    footer(s, 7)


# ------------------------------------------------------------------ 08 方法
def s08(prs):
    s = blank(prs)
    y = header(s, "04 · 方法", "为什么是“检索增强 + 规则路由”",
               "在事实密度高、容错率低的场景，可解释性比生成能力更重要。")
    rows = [["纯大模型问答", "表达自然、覆盖广", "易编造票价与年份；给不出处；成本与延迟不可控", "不采用"],
            ["纯关键词 FAQ", "可控、快", "问法一变就答不上；无法组织行程与文案", "不采用"],
            ["检索增强 + 规则路由", "答案有出处；边界清晰；可离线", "长尾问法需持续扩充规则；知识维护成本高", "采用"]]
    table(s, Inches(0.62), y, Inches(12.1), [["方案", "优势", "局限", "结论"]] + rows,
          widths=[2.6, 2.6, 5.6, 1.3], font_size=11, row_h=0.72)

    y2 = y + Inches(3.05)
    textbox(s, Inches(0.62), y2, Inches(12), Inches(0.35), "四个可量化的指标", 15, True, RED)
    metrics = [("意图准确率", "是否落到正确功能分支"), ("来源覆盖率", "事实型回答能否给得出处"),
               ("端到端时延", "P50 / P95"), ("边界行为", "该拒答时是否拒答")]
    x = Inches(0.62)
    for name, desc in metrics:
        rect(s, x, y2 + Inches(0.45), Inches(2.9), Inches(1.25), fill=WHITE, line=LINE, radius=0.06)
        textbox(s, x + Inches(0.2), y2 + Inches(0.6), Inches(2.5), Inches(0.35), name, 13, True, INK)
        textbox(s, x + Inches(0.2), y2 + Inches(1.0), Inches(2.5), Inches(0.6), desc, 10, False, INK3)
        x += Inches(3.08)
    textbox(s, Inches(0.62), y2 + Inches(1.95), Inches(12), Inches(0.5),
            "老区文旅的容错率极低：一句错的建馆年份或票价，会被游客当成官方信息转发。", 13, True, RED)
    note(s, "我们比较了三条路线，最后选了最不酷的那条。原因很实际：老区文旅的错误会被当作官方信息传播，"
            "所以宁可少答，不可错答。代价是覆盖面有限，收益是每句话都能被追问。")
    footer(s, 8)


# ------------------------------------------------------------------ 09 需求转化
def s09(prs):
    s = blank(prs)
    y = header(s, "04 · 需求转化", "从数据到功能的四次转化",
               "每一次转化都对应一个可验证的功能，而不是一句口号。")
    center = rect(s, Inches(4.35), y, Inches(4.65), Inches(0.95), fill=RED, radius=0.08)
    tf = center.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = "AI 赋能革命老区振兴\n把“来过”变成“记住并带走”"
    set_font(run, 15, True, WHITE)

    blocks = [("流量 → 消费", "游客侧", "行程编排降低决策成本；讲解延长停留；农品承接二次消费", "对应功能：智能导览 · 行程规划", Inches(0.62), y + Inches(1.35)),
              ("文化 → 产品", "运营侧", "史实结构化为可复述条目；点位可组合成线路；回答自带出处", "对应功能：知识库 · 来源回填", Inches(6.9), y + Inches(1.35)),
              ("特产 → 品牌", "农户侧", "地标身份可核验；卖点转成合规文案；渠道事实可查", "对应功能：农品 IP 工坊 · 合规检查", Inches(0.62), y + Inches(3.2)),
              ("数据 → 治理", "政府侧", "缺口清单即改进清单；问句日志反映需求；口径冲突暴露问题", "对应功能：运营看板 · 缺口表", Inches(6.9), y + Inches(3.2))]
    for title, who, desc, mapping, x, yb in blocks:
        rect(s, x, yb, Inches(5.8), Inches(1.55), fill=WHITE, line=LINE, radius=0.06)
        textbox(s, x + Inches(0.24), yb + Inches(0.16), Inches(4.0), Inches(0.35), title, 15, True, RED)
        textbox(s, x + Inches(4.55), yb + Inches(0.2), Inches(1.0), Inches(0.3), who, 9.5, False, INK3)
        textbox(s, x + Inches(0.24), yb + Inches(0.62), Inches(5.3), Inches(0.5), desc, 10.5, False, INK2, line_spacing=1.35)
        textbox(s, x + Inches(0.24), yb + Inches(1.16), Inches(5.3), Inches(0.3), mapping, 9, True, GOLD)
    note(s, "这一页回答‘为什么是这四个功能’。四个转化分别对应游客、运营、农户、政府四个主体，"
            "每个主体都能在本作品里找到一个具体动作。")
    footer(s, 9)


# ------------------------------------------------------------------ 10 数据洞察
def s10(prs):
    s = blank(prs)
    y = header(s, "05 · 数据洞察", "三个结构性事实，决定功能优先级",
               "数据来自前页来源清单，未做估算或插值。")
    textbox(s, Inches(0.62), y, Inches(5.5), Inches(0.3), "① 游客在增长，人均花费仅 805 元", 12, True, INK)
    bar_chart(s, Inches(0.62), y + Inches(0.35), Inches(5.7), Inches(2.4), ["2023", "2024"], [4198.77, 4731.54],
              color=RED, title="接待游客（万人次）")
    textbox(s, Inches(0.62), y + Inches(2.78), Inches(5.5), Inches(0.3), "接待国内游客（万人次），2024 年同比 +12.7%",
            9, False, INK3)

    textbox(s, Inches(6.9), y, Inches(5.5), Inches(0.3), "② 景区供给呈“金字塔”", 12, True, INK)
    rows = [["5A 级", "4 家", "头部稀缺"], ["4A 级", "9 家", "中坚"], ["3A 级", "49 家", "大量缺讲解"]]
    table(s, Inches(6.9), y + Inches(0.45), Inches(5.8), [["等级", "数量", "含义"]] + rows,
          widths=[1.5, 1.5, 2.8], font_size=11, row_h=0.5)
    textbox(s, Inches(6.9), y + Inches(2.5), Inches(5.8), Inches(0.6),
            "全市 A 级景区 62 个；星级宾馆 39 家。", 10, False, INK3)

    y2 = y + Inches(3.2)
    textbox(s, Inches(0.62), y2, Inches(12), Inches(0.3), "③ 苹果是“压舱石”，品牌价值与县域产值相差一个量级", 12, True, INK)
    kpis = [("332 万亩", "2025 年种植面积"), ("528 万吨", "2025 年产量"), ("292.4 亿元", "2025 年鲜果产值"),
            ("619.9 亿元", "全产业链综合产值"), ("883.26 亿元", "洛川苹果品牌价值（≠产值）")]
    x = Inches(0.62)
    for v, l in kpis:
        rect(s, x, y2 + Inches(0.38), Inches(2.3), Inches(0.95), fill=WHITE, line=LINE, radius=0.08)
        textbox(s, x + Inches(0.18), y2 + Inches(0.48), Inches(2.0), Inches(0.4), v, 17, True, RED if "883" not in v else GOLD)
        textbox(s, x + Inches(0.18), y2 + Inches(0.88), Inches(2.0), Inches(0.35), l, 8.5, False, INK3)
        x += Inches(2.42)
    note(s, "三个事实分别对应三个功能决策：人均花费低→做行程；3A 多→讲解不只做 5A；"
            "品牌价值远高于产值→文案要能直接给合作社用。特别注意：883.26 亿是品牌价值，不是产值，我们没有混用。")
    footer(s, 10)


# ------------------------------------------------------------------ 11 创新 1
def s11(prs):
    s = blank(prs)
    y = header(s, "06 · 创新点 01", "文旅 + 农品同库的“双引擎”",
               "通用助手讲完景点再让你跳去电商；我们把“玩”和“买”放进同一次检索。")
    rect(s, Inches(0.62), y, Inches(5.8), Inches(3.6), fill=WHITE, line=LINE, radius=0.06)
    textbox(s, Inches(0.9), y + Inches(0.2), Inches(5.2), Inches(0.3), "通用方案", 11, True, INK3)
    textbox(s, Inches(0.9), y + Inches(0.58), Inches(5.2), Inches(0.7), "讲解 → 购票 → 跳转电商", 16, True, INK2)
    textbox(s, Inches(0.9), y + Inches(1.35), Inches(5.2), Inches(1.9),
            "两套内容、两个入口、两套审核；\n用户在景点里想买，要自己找链接；\n农品页面讲不出历史，景区页面卖不了货。",
            11, False, INK3, line_spacing=1.5)

    rect(s, Inches(6.9), y, Inches(5.8), Inches(3.6), fill=RGBColor(0x7D, 0x14, 0x18), radius=0.06)
    textbox(s, Inches(7.18), y + Inches(0.2), Inches(5.2), Inches(0.3), "红源智导", 11, True, RGBColor(0xE8, 0xC0, 0xA6))
    textbox(s, Inches(7.18), y + Inches(0.58), Inches(5.2), Inches(0.7), "同库 → 同一次检索 → 同一条回答", 15, True, WHITE)
    textbox(s, Inches(7.18), y + Inches(1.35), Inches(5.2), Inches(1.9),
            f"{N_SPOTS} 个点位与 {N_PROD} 个地标产品共享一套来源规则；\n在枣园问“能带走什么”，同一条回答里\n既有产地事实，也有助农渠道。",
            11, False, RGBColor(0xF2, 0xD8, 0xC8), line_spacing=1.5)

    y2 = y + Inches(3.9)
    textbox(s, Inches(0.62), y2, Inches(12), Inches(0.35), "它带来的三个变化", 14, True, RED)
    items = ["内容侧：两类内容共用一套“来源—日期—边界”规则，审核成本减半",
             "体验侧：行程结束点自然衔接农品，不需要跳 App",
             "商业侧：为“游中带购”提供可审计的话术，而不是一句“欢迎选购”"]
    yy = y2 + Inches(0.45)
    for it in items:
        textbox(s, Inches(0.62), yy, Inches(0.25), Inches(0.3), "·", 14, True, GOLD)
        textbox(s, Inches(0.9), yy, Inches(11.5), Inches(0.3), it, 11.5, False, INK2)
        yy += Inches(0.38)
    note(s, "创新点 1 的关键不是‘都能做’，而是‘同一套规则’。这意味着审核一次、两边都准，"
            "也意味着用户不需要在两个 App 之间跳来跳去。")
    footer(s, 11)


# ------------------------------------------------------------------ 12 创新 2
def s12(prs):
    s = blank(prs)
    y = header(s, "06 · 创新点 02", "把“不知道”设计成一等功能",
               "降级不是失败提示，而是带官方入口的结构化答复。")
    rows = [["天气 / 客流 / 余票", "不掌握实时数据", "说明原因 → 给气象 / 景区官方入口 → 提供可替代的稳定信息"],
            ["未收录的实体", "知识库没有", "明确说未收录 → 列出可回答的相近对象 → 不编造"],
            ["未核实的数据", "来源冲突或缺失", "标注“未核实” → 说明口径差异 → 不合并、不平均"],
            ["超出范围", "非文旅/农品任务", "说明能力边界 → 引导到可做的事"]]
    table(s, Inches(0.62), y, Inches(12.1), [["问题类型", "系统状态", "输出行为"]] + rows,
          widths=[3.1, 3.0, 6.0], font_size=11, row_h=0.7)
    y2 = y + Inches(3.55)
    rect(s, Inches(0.62), y2, Inches(5.9), Inches(1.6), fill=GOLD_L, radius=0.06)
    textbox(s, Inches(0.9), y2 + Inches(0.18), Inches(5.4), Inches(0.3), "为什么这算创新", 10, False, RGBColor(0x7A, 0x5B, 0x16))
    textbox(s, Inches(0.9), y2 + Inches(0.52), Inches(5.35), Inches(0.9),
            "大模型天然倾向于“给一个像样的答案”。我们把“承认不知道”变成产品路径，"
            "并把缺口写进知识库文档，形成可追踪的改进清单。", 10.5, False, INK2, line_spacing=1.4)
    rect(s, Inches(6.9), y2, Inches(5.8), Inches(1.6), fill=WHITE, line=LINE, radius=0.06)
    textbox(s, Inches(7.18), y2 + Inches(0.18), Inches(5.3), Inches(0.3), "对应的工程实现", 10, False, GOLD)
    textbox(s, Inches(7.18), y2 + Inches(0.52), Inches(5.3), Inches(0.9),
            "server / agent 中的边界分支 + 知识库缺口表 + 回答模板；\n可在“知识库溯源”页面直接看到每条事实的出处。",
            10.5, False, INK2, line_spacing=1.4)
    note(s, "这是最容易被忽略、但评审最该看的一页。我们没有把‘答不上来’藏起来，而是把它做成了一条正式的路径。"
            "这背后是一个判断：在老区做 AI，可信度比覆盖面更重要。")
    footer(s, 12)


# ------------------------------------------------------------------ 13 跨学科
def s13(prs):
    s = blank(prs)
    y = header(s, "06 · 独特视角", "把老区当作一个“需要被准确讲述的产品”",
               "五个学科各解决一段，缺一段就会漏。")
    discs = [("情报学", "来源分级与可信度", "T1–T4 时效分级、机构权威性写进数据结构"),
             ("旅游管理", "游线组织与停留时长", "片区聚类 + 节奏约束，半天一个片区"),
             ("农业经济", "区域品牌与价值链", "区分品牌价值与产值，不把 883 亿说成 140 亿"),
             ("法学", "广告法合规前置", "绝对化用语、功效宣称、价格承诺三类红线"),
             ("计算机", "检索增强与结构化生成", "BM25 + 槽位模板，把生成限制在可验证范围")]
    yy = y
    for name, cap, desc in discs:
        rect(s, Inches(0.62), yy, Inches(12.1), Inches(0.78), fill=WHITE, line=LINE, radius=0.06)
        textbox(s, Inches(0.9), yy + Inches(0.1), Inches(1.3), Inches(0.3), name, 13, True, RED)
        textbox(s, Inches(2.35), yy + Inches(0.12), Inches(2.9), Inches(0.3), cap, 10.5, False, INK3)
        textbox(s, Inches(5.4), yy + Inches(0.12), Inches(7.0), Inches(0.4), desc, 10.5, False, INK2)
        yy += Inches(0.88)
    rect(s, Inches(0.62), yy + Inches(0.1), Inches(12.1), Inches(0.95), fill=RED, radius=0.06)
    textbox(s, Inches(0.95), yy + Inches(0.26), Inches(11.4), Inches(0.6),
            "别人在做“更会说话的模型”，我们在做“更少说错的话”。", 19, True, WHITE)
    note(s, "这一页是答辩的‘差异化’页。五个学科不是凑数：来源分级、游线组织、品牌口径、广告法、RAG，"
            "每一个都对应代码里的一个模块。")
    footer(s, 13)


# ------------------------------------------------------------------ 14 对话演示
def s14(prs):
    s = blank(prs)
    y = header(s, "07 · 真实效果", "三条真实对话，三种任务",
               "内容为智能体实际输出，未改写。")
    img_path = ROOT / "docs" / "ui_mock.png"
    if not img_path.exists():
        im = build_ui_mock(1414, 1180)
        im.save(img_path)
    # 左：界面
    s.shapes.add_picture(str(img_path), Inches(0.62), y - Inches(0.2), width=Inches(6.2))
    # 右：三条提示词与结果
    items = [("提示词 1", "帮我安排延安两天红色研学，节奏别太赶",
              "输出 D1 城区四点 + 午餐占位、D2 壶口；标注“时长估算”“以当日公告为准”。"),
             ("提示词 2", "宝塔山门票多少钱，开放到几点",
              "免费；夏季 7:30–18:00、冬季 8:00–17:30；附官方表来源与日期，不猜当日闭馆。"),
             ("提示词 3", "给洛川苹果写一段直播开场，面向企业采购",
              "品牌主张 + 卖点 + 30 秒开场 + 企业话术；事实槽位来自知识库；附广告法检查结果。")]
    yy = y
    for tag, q, a in items:
        rect(s, Inches(6.95), yy, Inches(5.8), Inches(1.55), fill=WHITE, line=LINE, radius=0.06)
        textbox(s, Inches(7.15), yy + Inches(0.12), Inches(1.0), Inches(0.25), tag, 8.5, False, GOLD)
        textbox(s, Inches(7.15), yy + Inches(0.36), Inches(5.4), Inches(0.5), q, 10.5, True, INK, line_spacing=1.25)
        textbox(s, Inches(7.15), yy + Inches(0.9), Inches(5.4), Inches(0.6), a, 8.8, False, INK3, line_spacing=1.3)
        yy += Inches(1.7)
    note(s, "现场演示的时候只跑第一条和第三条。第一条看行程卡，第三条看合规检查——"
            "这两个是最能体现‘准确 + 可用’的功能。")
    footer(s, 14)


# ------------------------------------------------------------------ 15 评测
def s15(prs):
    s = blank(prs)
    y = header(s, "07 · 真实评测", "46 条问句、11 类意图、两种模式",
               "离线亚毫秒级；接入 DeepSeek API 后平均约 1.1 秒，共用同一套来源与护栏。")
    cards = [(f"{EVAL['total']}", "评测问句", "覆盖 11 类意图"), (f"{EVAL['accuracy']*100:.0f}%", "意图准确率",
                                                          f"{EVAL['correct']}/{EVAL['total']} 命中"),
             (f"{EVAL['latency_ms']['p50']:.2f} ms", "P50 时延", f"P95 {EVAL['latency_ms']['p95']:.2f} ms"),
             (f"{EVAL['source_coverage']*100:.1f}%", "附来源比例", "规划/推荐类不计")]
    x = Inches(0.62)
    for v, l, d in cards:
        rect(s, x, y, Inches(2.9), Inches(1.3), fill=WHITE, line=LINE, radius=0.08)
        textbox(s, x + Inches(0.22), y + Inches(0.12), Inches(2.4), Inches(0.5), v, 26, True, RED)
        textbox(s, x + Inches(0.22), y + Inches(0.68), Inches(2.5), Inches(0.3), l, 10.5, True, INK2)
        textbox(s, x + Inches(0.22), y + Inches(0.98), Inches(2.5), Inches(0.3), d, 8.5, False, INK3)
        x += Inches(3.08)

    y2 = y + Inches(1.65)
    rows = [[k, f"{v['ok']}/{v['n']}", f"{v['acc']*100:.0f}%"] for k, v in sorted(EVAL["by_intent"].items())]
    table(s, Inches(0.62), y2, Inches(5.6), [["意图", "命中", "准确率"]] + rows[:6], widths=[2.4, 1.6, 1.6],
          font_size=10, row_h=0.36)
    table(s, Inches(6.55), y2, Inches(5.6), [["意图", "命中", "准确率"]] + rows[6:], widths=[2.4, 1.6, 1.6],
          font_size=10, row_h=0.36)

    y3 = y2 + Inches(2.7)
    rect(s, Inches(0.62), y3, Inches(12.1), Inches(1.15), fill=GOLD_L, radius=0.06)
    textbox(s, Inches(0.9), y3 + Inches(0.15), Inches(11.5), Inches(0.3), "我们主动写下的局限", 10, False,
            RGBColor(0x7A, 0x5B, 0x16))
    textbox(s, Inches(0.9), y3 + Inches(0.45), Inches(11.5), Inches(0.6),
            "评测集自建、与规则同源，存在过拟合；样本量 46 条偏小；口语与方言未覆盖。API 模式实测平均 1.12 s。下一步：建 200 条盲测集。",
            10.5, False, RGBColor(0x5A, 0x45, 0x14))
    note(s, "评测页重点讲两件事：一是数据是真的（脚本可复跑），二是我们主动承认过拟合。"
            "评审更愿意相信一个知道自己在哪儿不准的团队。")
    footer(s, 15)


# ------------------------------------------------------------------ 16 问题建议
def s16(prs):
    s = blank(prs)
    y = header(s, "08 · 问题与建议", "四个真问题，四条可执行的下一步",
               "按“能直接换钱 → 能提升体验 → 模型升级”排序。")
    rows = [["知识颗粒度停在市域", "能答“延安苹果 528 万吨”，答不出“南沟村谁家在卖”",
             "与县级农业农村局/供销社对接，先做 1 个试点村"],
            ["规则路由长尾脆弱", "“咋卖嘞”“有没有便宜住处”容易落空",
             "引入本地向量召回做语义兜底，规则只兜底"],
            ["没有实时数据", "票价、余票、客流只能给静态信息",
             "只读接入票务/预约开放接口，回答标注数据时间戳"],
            ["农品转化不闭环", "生成文案后，用户仍要自己找购买入口",
             "小程序挂载合作社店铺，按村/社维度，佣金透明"]]
    table(s, Inches(0.62), y, Inches(12.1), [["问题", "具体表现", "下一步"]] + rows,
          widths=[3.0, 5.0, 4.1], font_size=10.5, row_h=0.85)
    y2 = y + Inches(4.35)
    rect(s, Inches(0.62), y2, Inches(12.1), Inches(0.85), fill=RED, radius=0.06)
    textbox(s, Inches(0.95), y2 + Inches(0.2), Inches(11.4), Inches(0.5),
            "优先级：先补“能直接换钱”的数据，再补“能提升体验”的功能，模型能力升级排在最后。", 13, True, WHITE)
    note(s, "这一页要显得诚实。四个问题都是真实存在的，而且每一个都给了具体下一步，不是‘持续优化’这种空话。")
    footer(s, 16)


# ------------------------------------------------------------------ 17 风险
def s17(prs):
    s = blank(prs)
    y = header(s, "08 · 风险", "先假设它会出错",
               "四类风险，四个可执行的控制点。")
    rows = [["史实与数据错误", "高", "来源分级 + 日期戳 + 双人复核；可一键跳原文；24 小时内更正留痕"],
            ["广告法与虚假宣传", "高", "21 个词族违禁词拦截；只做事实槽位填充；不生成价格与功效"],
            ["隐私与数据安全", "中", "日志最小化；PBKDF2 加盐存密码；不采集身份证/手机号"],
            ["过度依赖与替代人工", "中", "定位讲解员助手；输出明示 AI 生成；重点点位保留人工讲解"]]
    table(s, Inches(0.62), y, Inches(12.1), [["风险", "等级", "应对"]] + rows,
          widths=[2.8, 1.0, 8.3], font_size=10.5, row_h=0.8)
    y2 = y + Inches(4.15)
    textbox(s, Inches(0.62), y2, Inches(12), Inches(0.35), "底线原则", 13, True, RED)
    textbox(s, Inches(0.62), y2 + Inches(0.4), Inches(12), Inches(0.7),
            "宁可少答一条，不可错答一条。革命老区的历史叙述具有公共属性，任何“看起来合理”的补全，"
            "都可能被当作事实传播。", 12, False, INK2, line_spacing=1.4)
    note(s, "风险页不要说‘没有风险’。我们列了四个，并且每一个都有工程上的控制点，"
            "比如违禁词表是写死在代码里的，不是写在制度里的。")
    footer(s, 17)


# ------------------------------------------------------------------ 18 结语
def s18(prs):
    s = blank(prs)
    slide_bg(s, DEEP)
    rect(s, Inches(0), Inches(0), W, Inches(0.09), fill=GOLD, radius=0)
    textbox(s, Inches(0.9), Inches(0.7), Inches(11), Inches(0.4), "10 · 结语与访问方式", 12, False,
            RGBColor(0xE0, 0xB4, 0x94))
    textbox(s, Inches(0.86), Inches(1.25), Inches(11.6), Inches(1.2),
            "把准确的信息，送到需要的人手里。", 40, True, RGBColor(0xFF, 0xF6, 0xEA))
    textbox(s, Inches(0.9), Inches(2.35), Inches(11.4), Inches(0.9),
            "老区的故事不需要被“生成”，它需要被准确地讲述、被方便地带走。\n我们选择先收窄事实、说清边界，再让 AI 去承担它真正擅长的事。",
            14, False, RGBColor(0xF0, 0xD2, 0xBC), line_spacing=1.5)

    rect(s, Inches(0.9), Inches(3.55), Inches(5.6), Inches(2.55), fill=RGBColor(0x92, 0x1D, 0x24), radius=0.06)
    textbox(s, Inches(1.18), Inches(3.75), Inches(5.0), Inches(0.3), "访问方式", 10, False, RGBColor(0xE8, 0xC0, 0xA6))
    textbox(s, Inches(1.18), Inches(3.98), Inches(4.95), Inches(0.30), PUBLIC_URL, 10.5, True, WHITE)
    textbox(s, Inches(1.18), Inches(4.34), Inches(4.95), Inches(0.24), "本地：http://127.0.0.1:8770", 8.5, False, RGBColor(0xF0, 0xD2, 0xBC))
    for i, (k, v) in enumerate([("账号 1", "judge01 / HongYuan@2026"), ("账号 2", "judge02 / YanAn@2026"),
                                ("演示账号", "demo / demo2026")]):
        textbox(s, Inches(1.18), Inches(4.72 + i * 0.42), Inches(1.1), Inches(0.3), k, 9.5, False, RGBColor(0xE0, 0xB4, 0x94))
        textbox(s, Inches(2.35), Inches(4.72 + i * 0.42), Inches(3.6), Inches(0.3), v, 10, False, WHITE)

    rect(s, Inches(6.85), Inches(3.55), Inches(5.55), Inches(2.55), fill=RGBColor(0x92, 0x1D, 0x24), radius=0.06)
    textbox(s, Inches(7.13), Inches(3.75), Inches(5.0), Inches(0.3), "复现（Windows / Python 3.12，零依赖）", 10, False,
            RGBColor(0xE8, 0xC0, 0xA6))
    for i, line in enumerate(["cd hongyuan-zhidao", "python run.py --port 8770", "打开 http://127.0.0.1:8770",
                              "python eval/run_eval.py  # 复跑评测",
                              "可选：DEEPSEEK_API_KEY → API + 实时联网"]):
        textbox(s, Inches(7.13), Inches(4.08 + i * 0.4), Inches(5.0), Inches(0.3), line, 9.5, False,
                RGBColor(0xF6, 0xDE, 0xCC))
    textbox(s, Inches(0.9), Inches(6.5), Inches(11.6), Inches(0.4),
            "谢谢各位评委。欢迎追问任何一条数据：它都能被点开核对。", 13, False, RGBColor(0xE0, 0xB4, 0x94))
    note(s, "收尾一句话：欢迎追问任何一条数据。这不是话术，是我们真的把每一条都放了链接。")
    footer(s, 18)


def main():
    prs = new_deck()
    for fn in [s01, s02, s03, s04, s05, s06, s07, s08, s09, s10,
               s11, s12, s13, s14, s15, s16, s17, s18]:
        fn(prs)
    out = ROOT / "docs"
    out.mkdir(exist_ok=True)
    path = out / "红源智导_答辩PPT_16-9.pptx"
    prs.save(path)
    print(f"已生成 {path}（{len(prs.slides.__iter__.__self__._sldIdLst)} 页，{path.stat().st_size/1024:.0f} KB）")


if __name__ == "__main__":
    main()
