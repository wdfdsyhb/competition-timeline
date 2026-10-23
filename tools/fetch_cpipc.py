#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业竞赛专源 #1：中国研究生创新实践系列大赛管理平台（cpipc.acge.org.cn）
= 「华为杯」中国研究生数学建模竞赛 + 18 个其他主题赛事的母体平台。

抓取 https://cpipc.acge.org.cn/pw/notice/detail/2c9080179e403028019e484cf50210a6
（年度赛程一览，静态表格：主题赛事 | 报名时间 | 提交作品时间 | 决赛时间），
把每一行主题赛事变成一条 candidates.json 兼容记录。

设计要点：
- 赛程表里的时间是「6月27日-10月23日」格式、无年份 → 年份取通知标题（2026年度）。
- 输出与 fetch_52jingsai.py 同 schema（confidence/tags/source/phases），
  由 merge_corporate.py 合并进 candidates.json，build_draft.py 无需改动。
- confidence = confirmed（官方平台一手数据），但解析仍是自动的，
  年份判定有跨年风险（决赛 12 月、次年举办），保留 tentative 语义更诚实 → 用 tentative。
"""

import json
import re
import ssl
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "cpipc.json"

SCHEDULE_URL = ("https://cpipc.acge.org.cn/pw/notice/detail/"
                "2c9080179e403028019e484cf50210a6")
PLATFORM_URL = "https://cpipc.acge.org.cn/"
UA = {"User-Agent": "Mozilla/5.0 Chrome/126.0"}

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

MONTH_RE = r"(\d{1,2})月(\d{1,2})日"


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    raw = urllib.request.urlopen(req, timeout=30, context=CTX).read()
    return raw.decode("utf-8", errors="replace")


def parse_year(title):
    m = re.search(r"(20\d{2})年度", title)
    return int(m.group(1)) if m else None


def parse_range(text, year):
    """'6月27日-10月23日' / '12月26日-27日' / '11月14日-15日 9月25日-27日（舞蹈赛道）'
    -> (start_iso, end_iso)。
    只取第一个「X月A日[-B日]」片段（多段区间/括号注释忽略）；
    第二段省略月份按同月处理；开始月>结束月判跨年。"""
    text = re.sub(r"\s+", "", text).replace("&nbsp;", "")
    if not text:
        return None, None
    # 第一段片段（含可选的同月短式结束日；短式结束日后面不能再跟「月」）
    seg = re.match(r"(\d{1,2})月(\d{1,2})日(?:[-–—~](\d{1,2})日?(?!\d*月))?", text)
    if seg:
        mo, d1, d2 = int(seg.group(1)), int(seg.group(2)), seg.group(3)
        s = f"{year:04d}-{mo:02d}-{d1:02d}"
        if d2 is not None:
            e = f"{year:04d}-{mo:02d}-{int(d2):02d}"
            return s, e
        # 无短式结束日：找后续是否有完整「X月X日」（跨月/跨年区间）
        rest = text[seg.end():]
        m2 = re.search(MONTH_RE, rest)
        if m2:
            e_mo, e_d = int(m2.group(1)), int(m2.group(2))
            e_year = year + 1 if mo > e_mo else year
            return s, f"{e_year:04d}-{e_mo:02d}-{e_d:02d}"
        # 单日
        return s, s
    return None, None


def row_cells(tr_html):
    cells = []
    for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr_html, re.S):
        t = re.sub(r"<[^>]+>", "", c)
        t = t.replace("&nbsp;", " ").replace("&ldquo;", "“").replace("&rdquo;", "”")
        t = re.sub(r"\s+", " ", t).strip()
        cells.append(t)
    return cells


def main():
    html = fetch(SCHEDULE_URL)
    title_m = re.search(r"<title>(.*?)</title>", html, re.S)
    page_title = title_m.group(1).split(" - ")[0].strip() if title_m else ""
    year = parse_year(page_title)
    if not year:
        print("FAIL: cannot parse year from", page_title)
        sys.exit(1)

    body = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    out_records = []
    skipped = []

    for tr in rows:
        cells = row_cells(tr)
        if len(cells) < 4 or cells[0] in ("序号",):
            continue
        # 第 0 列是序号则去掉
        if re.fullmatch(r"\d{1,2}", cells[0]):
            cells = cells[1:]
        # 剩余列：名称 | 报名 | 提交 | 决赛（部分行是子赛道行，无序号，名称在 0 列）
        if len(cells) < 4:
            skipped.append(cells)
            continue
        name, enroll, submit, final = cells[0], cells[1], cells[2], cells[3]
        # 赛道子行（如 EDA 精英挑战赛）作为独立记录
        phases = []
        s, e = parse_range(enroll, year)
        if s:
            phases.append({"name": "报名", "raw": enroll, "start": s, "end": e,
                           "precision": "day"})
        s2, e2 = parse_range(submit, year)
        if s2:
            phases.append({"name": "作品提交", "raw": submit, "start": s2, "end": e2,
                           "precision": "day"})
        s3, e3 = parse_range(final, year)
        if s3:
            phases.append({"name": "决赛", "raw": final, "start": s3, "end": e3,
                           "precision": "day"})
        if not phases:
            skipped.append([name, enroll, submit, final])
            continue

        title = f"中国研究生{name}"  # 平台全称即「中国研究生创新实践系列大赛」，加前缀避免与本科生同名赛混淆
        slug = re.sub(r"[^\w\u4e00-\u9fff]+", "", name)
        out_records.append({
            "id": f"cpipc-{year}-{slug[:24]}",
            "title": title,
            "title_raw": name,
            "organizer": "中国研究生创新实践系列大赛组委会",
            "official_url": PLATFORM_URL,
            "phases": phases,
            "published": now,
            "confidence": "tentative",
            "tags": ["企业赛", "研究生", "官方赛程表"],
            "source": {
                "type": "official",
                "name": "中国研究生创新实践系列大赛管理平台",
                "url": SCHEDULE_URL,
            },
        })

    payload = {
        "generated_at": now,
        "source": SCHEDULE_URL,
        "page_title": page_title,
        "year": year,
        "counts": {"total": len(out_records), "skipped": skipped},
        "records": out_records,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"OK cpipc year={year} records={len(out_records)} "
          f"skipped={len(skipped)} -> {OUT.name}")
    for r in out_records:
        print("  ", r["id"], "|", " ; ".join(
            f"{p['name']} {p['start']}~{p['end']}" for p in r["phases"]))


if __name__ == "__main__":
    main()
