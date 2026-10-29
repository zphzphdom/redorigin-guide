# -*- coding: utf-8 -*-
"""把文档生成脚本里写死的知识库规模，改为按 data/*.json 实时计算。

运行一次即可（幂等）：python tools/patch_counts.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "tools" / "build_pdf.py"
PPT = ROOT / "tools" / "build_pptx.py"

PDF_DEF = '''PUBLIC_URL = _public_url()
N_KB, N_SPOTS, N_PROD = len(KB), len(SPOTS), len(PRODUCTS)
'''

PPT_DEF = '''PUBLIC_URL = public_url()
N_KB, N_SPOTS, N_PROD = len(KB), len(SPOTS), len(PRODUCTS)
'''

pdf_pairs = [
    ('"13 个点位、31 条事实，逐条注明机构、文件、日期"',
     'f"{N_SPOTS} 个点位、{N_KB} 条事实，逐条注明机构、文件、日期"'),
    ('"6 个地标产品，自动拦截绝对化用语"',
     'f"{N_PROD} 个地标产品，自动拦截绝对化用语"'),
    ('"红源智导反其道而行：把可讲的话收窄到 31 条有出处的事实，把不能讲的话明确说出来。"',
     'f"红源智导反其道而行：把可讲的话收窄到 {N_KB} 条有出处的事实，把不能讲的话明确说出来。"'),
    ('：13 个点位的等级、门票、开放时间、预约电话。',
     '：{N_SPOTS} 个点位的等级、门票、开放时间、预约电话。'),
    ('"13 个点位门票与时间"', 'f"{N_SPOTS} 个点位门票与时间"'),
    ('"数据结构与统计由作者对 data/kb.json 直接计算得出（31 条）。"',
     'f"数据结构与统计由作者对 data/kb.json 直接计算得出（{N_KB} 条）。"'),
    ('f"覆盖：{len(SPOTS)} 个点位 × 8 个字段；13 个点位的门票、开放时间、预约电话全部来自官方表（2026-10-26）。"',
     'f"覆盖：{N_SPOTS} 个点位 × 8 个字段；全部点位的门票、开放时间、预约电话来自官方表（2026-10-26）。"'),
    ('"本方案把“生成”降级为“组织”，把“知识”前置到人工核验过的 31 条事实上；"',
     'f"本方案把“生成”降级为“组织”，把“知识”前置到人工核验过的 {N_KB} 条事实上；"'),
    ('"供给金字塔意味着大量 3A 景区缺讲解 → 讲解功能覆盖 13 个点位而非只做 5A；"',
     'f"供给金字塔意味着大量 3A 景区缺讲解 → 讲解功能覆盖 {N_SPOTS} 个点位而非只做 5A；"'),
    ('"通用文旅助手把“玩”和“买”分开：讲完景点，再让用户跳去电商。红源智导把 13 个点位与 6 个地标产品放进同一个知识库、"',
     'f"通用文旅助手把“玩”和“买”分开：讲完景点，再让用户跳去电商。红源智导把 {N_SPOTS} 个点位与 {N_PROD} 个地标产品放进同一个知识库、"'),
    ('"当一个县的文化资源被拆成 31 条可引用的事实，它才第一次具备了被机器稳定复述的条件；"',
     'f"当一个县的文化资源被拆成 {N_KB} 条可引用的事实，它才第一次具备了被机器稳定复述的条件；"'),
    ('"知识库：31 条事实 · 全部带源"', 'f"知识库：{N_KB} 条事实 · 全部带源"'),
    ('"数据：kb.json（31 条）、spots.json（13 点位）、products.json（6 产品）。"',
     'f"数据：kb.json（{N_KB} 条）、spots.json（{N_SPOTS} 点位）、products.json（{N_PROD} 产品）。"'),
]

ppt_pairs = [
    ('"13 个点位、31 条事实，逐条注明机构、文件、日期"',
     'f"{N_SPOTS} 个点位、{N_KB} 条事实，逐条注明机构、文件、日期"'),
    ('"6 个地标产品；生成即做广告法风险词扫描"',
     'f"{N_PROD} 个地标产品；生成即做广告法风险词扫描"'),
    ('"把可讲的话收窄到 31 条\\n有出处的事实，把不能\\n讲的话明确说出来。"',
     'f"把可讲的话收窄到 {N_KB} 条\\n有出处的事实，把不能\\n讲的话明确说出来。"'),
    ('"13 个点位的等级、门票、开放时间、预约电话"',
     'f"{N_SPOTS} 个点位的等级、门票、开放时间、预约电话"'),
    ('"31 条事实、13 个点位、6 个地标产品，全部结构化存储。"',
     'f"{N_KB} 条事实、{N_SPOTS} 个点位、{N_PROD} 个地标产品，全部结构化存储。"'),
    ('"13 个点位与 6 个地标产品共享一套来源规则；\\n在枣园问“能带走什么”，同一条回答里\\n既有产地事实，也有助农渠道。"',
     'f"{N_SPOTS} 个点位与 {N_PROD} 个地标产品共享一套来源规则；\\n在枣园问“能带走什么”，同一条回答里\\n既有产地事实，也有助农渠道。"'),
]


def patch(path: Path, defs_anchor: str, defs_new: str, pairs: list[tuple[str, str]]) -> None:
    s = path.read_text(encoding="utf-8")
    if "N_KB, N_SPOTS, N_PROD" not in s:
        assert defs_anchor in s, f"anchor missing in {path.name}"
        s = s.replace(defs_anchor, defs_new, 1)
    for old, new in pairs:
        if old in s:
            s = s.replace(old, new)
        else:
            print(f"  [skip] {path.name}: 未找到 {old[:30]}...")
    path.write_text(s, encoding="utf-8")
    print(f"  patched {path.name}")


if __name__ == "__main__":
    patch(PDF, 'PUBLIC_URL = _public_url()\n', PDF_DEF, pdf_pairs)
    patch(PPT, 'PUBLIC_URL = public_url()\n', PPT_DEF, ppt_pairs)
