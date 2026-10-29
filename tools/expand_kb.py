# -*- coding: utf-8 -*-
"""知识库扩容：追加 5 个点位、4 个地标产品，全部带可核验来源。

运行：python tools/expand_kb.py
幂等：已存在的 id 会跳过，可重复执行。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

SRC_TICKET = {
    "name": "延安市文化和旅游局",
    "doc": "延安市A级旅游景区基本信息表",
    "date": "2026-10-26",
    "url": "https://yanan.gov.cn/gk/fdzdgknr/shgy/wtly/wlyw/gsgg/2114647785526538241.html",
}

NEW_SPOTS = [
    {
        "id": "wuyi_memorial", "kb_id": "spot_wuyi_memorial", "name": "吴起中央红军长征胜利纪念园", "area": "吴起",
        "level": "4A", "minutes": 90, "priority": 4, "order": 1, "must": False,
        "one_line": "1935 年 10 月中央红军长征到达吴起镇，长征胜利结束",
        "official": "景区电话 0911-7615205",
        "ticket": "免费", "open_time": "夏季 8:30–17:30；冬季 8:30–17:00",
        "booking": "电话咨询 0911-7615205", "phone": "0911-7615205",
        "tags": ["红色", "长征", "研学"], "aliases": ["吴起纪念园", "长征胜利纪念园"]
    },
    {
        "id": "ansai_culture", "kb_id": "spot_ansai_culture", "name": "安塞区文化艺术馆", "area": "安塞",
        "level": "3A", "minutes": 90, "priority": 3, "order": 1, "must": False,
        "one_line": "腰鼓、剪纸、农民画、陕北说书的集中体验地",
        "official": "场馆电话 0911-6216219",
        "ticket": "免费", "open_time": "夏季 8:00–12:00、14:30–17:30；冬季 8:00–12:00、14:00–17:00",
        "booking": "电话咨询 0911-6216219", "phone": "0911-6216219",
        "tags": ["非遗", "民俗", "亲子", "体验"], "aliases": ["安塞文化艺术馆", "安塞文化馆"]
    },
    {
        "id": "luochuan_meeting", "kb_id": "spot_luochuan_meeting", "name": "洛川会议纪念馆", "area": "洛川",
        "level": "3A", "minutes": 70, "priority": 3, "order": 1, "must": False,
        "one_line": "1937 年 8 月洛川会议召开地，确定全面抗战路线",
        "official": "景区电话 0911-3861545",
        "ticket": "免费", "open_time": "9:00–17:00",
        "booking": "电话咨询 0911-3861545", "phone": "0911-3861545",
        "tags": ["红色", "旧址", "研学"], "aliases": ["洛川会议旧址"]
    },
    {
        "id": "zhidan_memorial", "kb_id": "spot_zhidan_memorial", "name": "刘志丹烈士陵园", "area": "志丹",
        "level": "3A", "minutes": 60, "priority": 3, "order": 1, "must": False,
        "one_line": "纪念西北红军和西北革命根据地主要创建人刘志丹",
        "official": "陵园电话 0911-6621695",
        "ticket": "免费", "open_time": "夏季 8:30–17:30；冬季 8:30–17:00",
        "booking": "电话咨询 0911-6621695", "phone": "0911-6621695",
        "tags": ["红色", "纪念", "研学"], "aliases": ["志丹陵园"]
    },
    {
        "id": "waYaobao", "kb_id": "spot_wayaobao", "name": "瓦窑堡革命旧址", "area": "子长",
        "level": "全国重点文物保护单位（未列入 A 级景区名录）", "minutes": 70, "priority": 4, "order": 1, "must": False,
        "one_line": "1935 年 12 月瓦窑堡会议召开地，抗日民族统一战线策源地",
        "official": "子长市文旅部门 / 旧址管理单位（门票与开放时间未核实）",
        "ticket": "未核实", "open_time": "未核实（出行前请查询官方公告）",
        "booking": "未核实", "phone": "",
        "tags": ["红色", "旧址", "研学"], "aliases": ["瓦窑堡会议旧址", "瓦窑堡"]
    },
]

NEW_KB = [
    {
        "id": "spot_wuyi_memorial", "category": "spot", "title": "吴起中央红军长征胜利纪念园",
        "keywords": ["吴起", "长征", "纪念园", "1935", "胜利山", "中央红军"],
        "text": "1935 年 10 月 19 日，中央红军（陕甘支队）到达陕北吴起镇，中央红军主力的长征胜利结束。纪念园依胜利山而建、层叠铺展，山顶矗立中央红军长征胜利纪念碑；园内吴起革命纪念馆展出当年红军留下的“红军锅”等文物。现为国家 4A 级旅游景区，免费开放。",
        "source": {"name": "光明网", "doc": "一口“红军锅”见证鱼水情——走进陕西吴起中央红军长征胜利纪念园", "date": "2026-10-28", "url": "https://m.gmw.cn/toutiao/2026-10/29/content_39071857.htm"}
    },
    {
        "id": "spot_luochuan_meeting", "category": "spot", "title": "洛川会议纪念馆",
        "keywords": ["洛川会议", "1937", "洛川", "抗日", "旧址", "窑洞"],
        "text": "洛川会议旧址位于延安市洛川县。1937 年 8 月 22 日至 25 日，中共中央政治局扩大会议在此召开，确定了全面抗战的路线，提出中共在统一战线中的独立自主原则。旧址现存小院一座，内有坐北朝南砖砌窑洞两孔，左侧为会议室，右侧为毛泽东居室。现为 3A 级旅游景区，免费开放。",
        "source": {"name": "国家文物局", "doc": "洛川会议旧址", "date": "2014-08-27", "url": "http://www.ncha.gov.cn/art/2014/8/28/art_1756_112848.html"}
    },
    {
        "id": "spot_zhidan_memorial", "category": "spot", "title": "刘志丹烈士陵园",
        "keywords": ["刘志丹", "志丹", "烈士陵园", "爱国主义教育", "西北红军"],
        "text": "刘志丹烈士陵园位于志丹县，是为纪念西北红军和西北革命根据地主要创建人之一刘志丹而建。2017 年 7 月 31 日，陵园“全国爱国主义教育示范基地”揭牌；同时是全国红色旅游经典景区。现为 3A 级旅游景区，免费开放。",
        "source": {"name": "中国文明网", "doc": "刘志丹烈士陵园全国爱国主义教育示范基地揭牌", "date": "2017-07-31", "url": "http://sxya.wenming.cn/yw/201708/t20170801_4654549.shtml"}
    },
    {
        "id": "spot_ansai_culture", "category": "spot", "title": "安塞区文化艺术馆",
        "keywords": ["安塞", "腰鼓", "剪纸", "农民画", "陕北说书", "非遗"],
        "text": "安塞区文化艺术馆（安塞区文化文物馆）位于安塞区文化艺术中心裙楼，是集历史文物展示与民间艺术传承于一体的综合性场馆。安塞腰鼓、安塞剪纸、安塞农民画、陕北说书等非遗在此集中展示，游客可现场观看腰鼓表演、体验剪纸。现为 3A 级旅游景区，免费开放。",
        "source": {"name": "延安新闻网", "doc": "安塞非遗文化魅力多 夏日经济活力足", "date": "2025-07-18", "url": "https://www.yanews.cn/bendi/2025/07-19/q19KZdeD.html"}
    },
    {
        "id": "spot_wayaobao", "category": "spot", "title": "瓦窑堡革命旧址",
        "keywords": ["瓦窑堡", "子长", "1935", "瓦窑堡会议", "抗日民族统一战线", "旧址"],
        "text": "瓦窑堡革命旧址位于子长市。1935 年 11 月至 1936 年 6 月，中共中央、中华苏维埃共和国临时中央政府等在此驻扎；1935 年 12 月下旬中共中央政治局会议（瓦窑堡会议）在此召开，讨论抗日民族统一战线问题；12 月 27 日毛泽东作《论反对日本帝国主义的策略》报告。子长是中央红军长征的落脚点、抗日东征的出发地。该旧址未列入延安市 A 级景区名录，门票与开放时间请以官方公告为准。",
        "source": {"name": "央视网", "doc": "瓦窑堡旧址焕新生 陕西子长推动老城保护与民生福祉共同发展", "date": "2026-04-05", "url": "https://ysxw.cctv.cn/article.html?item_id=18413199755159117468&toc_style_id=feeds_default"}
    },
    {
        "id": "product_yanan_millet", "category": "product", "title": "延安小米",
        "keywords": ["延安小米", "小米", "地理标志", "小杂粮", "宝塔山图形"],
        "text": "“延安小米”是延安的地理标志品牌，其地理标志图形商标（第 10503400 号）以延安宝塔山图形代表产地。陕北是全国小米主产区之一，延安小米在当地被视为红色记忆与日常主食的结合；延安市市场监管部门将其列入地理标志运用促进工程的重点品牌之一。",
        "source": {"name": "中国市场监管报", "doc": "如何申请地理标志商标（延安小米图形商标示例）", "date": "2017-03-13", "url": "http://pc.cmrnn.com.cn/shtml/zggsb/20170314/93140.html"}
    },
    {
        "id": "product_gi_2016", "category": "product", "title": "甘泉豆腐、吴起荞麦香醋、黄龙蜂蜜",
        "keywords": ["甘泉豆腐", "吴起荞麦香醋", "黄龙蜂蜜", "地理标志保护产品", "2016"],
        "text": "2016 年 12 月 28 日，原国家质检总局发布 2016 年第 128 号公告，批准甘泉豆腐、甘泉黄酒、吴起荞麦香醋、黄龙蜂蜜等为国家地理标志保护产品。这批产品与洛川苹果、延川红枣、黄龙核桃、子长粉条等共同构成延安的地理标志矩阵（全市地理标志保护产品 9 个、有效地理标志商标 34 件，2024 年底）。",
        "source": {"name": "延安日报", "doc": "吴起荞麦香醋、黄龙蜂蜜、甘泉豆腐、甘泉黄酒成为国家地理标志保护产品", "date": "2017-01-05", "url": "https://paper.yanews.cn/yarb/20170105/html/content_20170105009001.htm"}
    },
]

NEW_PRODUCTS = [
    {
        "id": "yanan_millet", "name": "延安小米", "aliases": ["小米", "黄小米"],
        "region": "延安市（黄土高原杂粮区）",
        "facts": {
            "origin": "陕西省延安市（黄土高原小米主产区）",
            "gi": "地理标志图形商标（第 10503400 号，以宝塔山图形代表产地）",
            "taste": "颗粒饱满、熬粥黏稠，是陕北传统主食",
            "story": "延安市市场监管部门将“延安小米”列入地理标志运用促进工程重点品牌，与苹果、红枣等共同构成区域品牌矩阵。"
        },
        "source": {"name": "中国市场监管报", "doc": "如何申请地理标志商标（延安小米图形商标示例）", "date": "2017-03-13", "url": "http://pc.cmrnn.com.cn/shtml/zggsb/20170314/93140.html"}
    },
    {
        "id": "ganquan_tofu", "name": "甘泉豆腐", "aliases": ["甘泉豆腐干", "豆腐"],
        "region": "延安市甘泉县",
        "facts": {
            "origin": "陕西省延安市甘泉县",
            "gi": "国家地理标志保护产品（2016 年 12 月 28 日原国家质检总局 2016 年第 128 号公告批准）",
            "taste": "以当地泉水点制，豆香浓、口感细嫩"
        },
        "source": {"name": "延安日报", "doc": "吴起荞麦香醋、黄龙蜂蜜、甘泉豆腐、甘泉黄酒成为国家地理标志保护产品", "date": "2017-01-05", "url": "https://paper.yanews.cn/yarb/20170105/html/content_20170105009001.htm"}
    },
    {
        "id": "wuqi_vinegar", "name": "吴起荞麦香醋", "aliases": ["荞麦醋", "吴起醋"],
        "region": "延安市吴起县",
        "facts": {
            "origin": "陕西省延安市吴起县",
            "gi": "国家地理标志保护产品（2016 年 12 月 28 日原国家质检总局 2016 年第 128 号公告批准）",
            "taste": "以荞麦为原料固态发酵，酸味柔和、带粮香"
        },
        "source": {"name": "延安日报", "doc": "吴起荞麦香醋、黄龙蜂蜜、甘泉豆腐、甘泉黄酒成为国家地理标志保护产品", "date": "2017-01-05", "url": "https://paper.yanews.cn/yarb/20170105/html/content_20170105009001.htm"}
    },
    {
        "id": "huanglong_honey", "name": "黄龙蜂蜜", "aliases": ["黄龙蜜", "蜂蜜"],
        "region": "延安市黄龙县",
        "facts": {
            "origin": "陕西省延安市黄龙县（黄龙山林区）",
            "gi": "国家地理标志保护产品（2016 年 12 月 28 日原国家质检总局 2016 年第 128 号公告批准）",
            "taste": "林区蜜源多样，蜜色浅、花香清"
        },
        "source": {"name": "延安日报", "doc": "吴起荞麦香醋、黄龙蜂蜜、甘泉豆腐、甘泉黄酒成为国家地理标志保护产品", "date": "2017-01-05", "url": "https://paper.yanews.cn/yarb/20170105/html/content_20170105009001.htm"}
    },
]


def merge(path: Path, new_items: list[dict], key: str = "id") -> tuple[int, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    have = {x.get(key) for x in data}
    added = [x for x in new_items if x.get(key) not in have]
    data.extend(added)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(data), len(added)


def main() -> None:
    n1, a1 = merge(DATA / "spots.json", NEW_SPOTS)
    n2, a2 = merge(DATA / "kb.json", NEW_KB)
    n3, a3 = merge(DATA / "products.json", NEW_PRODUCTS)
    print(f"spots.json      {n1} 条（新增 {a1}）")
    print(f"kb.json         {n2} 条（新增 {a2}）")
    print(f"products.json   {n3} 条（新增 {a3}）")


if __name__ == "__main__":
    main()
