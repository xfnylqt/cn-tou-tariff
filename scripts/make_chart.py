#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成全国峰谷价差排行图（assets/spread_ranking.svg）。"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

FONT = "-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
rows = [p for p in index["provinces"] if p["has_residential_tou"] and p["spread"]]
noprice = [p for p in index["provinces"] if p["has_residential_tou"] and not p["spread"]]
rows.sort(key=lambda r: -r["spread"])

W = 880
row_h = 25
top = 78
bottom = 62
H = top + len(rows) * row_h + bottom
L = 128
bar_w = W - L - 96
vmax = max(r["spread"] for r in rows)

parts = ['<rect width="%d" height="%d" fill="#FAF9F6" rx="12"/>' % (W, H)]
parts.append('<text x="28" y="34" font-family="%s" font-size="16" font-weight="500" fill="#2C2C2A">'
             '全国居民峰谷电价价差排行</text>' % FONT)
parts.append('<text x="28" y="56" font-family="%s" font-size="12" fill="#7A7873">'
             '价差 = 峰段电价 − 谷段电价（元/kWh），共 %d 个省级行政区。采集日期 2026-10-09</text>'
             % (FONT, len(rows)))


def color(v):
    if v >= 0.4:
        return "#185FA5"
    if v >= 0.2:
        return "#378ADD"
    return "#85B7EB"


for i, r in enumerate(rows):
    y = top + i * row_h
    name = r["region"]
    if len(name) > 8:
        name = name[:7] + "…"
    bw = r["spread"] / vmax * bar_w
    parts.append('<text x="%d" y="%.1f" text-anchor="end" font-family="%s" font-size="12" '
                 'fill="#2C2C2A">%s</text>' % (L - 12, y + 13, FONT, esc(name)))
    parts.append('<rect x="%d" y="%.1f" width="%.1f" height="14" rx="3" fill="%s"/>'
                 % (L, y + 4, bw, color(r["spread"])))
    parts.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="11.5" fill="#5F5E5A">%.4f</text>'
                 % (L + bw + 8, y + 15, FONT, r["spread"]))

y0 = top + len(rows) * row_h + 22
parts.append('<line x1="28" y1="%d" x2="%d" y2="%d" stroke="#E8E6DF" stroke-width="1"/>'
             % (y0 - 10, W - 28, y0 - 10))
parts.append('<text x="28" y="%d" font-family="%s" font-size="12" fill="#7A7873">'
             '另有 %d 个省级行政区已确认执行居民峰谷分时电价，但电价值尚未从官方原文核实：%s</text>'
             % (y0 + 8, FONT, len(noprice), "、".join(p["region"] for p in noprice)))
y1 = y0 + 24
parts.append('<text x="28" y="%d" font-family="%s" font-size="12" fill="#7A7873">'
             '另有 %d 个省级行政区居民生活用电不执行峰谷分时电价（天津、辽宁、吉林、黑龙江、'
             '云南、贵州、西藏、青海、新疆），详见 README。</text>'
             % (y1 + 8, FONT, index["without_residential_tou"]))


svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="100%%" role="img" '
       'font-family="%s"><title>全国居民峰谷电价价差排行</title>%s</svg>'
       % (W, H, FONT, "".join(parts)))

(ASSETS / "spread_ranking.svg").write_text(svg, encoding="utf-8")
print("已生成 assets/spread_ranking.svg（%d 个省级行政区）" % len(rows))
