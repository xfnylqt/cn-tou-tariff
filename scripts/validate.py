#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校验 data/*.json 的数据完整性（纯标准库，零依赖）。

用法：
    python scripts/validate.py          # 校验全部
    python scripts/validate.py --strict # 含未核实数据的严格模式（发现即失败）
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

REQUIRED_TOP = ["region", "province_code", "effective_date", "accessed_date",
                "source", "confidence", "periods"]
VALID_CONFIDENCE = {"official", "official-media", "unverified"}
VALID_PERIOD_NAMES = {"sharp", "peak", "flat", "valley", "deep_valley"}
def time_ok(s, allow_end_of_day=False):
    """校验 HH:MM。结束时间允许 24:00 表示当日终点。"""
    if not isinstance(s, str) or len(s) != 5 or s[2] != ":":
        return False
    if s == "24:00":
        return allow_end_of_day
    if not (s[:2].isdigit() and s[3:].isdigit()):
        return False
    h, m = int(s[:2]), int(s[3:])
    return 0 <= h < 24 and 0 <= m < 60


def validate_periods(periods, where, errors, warnings):
    if not isinstance(periods, list) or not periods:
        errors.append("%s: periods 必须是非空数组" % where)
        return
    has_valley = False
    for i, p in enumerate(periods):
        tag = "%s.periods[%d]" % (where, i)
        if not isinstance(p, dict):
            errors.append("%s: 不是对象" % tag)
            continue
        for k in ("name", "start", "end"):
            if k not in p:
                errors.append("%s: 缺少字段 %s" % (tag, k))
        if p.get("name") not in VALID_PERIOD_NAMES:
            errors.append("%s.name 取值非法：%r" % (tag, p.get("name")))
        if p.get("name") == "valley":
            has_valley = True
        for k in ("start", "end"):
            if k in p and not time_ok(p[k], allow_end_of_day=(k == "end")):
                errors.append("%s.%s 时间格式非法：%r" % (tag, k, p.get(k)))
        if p.get("price") is None:
            warnings.append("%s.price 为空（数值待核实）" % tag)
        elif not isinstance(p.get("price"), (int, float)):
            errors.append("%s.price 不是数值：%r" % (tag, p.get("price")))
    if not has_valley:
        warnings.append("%s: 未找到 valley（谷段）定义" % where)


def validate_file(path, strict=False):
    errors, warnings = [], []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return ["JSON 解析失败：%s" % e], []

    for k in REQUIRED_TOP:
        if k not in data:
            errors.append("缺少必填字段：%s" % k)

    conf = data.get("confidence")
    if conf not in VALID_CONFIDENCE:
        errors.append("confidence 取值非法：%r" % conf)
    if strict and conf == "unverified":
        errors.append("strict 模式：存在未核实数据（confidence=unverified）")

    src = data.get("source")
    if not isinstance(src, dict):
        errors.append("source 必须是对象")
    else:
        if not src.get("url"):
            errors.append("source.url 不能为空")
        if not src.get("name"):
            errors.append("source.name 不能为空")
        if conf == "unverified" and src.get("url", "").startswith("http"):
            warnings.append("标记为 unverified，请确认无法找到官方来源")

    if data.get("residential_tou_available", True):
        validate_periods(data.get("periods"), "periods", errors, warnings)
    else:
        if not data.get("no_tou_reason"):
            errors.append("residential_tou_available=false 时必须提供 no_tou_reason 说明原因")
        if data.get("periods"):
            warnings.append("标记为无居民峰谷，但 periods 非空，请确认")

    for si, s in enumerate(data.get("seasonal") or []):
        validate_periods(s.get("periods"), "seasonal[%d]" % si, errors, warnings)

    if not data.get("tiers"):
        warnings.append("tiers 为空（阶梯电价数据待补充）")

    return errors, warnings


def check_index(index_path, data_files):
    errors, warnings = [], []
    if not index_path.exists():
        return ["缺少 data/index.json"], []
    idx = json.loads(index_path.read_text(encoding="utf-8"))
    listed = {p["file"] for p in idx.get("provinces", [])}
    actual = {f.name for f in data_files if f.name != "index.json"}
    for miss in sorted(actual - listed):
        errors.append("index.json 未收录：%s" % miss)
    for extra in sorted(listed - actual):
        errors.append("index.json 收录了不存在的文件：%s" % extra)
    if idx.get("count") != len(idx.get("provinces", [])):
        warnings.append("index.json 的 count 与实际条目数不一致")
    return errors, warnings


def main():
    strict = "--strict" in sys.argv
    files = sorted(f for f in DATA.glob("*.json") if f.name != "index.json")
    if not files:
        print("未找到任何数据文件")
        return 1

    total_err = total_warn = 0
    for f in files:
        errs, warns = validate_file(f, strict)
        total_err += len(errs)
        total_warn += len(warns)
        if errs:
            print("[FAIL] %s" % f.name)
            for e in errs:
                print("       错误  %s" % e)
            for w in warns:
                print("       提醒  %s" % w)
        elif warns:
            print("[WARN] %s" % f.name)
            for w in warns:
                print("       %s" % w)
        else:
            print("[ OK ] %s" % f.name)

    idx_errs, idx_warns = check_index(DATA / "index.json", files)
    total_err += len(idx_errs)
    if idx_errs:
        print("[FAIL] index.json")
        for e in idx_errs:
            print("       错误  %s" % e)
    else:
        print("[ OK ] index.json")

    print("\n合计：%d 个数据文件，%d 项错误，%d 项提醒" % (len(files), total_err, total_warn))
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())
