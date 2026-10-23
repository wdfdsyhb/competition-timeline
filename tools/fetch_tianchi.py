#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阿里云天池赛事抓取（官方列表 API，免登录）。

来源：https://tianchi.aliyun.com/competition/activeList
接口：GET /v3/proxy/competition/api/race/page
     ?visualTab={1|2}&raceName=&pageNum={n}&isActive=1
     由 g.alicdn.com 上 hmod-ace-2024-tianchi-competition-list 组件内 fetch 调用反查得到。

坑：
- visualTab 必须是数字（1=AI大模型赛，2=其它）；isActive 必须是数字 1，传 "true" 报
  TST-SYS-ILL_ARGS。
- 接口返回的 signupStartTime/signupEndTime/raceStartTime/raceEndTime 已是结构化时间，
  无需解析 HTML。
- 每页上限 10 条，需翻页；total 与实际页数不一定对齐，按 pages 字段翻。

产出：data/candidates_tianchi.json（与 candidates_*.json 同构，供 merge_corporate.py 消费）
"""

import json
import ssl
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "candidates_tianchi.json"

API = ("https://tianchi.aliyun.com/v3/proxy/competition/api/race/page"
       "?visualTab={vt}&raceName=&pageNum={page}&isActive=1")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126",
    "Referer": "https://tianchi.aliyun.com/competition/activeList",
    "Accept": "application/json",
}

# 常驻打榜赛/系列赛的结束时间都在一年后，会污染首屏 → 按结束年月截断
MAX_END = "2026-12"


def fetch_page(vt, page, ctx):
    url = API.format(vt=vt, page=page)
    req = urllib.request.Request(url, headers=HEADERS)
    body = urllib.request.urlopen(req, timeout=20, context=ctx).read()
    return json.loads(body)


def collect(ctx):
    seen, races = set(), []
    for vt in (1, 2):
        page = 1
        while page <= 5:
            j = fetch_page(vt, page, ctx)
            data = j.get("data") or {}
            lst = data.get("list") or []
            for r in lst:
                rid = r.get("raceId")
                if rid and rid not in seen:
                    seen.add(rid)
                    races.append(r)
            # pages 字段不可信（visualTab=1 报 pages=1 实际有 2 页）→ 翻到空页为止
            if not lst:
                break
            page += 1
            time.sleep(0.8)
    return races


def phase(name, start, end):
    return {
        "name": name,
        "start": start or None,
        "end": end or None,
        "precision": "day",
        "raw": "%s~%s" % (start or "", end or ""),
    }


def to_record(r):
    name = (r.get("name") or "").strip()
    if not name:
        return None
    sig = (r.get("signupStartTime") or "")[:10]
    eig = (r.get("signupEndTime") or "")[:10]
    sst = (r.get("raceStartTime") or "")[:10]
    eet = (r.get("raceEndTime") or "")[:10]

    phases = []
    if sig or eig:
        phases.append(phase("报名", sig, eig))
    if sst and eet and sst != sig:
        phases.append(phase("比赛周期", sst, eet))
    if not phases:
        return None

    # 常驻赛过滤：任一阶段结束超过 MAX_END 就整条丢掉
    latest = max((p["end"] or p["start"] or "") for p in phases)
    if latest and latest[:7] > MAX_END:
        return None

    tags = [t.get("tagNameCn") or t.get("tagName")
            for t in (r.get("tagsList") or [])][:4]
    return {
        "id": "tianchi-%s" % r["raceId"],
        "title": name,
        "organizer": "阿里云天池",
        "tags": [t for t in tags if t] + ["企业赛"],
        "phases": phases,
        "confidence": "confirmed",
        "source": {
            "type": "official_api",
            "name": "天池官方 API",
            "url": "https://tianchi.aliyun.com/competition/entrance/%s" % r["raceId"],
        },
    }


def main():
    ctx = ssl.create_default_context()
    races = collect(ctx)
    records = [x for x in (to_record(r) for r in races) if x]

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "source": "tianchi-api",
        "counts": {"total": len(records), "with_phases": len(records),
                   "raw_races": len(races)},
        "records": records,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("天池：原始 %d 条 → 保留 %d 条 → %s"
          % (len(races), len(records), OUT))
    for r in records:
        print("  %-14s %s" % (r["id"], r["title"][:34]))


if __name__ == "__main__":
    sys.exit(main())
