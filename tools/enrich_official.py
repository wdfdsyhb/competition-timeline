#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P2 官网直连补时：抓 candidates.json 里 official_url 的竞赛官网，找最新年度的报名/截止时间。

策略：
- 抓官网首页（或 /news、/notice 列表链接深度 1），转纯文本
- 沿用 enrich_articles 的时间行解析（阶段名：日期 / 范围 / 截止）
- 命中即写入 phases（confidence=estimated，官网自动解析），source 官网 URL
- 输出 data/candidates_official.json
"""

import html as H
import json
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "candidates.json"
DST = ROOT / "data" / "candidates_official.json"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

DATE_RE = re.compile(r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日")
PHASE_COLON = re.compile(r"([^，,。；\n:：]{2,20})[:：]\s*(20\d{2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日(?:\s*[之前后])?)")
PHASE_KW = ("报名", "截止", "提交", "初赛", "复赛", "决赛", "省赛", "国赛",
            "总决赛", "作品征集", "赛程", "开考", "开赛", "注册")


def norm_date(y, m, d):
    try:
        y, m, d = int(y), int(m), int(d)
        if not (1 <= m <= 12 and 1 <= d <= 31):
            return None
        import datetime
        return datetime.date(y, m, d).isoformat()
    except ValueError:
        return None


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    raw = urllib.request.urlopen(req, timeout=timeout, context=CTX).read()
    head = raw[:2000].decode("latin1", errors="replace").lower()
    for enc in ("utf-8", "gb18030", "gbk"):
        if f"charset={enc}" in head:
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                pass
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("gb18030", errors="replace")


def to_lines(html_text):
    plain = re.sub(r"<script.*?</script>|<style.*?</style>", "", html_text, flags=re.S)
    plain = re.sub(r"<[^>]+>", "\n", plain)
    plain = H.unescape(plain)
    return [l.strip() for l in plain.split("\n") if l.strip()]


def extract_phases(lines):
    phases, seen = [], set()

    def add(name, s, e):
        if name and name not in seen:
            phases.append({"name": name, "start": s, "end": e})
            seen.add(name)

    for line in lines:
        if len(line) > 200 or "||" in line:
            continue
        for m in PHASE_COLON.finditer(line):
            name = re.sub(r"[\s　]+", "", m.group(1))
            name = re.sub(r"^([\d.、（(]+)", "", name)
            d = norm_date(*re.search(DATE_RE, m.group(2)).groups()) if re.search(DATE_RE, m.group(2)) else None
            if name and d and not any(n in name for n in ("摘要", "正文", "详情")):
                add(name[:24], None, d)
        rng = re.search(r"即日起\s*[至到]\s*(" + DATE_RE.pattern + r")", line)
        if rng:
            d = norm_date(*re.search(DATE_RE, rng.group(1)).groups())
            kw = next((k for k in PHASE_KW if k in line), "报名")
            if d:
                add(kw, None, d)
        rng = re.search(r"(" + DATE_RE.pattern + r")\s*[至到—–]\s*(" + DATE_RE.pattern + r")", line)
        if rng:
            a = norm_date(*re.search(DATE_RE, rng.group(1)).groups())
            b = norm_date(*re.search(DATE_RE, rng.group(2)).groups())
            kw = next((k for k in PHASE_KW if k in line), "报名")
            if a and b:
                add(kw, a, b)
    return phases


def latest_year(lines):
    """页面里最新出现的 20XX 年，用来确认是本届信息。"""
    text = "\n".join(lines)
    ys = [int(m.group(0)[:4]) for m in re.finditer(r"20\d{2}\s*年", text)]
    return max(ys) if ys else 0


def probe_site(url):
    """首页 + 深度 1 的通知/新闻链接，返回聚合文本行。"""
    lines = []
    try:
        t = fetch(url)
        lines = to_lines(t)
        # 找通知/新闻/公告列表链接
        sub_urls = []
        for m in re.finditer(r'<a[^>]+href="([^"#]+)"[^>]*>([^<]{2,20}(?:通知|公告|新闻|动态|资讯|报名)[^<]{0,10})</a>', t):
            u = m.group(1)
            if u.startswith("//"):
                u = "https:" + u
            elif u.startswith("/"):
                base = "/".join(url.split("/")[:3])
                u = base + u
            elif not u.startswith("http"):
                continue
            if u not in sub_urls and u.split("/")[2] == url.split("/")[2]:
                sub_urls.append(u)
        for u in sub_urls[:3]:
            try:
                lines += to_lines(fetch(u))
                time.sleep(0.8)
            except Exception:
                pass
    except Exception as e:
        return lines, f"fetch-fail: {e}"
    return lines, "ok"


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    recs = data["records"]
    todo = [r for r in recs if r.get("official_url") and not r.get("phases")]
    print(f"total {len(recs)}, official-url-no-phase {len(todo)}", flush=True)
    ok = nofind = fail = 0
    for i, rec in enumerate(todo):
        ou = rec["official_url"]
        lines, status = probe_site(ou)
        phases = extract_phases(lines)
        yr = latest_year(lines)
        rec = dict(rec)
        if phases:
            rec["phases"] = phases
            rec["confidence"] = "estimated"  # 官网自动解析
            rec["official_checked_at"] = time.strftime("%Y-%m-%d")
            ok += 1
        elif status.startswith("fetch-fail"):
            fail += 1
            rec["official_probe"] = {"error": status}
        else:
            nofind += 1
            rec["official_probe"] = {"checked": time.strftime("%Y-%m-%d"), "year_seen": yr}
        for j, r in enumerate(recs):
            if r.get("id") == rec["id"]:
                recs[j] = rec
                break
        time.sleep(1.0)
        if (i + 1) % 5 == 0:
            print(f"  {i+1}/{len(todo)} ok={ok} nofind={nofind} fail={fail}", flush=True)

    data["official_enriched_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    data["counts"]["phases_after_official"] = sum(1 for r in recs if r.get("phases"))
    DST.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"DONE ok={ok} nofind={nofind} fail={fail} -> {DST.name}", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
