#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按省份查询分时电价（纯标准库，零依赖）。

用法：
    python scripts/query.py --list                        # 列出所有已收录省份
    python scripts/query.py --province 浙江                # 查询指定省份
    python scripts/query.py --province 广东 --json         # JSON 输出
    python scripts/query.py --sort-by spread               # 按峰谷价差排序
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def load_index():
    return json.loads((DATA / "index.json").read_text(encoding="utf-8"))


def load_province(name_or_code):
    idx = load_index()
    key = name_or_code.strip()
    for p in idx["provinces"]:
        if key in (p["region"], p["code"], p["file"], p["file"].replace(".json", "")):
            return json.loads((DATA / p["file"]).read_text(encoding="utf-8")), p
    return None, None


def fmt_rows(provinces):
    rows = [
        ("省份", "用户类型", "峰段", "谷段", "峰价", "谷价", "价差", "可信度"),
    ]
    for p in provinces:
        rows.append((
            p["region"],
            (p.get("customer_type") or "")[:14],
            p.get("peak") or "-",
            p.get("valley") or "-",
            _num(p.get("peak_price")),
            _num(p.get("valley_price")),
            _num(p.get("spread")),
            p.get("confidence", ""),
        ))
    return rows


def _num(v):
    return "-" if v is None else ("%.4f" % v if isinstance(v, float) else str(v))


def print_table(rows):
    widths = [max(_disp_len(r[i]) for r in rows) for i in range(len(rows[0]))]
    for ri, r in enumerate(rows):
        line = "  ".join(_pad(c, widths[i]) for i, c in enumerate(r))
        print(line)
        if ri == 0:
            print("  ".join("-" * w for w in widths))


def _disp_len(s):
    return sum(2 if ord(c) > 127 else 1 for c in str(s))


def _pad(s, width):
    s = str(s)
    return s + " " * max(0, width - _disp_len(s))


def main():
    ap = argparse.ArgumentParser(description="中国居民分时电价查询")
    ap.add_argument("--list", action="store_true", help="列出所有省份")
    ap.add_argument("--province", help="省份名称或代码")
    ap.add_argument("--sort-by", choices=["spread", "peak_price", "valley_price", "region"],
                    default="region", help="排序字段")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    args = ap.parse_args()

    idx = load_index()
    provinces = list(idx["provinces"])

    if args.sort_by in ("spread", "peak_price", "valley_price"):
        provinces.sort(key=lambda p: (p.get(args.sort_by) is None, p.get(args.sort_by) or 0),
                       reverse=True)

    if args.province:
        data, meta = load_province(args.province)
        if not data:
            print("未找到省份：%s" % args.province, file=sys.stderr)
            print("可用：" + "、".join(p["region"] for p in idx["provinces"]), file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print("=" * 62)
            print("%s  ·  %s" % (data["region"], data.get("customer_type", "")))
            print("=" * 62)
            print("可信度    : %s" % data.get("confidence"))
            print("生效日期  : %s" % data.get("effective_date"))
            print("数据来源  : %s" % data.get("source", {}).get("name"))
            print("来源链接  : %s" % data.get("source", {}).get("url"))
            print("居民可选  : %s" % ("是（自愿申请）" if data.get("optional") else "否"))
            print()
            print("时段与电价")
            for p in data.get("periods", []):
                price = "待核实" if p.get("price") is None else "%.4f 元/kWh" % p["price"]
                print("  %-10s %s - %s   %s" % (p.get("label", p["name"]), p["start"], p["end"], price))
            if data.get("seasonal"):
                print()
                print("季节性时段")
                for s in data["seasonal"]:
                    print("  【%s】月份 %s" % (s["season"], ",".join(str(m) for m in s["months"])))
                    for p in s["periods"]:
                        price = "待核实" if p.get("price") is None else "%.4f" % p["price"]
                        print("      %-8s %s-%s  %s" % (p.get("label", p["name"]), p["start"], p["end"], price))
            if data.get("notes"):
                print()
                print("说明：%s" % data["notes"])
        return 0

    if args.json:
        print(json.dumps(provinces if args.list or True else provinces,
                         ensure_ascii=False, indent=2))
        return 0

    print("已收录 %d 个省市  （数据更新：%s）\n" % (idx["count"], idx["updated"]))
    print_table(fmt_rows(provinces))
    print("\n可信度说明：official=官方原文 / official-media=官方媒体 / unverified=未经核实")
    print("注：峰谷单价为 null 表示尚未从官方原文核实。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
