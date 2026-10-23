#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
华为软件精英挑战赛（CodeCraft）2026 专源抓取器。
官网 https://developer.huaweicloud.com/codecraft2026 是 Vite SPA，
赛程静态内嵌在 res-hd.hc-cdn.cn 的 HDCompetitionPortal chunk 里
（index.87f1fb4b.js → mu=[{id:"preliminary",date:[...]},...]）。
无需浏览器，不需要后端 API（详情 API 302 到登录）。

用法：python fetch_codecraft.py  → data/candidates_codecraft.json
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "candidates_codecraft.json"

CHUNK = ("https://res-hd.hc-cdn.cn/HDCompetitionPortal/1.0.42/"
         "assets/index.87f1fb4b.js")
PHASE_NAMES = {
    "preliminary": "初赛",
    "rematch": "复赛",
    "final": "决赛",
}
TITLE = "2026华为软件精英挑战赛"
ORG = "华为技术有限公司"
OFFICIAL = "https://developer.huaweicloud.com/codecraft2026"


def fetch(url: str) -> str:
    r = subprocess.run(
        ["curl", "-sL", "--max-time", "30", "-A", "Mozilla/5.0", url],
        capture_output=True)
    return r.stdout.decode("utf-8", "ignore")


def extract(text: str) -> dict:
    # 生产分支（VITE_APP_ENVIROMENT==="huaweicloud"）报名窗口：
    # eu=start, au=end（正则里各取 huaweicloud 侧的第一个日期）
    signup = re.search(
        r'VITE_APP_ENVIROMENT==="huaweicloud"\?new Date\("([^"]+)"\)'
        r'.*?huaweicloud"\?new Date\("([^"]+)"\)', text)
    if not signup:
        raise SystemExit("signup window not found")
    mu = re.search(r"mu=\[(.*?)\];", text).group(1)
    phases = []
    for m in re.finditer(
            r'id:"(\w+)",date:\[new Date\("([^"]+)"\).getTime\(\),'
            r'new Date\("([^"]+)"\).getTime\(\)\]', mu):
        pid, start, end = m.groups()
        phases.append({
            "name": PHASE_NAMES.get(pid, pid),
            "start": start,
            "end": end,
            "precision": "day",
        })
    if not phases:
        raise SystemExit("phase table not found")
    return {
        "signup": [signup.group(1), signup.group(2)],
        "phases": phases,
    }


def main():
    text = fetch(CHUNK)
    data = extract(text)

    # 报名作为第一个 phase
    all_phases = [{
        "name": "报名时间",
        "start": data["signup"][0],
        "end": data["signup"][1],
        "precision": "day",
    }] + data["phases"]

    rec = {
        "id": "codecraft-2026",
        "title": TITLE,
        "organizer": ORG,
        "tags": ["企业赛", "程序设计"],
        "source": {"type": "official", "name": "华为开发者大赛官网", "url": OFFICIAL},
        "official_url": OFFICIAL,
        "confidence": "confirmed",
        "published": None,
        "phases": all_phases,
        "method": "vite-chunk-static",
    }
    OUT.write_text(json.dumps(
        {"generated_at": datetime.now().isoformat(), "source": "codecraft",
         "counts": {"total": 1}, "records": [rec]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"written {OUT}: 1 record, {len(all_phases)} phases")
    for p in all_phases:
        print(" ", p["name"], p["start"], "→", p["end"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
