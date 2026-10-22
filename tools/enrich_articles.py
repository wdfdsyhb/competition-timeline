#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回源补漏：抓 52jingsai 文章页，给无时间的候选记录补阶段时间。

输入：data/candidates.json（fetch_52jingsai.py 产出）
输出：data/candidates_enriched.json（原结构 + 补出的 phases；抓取失败保留原样并记 enrich.error）

策略（按命中优先级）：
1. 「即日起至X」「X-Y」「X至Y」「X—Y」整行 → 报名阶段
2. 列表页已有的阶段名上下文行（阶段名：时间）在文章页同样命中
3. 标题括号前缀「【10月24报名截止，…】」→ 摘要已有时间，仅在无其他命中时用
4. 正文自由日期：取「报名/截止/提交/初赛/复赛/决赛/省赛/国赛」等关键词 ±80 字符内的日期，
   聚类成阶段；日期孤行（如落款 2026年5月10日）单独判断。

注意：文章页是 GB18030 编码；官方 URL 在「官网报名地址：」之后的 <a href>。
"""

import html as H
import json
import re
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "candidates.json"
DST = ROOT / "data" / "candidates_enriched.json"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept-Language": "zh-CN,zh;q=0.9"}

PHASE_COLON = re.compile(r"([^，,。；\n:：]{2,20})[:：]\s*(20\d{2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日(?:\s*[之前后])?)")
PHASE_TAIL = re.compile(r"([^，,。；\n:：]{2,20}?)(20\d{2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日(?:\s*[之前后])?)")
DATE_RE = re.compile(r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日")
PHASE_KW = ("报名", "截止", "提交", "初赛", "复赛", "决赛", "省赛", "国赛",
            "网络初赛", "总决赛", "作品征集", "赛程", "开考", "开赛")

TITLE_PREFIXES = [r"^【[^】]*】", r"^\[[^\]]*\]", r"^\([^)]*\)", r"^（[^）]*）"]


def norm_date(y, m, d):
    try:
        return date(int(y), int(m), int(d)).isoformat()
    except ValueError:
        return None


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    raw = urllib.request.urlopen(req, timeout=timeout).read()
    return raw.decode("gb18030", errors="replace")


def article_text(html_text):
    """剥掉 script/style 后转纯文本行，保留顺序。"""
    plain = re.sub(r"<script.*?</script>|<style.*?</style>", "", html_text, flags=re.S)
    plain = re.sub(r"<[^>]+>", "\n", plain)
    plain = H.unescape(plain)
    return [l.strip() for l in plain.split("\n") if l.strip()]


def official_url(lines):
    """官网报名地址：后的第一个 http 链接。"""
    for i, l in enumerate(lines):
        if "官网报名地址" in l or "报名网址" in l:
            for j in range(i, min(i + 6, len(lines))):
                m = re.search(r"https?://[^\s，。；)」』\"']+", lines[j])
                if m and "52jingsai.com" not in m.group(0):
                    return m.group(0)
    return None


def parse_dates_in(line):
    out = []
    for m in DATE_RE.finditer(line):
        d = norm_date(m.group(1), m.group(2), m.group(3))
        if d:
            out.append(d)
    return out


def parse_phase_colon(line):
    """阶段名：日期 行 → [(name, iso)]"""
    out = []
    for m in PHASE_COLON.finditer(line):
        name = re.sub(r"[\s　]+", "", m.group(1))
        name = re.sub(r"^([\d.、]+)", "", name)  # 剥序号
        if name and not any(n in name for n in ("摘要", "正文", "内容", "详情")):
            d = parse_dates_in(m.group(2))
            if d:
                out.append((name, d[0]))
    return out


def parse_range_line(line):
    """「即日起至X」「X至Y」「X—Y」→ (start|None, end)"""
    line = line.replace("—", "至").replace("–", "至").replace("-", "至")
    # 即日起至 2026年12月25日
    m = re.search(r"即日起\s*[至到]\s*(" + DATE_RE.pattern + r")", line)
    if m:
        d = parse_dates_in(m.group(1))
        if d:
            return (None, d[0])
    m = re.search(r"(" + DATE_RE.pattern + r")\s*[至到]\s*(" + DATE_RE.pattern + r")", line)
    if m:
        a = parse_dates_in(m.group(1))
        b = parse_dates_in(m.group(2))
        if a and b:
            return (a[0], b[0])
    return None


def extract_phases(lines):
    """文章页 → [(phase_name, start|None, end)]"""
    phases = []
    seen_names = set()

    def add(name, s, e):
        if name and name not in seen_names:
            phases.append({"name": name, "start": s, "end": e})
            seen_names.add(name)

    for line in lines:
        if len(line) > 200:
            continue
        # 噪声：页面底部推荐栏「XX活动||阶段：日期||主办...」
        if "||" in line:
            continue
        # 1) 阶段名：日期
        for name, d in parse_phase_colon(line):
            add(name, None, d)
        # 2) 范围行
        rng = parse_range_line(line)
        if rng:
            s, e = rng
            # 找阶段名：行内日期前的关键词
            kw = next((k for k in PHASE_KW if k in line), None)
            add(kw or "报名", s, e)
        # 3) 「X前」 Deadline
        for m in re.finditer(r"(" + DATE_RE.pattern + r")\s*前", line):
            d = parse_dates_in(m.group(1))
            if d:
                ctx = line[max(0, m.start() - 40):m.start()]
                kw = next((k for k in PHASE_KW if k in ctx), None)
                if kw:
                    add(kw, None, d[0])
    return phases


def enrich_one(rec):
    src = rec.get("source") or {}
    url = src.get("url", "") if isinstance(src, dict) else str(src)
    if "52jingsai.com" not in url:
        return rec, "skip-non-52"
    try:
        text = fetch(url)
    except Exception as e:
        return rec, f"fetch-fail: {e}"
    lines = article_text(text)
    phases = extract_phases(lines)
    ou = official_url(lines)
    rec = dict(rec)
    if phases:
        rec["phases"] = phases
        rec["confidence"] = "tentative"  # 文章页自动解析，未经人工核验
    if ou and not rec.get("official_url"):
        rec["official_url"] = ou
        rec["enrich"] = {"official_url_added": True}
    if ou and not phases:
        # 只补到官网链接、没解析出时间：confidence 保守回退
        rec["confidence"] = "tentative"
    if not phases and not ou:
        return rec, "no-findings"
    return rec, "ok"


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    recs = data["records"]
    todo = [r for r in recs if not r.get("phases")]
    print(f"total {len(recs)}, no-phase {len(todo)}", flush=True)
    ok = nofind = fail = 0
    for i, rec in enumerate(todo):
        new, status = enrich_one(rec)
        if status == "ok":
            ok += 1
        elif status.startswith("fetch-fail"):
            fail += 1
            rec["enrich"] = {"error": status}
        else:
            nofind += 1
        # 原位更新
        for j, r in enumerate(recs):
            if r.get("id") == rec["id"]:
                recs[j] = new
                break
        time.sleep(1.2)  # 礼貌限速
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(todo)} ok={ok} nofind={nofind} fail={fail}", flush=True)

    data["enriched_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    data["counts"]["phases_after_enrich"] = sum(1 for r in recs if r.get("phases"))
    DST.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"DONE ok={ok} nofind={nofind} fail={fail} -> {DST.name}", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
