# -*- coding: utf-8 -*-
"""极简中文 PDF 排版引擎（Pillow 绘制 + 多页 PDF 输出）。

为什么自己写：本机沙箱内浏览器/Office 导出均不可用，为保证"可复现、可离线"，
用 Pillow 直接排版为 200dpi 位图页面再合成 PDF。版式、字号、栅格全部由代码控制。
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = Path(r"C:\Windows\Fonts")
REG = str(FONT_DIR / "msyh.ttc")
BOLD = str(FONT_DIR / "msyhbd.ttc")
HEI = str(FONT_DIR / "simhei.ttf")

# 品牌色
RED = (180, 35, 43)
RED_DEEP = (125, 20, 24)
RED_SOFT = (246, 231, 228)
GOLD = (193, 154, 63)
GOLD_SOFT = (243, 234, 214)
INK = (32, 29, 26)
INK2 = (77, 71, 65)
INK3 = (133, 124, 114)
LINE = (231, 222, 210)
PAPER = (251, 248, 242)
WHITE = (255, 255, 255)
GREEN = (47, 125, 93)
BLUE = (54, 92, 138)
CREAM = (250, 245, 236)

DPI = 200
A4_W, A4_H = 1654, 2339
PX = DPI / 72.0


def pt(v: float) -> int:
    return int(round(v * PX))


_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def font(size_pt: float, bold: bool = False, hei: bool = False) -> ImageFont.FreeTypeFont:
    path = HEI if hei else (BOLD if bold else REG)
    key = (path, pt(size_pt))
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, pt(size_pt), index=0)
    return _font_cache[key]


def text_width(draw: ImageDraw.ImageDraw, s: str, size_pt: float, bold: bool = False) -> float:
    return draw.textlength(s, font=font(size_pt, bold))


class Canvas:
    def __init__(self, w: int = A4_W, h: int = A4_H, bg=PAPER):
        self.w, self.h = w, h
        self.img = Image.new("RGB", (w, h), bg)
        self.d = ImageDraw.Draw(self.img)

    # ---------- 文本 ----------
    def txt(self, x, y, s, size=10.5, color=INK, bold=False, anchor="la", hei=False):
        self.d.text((x, y), s, font=font(size, bold, hei), fill=color, anchor=anchor)
        return y

    def wrap(self, s: str, size: float, max_w: float, bold: bool = False) -> list[str]:
        out = []
        for para in s.split("\n"):
            if not para:
                out.append("")
                continue
            line = ""
            for ch in para:
                if ch == " ":
                    cand = line + ch
                    if text_width(self.d, cand, size, bold) <= max_w:
                        line = cand
                        continue
                if text_width(self.d, line + ch, size, bold) > max_w and line:
                    out.append(line)
                    line = ch
                else:
                    line += ch
            if line:
                out.append(line)
        return out

    def para(self, x, y, s, size=10.5, color=INK, max_w=1414, lh=1.78, bold=False,
             first_indent=0, space_after=0):
        lines = self.wrap(s, size, max_w - first_indent, bold)
        step = size * lh * PX
        for i, line in enumerate(lines):
            self.d.text((x + (first_indent if i == 0 else 0), y), line, font=font(size, bold), fill=color)
            y += step
        return y + space_after

    def bullet(self, x, y, s, size=10.5, color=INK, max_w=1330, gap=14, lh=1.72, mark="—", mcolor=RED):
        self.d.text((x, y), mark, font=font(size, True), fill=mcolor)
        lines = self.wrap(s, size, max_w, False)
        step = size * lh * PX
        for line in lines:
            self.d.text((x + 34, y), line, font=font(size), fill=color)
            y += step
        return y + gap

    def label(self, x, y, s, size=8.5, color=INK3):
        self.d.text((x, y), s, font=font(size), fill=color)

    # ---------- 形状 ----------
    def rect(self, x, y, w, h, fill=None, outline=None, width=2, radius=14):
        if radius:
            self.d.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill, outline=outline, width=width)
        else:
            self.d.rectangle([x, y, x + w, y + h], fill=fill, outline=outline, width=width)

    def line(self, x1, y1, x2, y2, color=LINE, width=2):
        self.d.line([x1, y1, x2, y2], fill=color, width=width)

    def tag(self, x, y, s, fg=RED, bg=RED_SOFT, size=8.5, pad_x=14, pad_y=7, radius=8):
        tw = text_width(self.d, s, size) + pad_x * 2
        th = size * PX * 1.6 + pad_y
        self.rect(x, y, tw, th, fill=bg, radius=radius)
        self.d.text((x + pad_x, y + th / 2), s, font=font(size), fill=fg, anchor="lm")
        return x + tw + 10

    # ---------- 组件 ----------
    def section_header(self, section: str, title: str, sub: str = ""):
        self.d.rectangle([0, 0, self.w, 14], fill=RED)
        self.d.text((120, 96), section, font=font(9), fill=RED)
        self.d.text((120, 130), title, font=font(20, True), fill=INK)
        y = 130 + pt(20) * 1.95
        if sub:
            self.d.text((120, y), sub, font=font(10), fill=INK3)
            y += pt(10) * 1.7
        self.d.line([(120, y + 18), (self.w - 120, y + 18)], fill=LINE, width=2)
        return y + 70

    def footer(self, page: int, total: int, title="红源智导 · 参赛作品说明"):
        y = self.h - 96
        self.d.line([(120, y - 18), (self.w - 120, y - 18)], fill=LINE, width=1)
        self.d.text((120, y), title, font=font(7.6), fill=INK3)
        self.d.text((self.w / 2, y), "命题：AI赋能革命老区振兴", font=font(7.6), fill=INK3, anchor="ma")
        self.d.text((self.w - 120, y), f"{page:02d} / {total:02d}", font=font(7.6), fill=INK3, anchor="ra")

    def kpi(self, x, y, w, h, value, unit, label, note="", accent=RED):
        self.rect(x, y, w, h, fill=WHITE, outline=LINE, radius=16)
        self.d.rectangle([x, y, x + 6, y + h], fill=accent)
        size = 24.0
        while size > 13 and text_width(self.d, value, size, True) > w - 96:
            size -= 1
        self.d.text((x + 30, y + 26), value, font=font(size, True), fill=accent)
        vw = text_width(self.d, value, size, True)
        self.d.text((x + 36 + vw, y + 26 + size * PX * 0.6), unit, font=font(9), fill=INK3)
        self.d.text((x + 30, y + 104), label, font=font(9.2), fill=INK2)
        if note:
            ny = y + 136
            for line in self.wrap(note, 7.4, w - 60)[:2]:
                self.d.text((x + 30, ny), line, font=font(7.4), fill=INK3)
                ny += 24

    def band(self, y, title, text, sources=""):
        """页面底部的“本页来源 / 说明”信息带，用于收口版面并交代出处。"""
        self._band = True
        self.d.line([(120, y), (1534, y)], fill=(226, 214, 197), width=1)
        self.d.text((120, y + 18), title, font=font(8), fill=GOLD)
        yy = y + 46
        for line in self.wrap(text, 8.2, 1380)[:3]:
            self.d.text((120, yy), line, font=font(8.2), fill=INK2)
            yy += 27
        if sources:
            for line in self.wrap(sources, 7.2, 1380)[:2]:
                self.d.text((120, yy + 4), line, font=font(7.2), fill=INK3)
                yy += 24

    def table(self, x, y, widths, headers, rows, size=8.6, row_h=44, header_bg=CREAM,
              zebra=True, align=None):
        align = align or ["l"] * len(headers)
        cx = x
        total_w = sum(widths)
        self.rect(x, y, total_w, row_h, fill=header_bg, radius=0)
        for i, hd in enumerate(headers):
            self.d.text((cx + 12, y + row_h / 2), hd, font=font(size, True), fill=INK2, anchor="lm")
            cx += widths[i]
        y += row_h
        for r, row in enumerate(rows):
            if zebra and r % 2 == 1:
                self.d.rectangle([x, y, x + total_w, y + row_h], fill=(253, 250, 244))
            cx = x
            for i, cell in enumerate(row):
                lines = self.wrap(str(cell), size, widths[i] - 20)
                ty = y + row_h / 2 - (len(lines) - 1) * size * PX * 0.62
                for line in lines[:2]:
                    anchor = "lm" if align[i] == "l" else ("rm" if align[i] == "r" else "mm")
                    px = cx + 12 if align[i] == "l" else (cx + widths[i] - 12 if align[i] == "r" else cx + widths[i] / 2)
                    self.d.text((px, ty), line, font=font(size), fill=INK, anchor=anchor)
                    ty += size * PX * 1.28
                cx += widths[i]
            self.d.line([(x, y + row_h), (x + total_w, y + row_h)], fill=(240, 234, 224), width=1)
            y += row_h
        return y

    # ---------- 图表 ----------
    def bar_chart(self, x, y, w, h, labels, series, colors=None, unit="", value_fmt="{:.0f}",
                  max_val=None, legend=True):
        colors = colors or [RED]
        pad_l, pad_b, pad_t = 70, 60, 30
        plot_x, plot_y = x + pad_l, y + pad_t
        plot_w, plot_h = w - pad_l - 20, h - pad_b - pad_t
        mv = max_val or max(max(s) for s in series) * 1.18
        # 网格
        for g in range(5):
            gy = plot_y + plot_h * g / 4
            self.d.line([(plot_x, gy), (plot_x + plot_w, gy)], fill=(240, 234, 224), width=1)
            self.d.text((plot_x - 12, gy), value_fmt.format(mv * (4 - g) / 4), font=font(7.4), fill=INK3, anchor="rm")
        n = len(labels)
        group_w = plot_w / n
        bw = group_w * 0.62 / max(1, len(series))
        for i, lab in enumerate(labels):
            gx = plot_x + group_w * i + group_w * 0.19
            for si, s in enumerate(series):
                v = s[i]
                bh = plot_h * v / mv
                bx = gx + si * bw
                self.d.rectangle([bx, plot_y + plot_h - bh, bx + bw * 0.86, plot_y + plot_h], fill=colors[si % len(colors)])
                self.d.text((bx + bw * 0.43, plot_y + plot_h - bh - 22), value_fmt.format(v),
                            font=font(8, True), fill=INK2, anchor="ma")
            self.d.text((plot_x + group_w * i + group_w / 2, plot_y + plot_h + 18), lab,
                        font=font(8.2), fill=INK2, anchor="ma")
        self.d.line([(plot_x, plot_y + plot_h), (plot_x + plot_w, plot_y + plot_h)], fill=LINE, width=2)
        if unit:
            self.d.text((plot_x - 64, plot_y - 6), unit, font=font(7.2), fill=INK3)

    def hbar(self, x, y, w, rows, max_val=None, color=RED, size=8.6, row_h=52, label_w=330):
        mv = max_val or max(v for _, v in rows) * 1.12
        for i, (lab, v, note) in enumerate(rows):
            ry = y + i * row_h
            self.d.text((x, ry + row_h / 2), lab, font=font(size), fill=INK, anchor="lm")
            bw = (w - label_w - 130) * v / mv
            self.d.rectangle([x + label_w, ry + 12, x + label_w + bw, ry + row_h - 12], fill=color)
            self.d.text((x + label_w + bw + 14, ry + row_h / 2), note, font=font(size, True), fill=INK2, anchor="lm")
        return y + row_h * len(rows)

    def donut(self, cx, cy, r, parts, thickness=52):
        total = sum(v for _, v, _ in parts)
        start = -90
        for lab, v, col in parts:
            extent = 360 * v / total
            self.d.arc([cx - r, cy - r, cx + r, cy + r], start=start, end=start + extent,
                       fill=col, width=thickness)
            start += extent
        self.d.ellipse([cx - r + thickness, cy - r + thickness, cx + r - thickness, cy + r - thickness], fill=PAPER)

    def flow(self, x, y, steps, box_w=250, box_h=100, gap=54, vertical=False):
        """横向/纵向流程：box + 箭头。steps: [(title, desc, color)]"""
        pos = []
        for i, (title, desc, col) in enumerate(steps):
            if vertical:
                bx, by = x, y + i * (box_h + gap)
            else:
                bx, by = x + i * (box_w + gap), y
            self.rect(bx, by, box_w, box_h, fill=WHITE, outline=LINE, radius=12)
            self.d.rectangle([bx, by, bx + box_w, by + 5], fill=col)
            self.d.text((bx + 18, by + 22), title, font=font(9.2, True), fill=INK)
            for j, line in enumerate(self.wrap(desc, 7.6, box_w - 36)[:2]):
                self.d.text((bx + 18, by + 22 + pt(9.2) * 1.5 + j * pt(7.6) * 1.5), line, font=font(7.6), fill=INK3)
            pos.append((bx, by))
        for i in range(len(steps) - 1):
            if vertical:
                x1, y1 = pos[i][0] + box_w / 2, pos[i][1] + box_h
                x2, y2 = x1, y1 + gap
                self.line(x1, y1 + 6, x2, y2 - 12, color=GOLD, width=3)
                self.d.polygon([(x2 - 8, y2 - 14), (x2 + 8, y2 - 14), (x2, y2 - 2)], fill=GOLD)
            else:
                x1, y1 = pos[i][0] + box_w, pos[i][1] + box_h / 2
                x2, y2 = x1 + gap, y1
                self.line(x1 + 6, y1, x2 - 12, y1, color=GOLD, width=3)
                self.d.polygon([(x2 - 14, y2 - 8), (x2 - 14, y2 + 8), (x2 - 2, y2)], fill=GOLD)
        return pos


def pagoda(draw: ImageDraw.ImageDraw, cx: int, base_y: int, scale: float, color):
    """写意宝塔轮廓（几何近似，非写实）。"""
    tiers = 9
    w0 = 190 * scale
    for i in range(tiers):
        t = i / tiers
        w = w0 * (1 - t * 0.55)
        h = 34 * scale * (1 - t * 0.35)
        y = base_y - (i + 1) * 40 * scale
        draw.rectangle([cx - w / 2, y, cx + w / 2, y + h], fill=color)
        draw.polygon([(cx - w / 2 - 16 * scale, y), (cx + w / 2 + 16 * scale, y),
                      (cx + w / 2 + 6 * scale, y - 10 * scale), (cx - w / 2 - 6 * scale, y - 10 * scale)], fill=color)
    top = base_y - tiers * 40 * scale
    draw.rectangle([cx - 4 * scale, top - 60 * scale, cx + 4 * scale, top + 10 * scale], fill=color)
    draw.ellipse([cx - 12 * scale, top - 78 * scale, cx + 12 * scale, top - 54 * scale], fill=color)


def save_pdf(pages: list[Image.Image], path: Path, quality: int = 88):
    pages[0].save(path, "PDF", resolution=DPI, save_all=True, append_images=pages[1:], quality=quality)
