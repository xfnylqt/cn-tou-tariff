#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重新生成 data/index.json（遍历全部省份文件汇总）。"""

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def span(periods, kind):
    """把某类型的时段合并成 'HH:MM-HH:MM' 描述。"""
    segs = [(p["start"], p["end"]) for p in periods if p.get("name") == kind]
    if not segs:
        return None
    return ", ".join("%s-%s" % (s, e) for s, e in segs)


def first_price(periods, kind):
    for p in periods:
        if p.get("name") == kind and p.get("price") is not None:
            return p["price"]
    return None


rows = []
for f in sorted(DATA.glob("*.json")):
    if f.name == "index.json":
        continue
    d = json.loads(f.read_text(encoding="utf-8"))
    periods = d.get("periods") or []
    has = d.get("residential_tou_available", True)
    # 安徽等省只有「平段 / 谷段」两段，以平段作为高价段参考
    peak_p = (first_price(periods, "peak") or first_price(periods, "sharp")
              or first_price(periods, "flat"))
    val_p = first_price(periods, "valley")
    spread = round(peak_p - val_p, 4) if (peak_p and val_p) else None

    row = {
        "code": d.get("province_code"),
        "file": f.name,
        "region": d.get("region"),
        "has_residential_tou": has,
        "customer_type": d.get("customer_type"),
        "peak": span(periods, "peak") or span(periods, "sharp"),
        "valley": span(periods, "valley"),
        "peak_price": peak_p,
        "valley_price": val_p,
        "spread": spread,
        "optional": d.get("optional"),
        "confidence": d.get("confidence"),
    }
    if not has:
        row["peak"] = None
        row["valley"] = None
        row["reason"] = (d.get("no_tou_reason") or "")[:60]
    else:
        row["note"] = (d.get("notes") or "")[:70]
    rows.append(row)

rows.sort(key=lambda r: (not r["has_residential_tou"], -(r["spread"] or -1), r["code"] or ""))

index = {
    "updated": "2026-10-09",
    "count": len(rows),
    "with_residential_tou": sum(1 for r in rows if r["has_residential_tou"]),
    "without_residential_tou": sum(1 for r in rows if not r["has_residential_tou"]),
    "description": "中国居民分时（峰谷）电价索引。完整字段见各省份文件。",
    "confidence_levels": {
        "official": "政府 / 发改委 / 电网公司官网原文",
        "official-media": "官方媒体转载官方文件",
        "unverified": "自媒体汇总，未经官方核实，不应作为测算依据",
    },
    "note": "has_residential_tou=false 表示该省居民生活用电不执行峰谷分时电价，"
            "原因见各省文件 no_tou_reason 字段。",
    "provinces": rows,
}

(DATA / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("索引已生成：共 %d 个，其中有居民峰谷 %d 个，无 %d 个"
      % (index["count"], index["with_residential_tou"], index["without_residential_tou"]))
