#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并企业赛专源（data/cpipc.json 等）到 data/candidates.json，
再由 build_draft.py 生成站点。去重键：id 前缀（52jingsai 数字 id vs cpipc-*）。

冲突策略：
- 同名赛事去重：cpipc 的主题赛事名（如「数学建模竞赛」）与 52jingsai 已收录的
  「第二十三届中国研究生数学建模竞赛」是同一赛事的不同来源 → 标题归一化匹配，
  cpipc 版本覆盖（官方赛程表 > 聚合站转载），confidence 升 confirmed。
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "data" / "candidates.json"
EXTRA = [ROOT / "data" / "cpipc.json", ROOT / "data" / "candidates_baidustar.json", ROOT / "data" / "candidates_codecraft.json", ROOT / "data" / "candidates_tianchi.json"]


def norm_title(t):
    """标题归一化：去届次/年份/第X届/标点，留核心名。"""
    t = re.sub(r"[（(].*?[)）]", "", t)
    t = re.sub(r"20\d{2}[年度]?|第[一二三四五六七八九十\d]+届", "", t)
    t = re.sub(r"[，。！？、：；\s\W]", "", t)
    return t


def main():
    base = json.loads(BASE.read_text(encoding="utf-8"))
    records = base["records"]
    merged = 0
    added = 0

    for path in EXTRA:
        if not path.exists():
            continue
        ext = json.loads(path.read_text(encoding="utf-8"))
        # 归一化索引
        idx = {}
        for i, r in enumerate(records):
            nt = norm_title(r["title"])
            if nt:
                idx.setdefault(nt, i)
        for rec in ext.get("records", []):
            nt = norm_title(rec["title"])
            hit = idx.get(nt)
            if hit is not None:
                # 覆盖：官方赛程表优先，但保留原 id（避免外链失效）
                old = records[hit]
                old["phases"] = rec["phases"]
                old["confidence"] = "confirmed"
                if rec.get("official_url"):
                    old["official_url"] = rec["official_url"]
                old.setdefault("tags", []).append("官方赛程表")
                merged += 1
            elif any(r["id"] == rec["id"] for r in records):
                continue  # 幂等：重复跑 merge 不再追加
            else:
                records.append(rec)
                if nt:
                    idx[nt] = len(records) - 1
                added += 1

    # 重算 counts
    n_ph = sum(1 for r in records if r.get("phases"))
    base["counts"]["total"] = len(records)
    base["counts"]["with_phases"] = n_ph
    base["counts"]["corporate_merged"] = merged
    base["counts"]["corporate_added"] = added

    BASE.write_text(json.dumps(base, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print(f"merged={merged} added={added} total={len(records)} "
          f"with_phases={n_ph}")


if __name__ == "__main__":
    main()
