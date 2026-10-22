#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
榜单竞赛索引抓取器 — 我爱竞赛网（52jingsai.com）

用途：把「榜单竞赛」索引页的 182 条记录抓成候选数据，供人工核验后转正式 YAML。
数据源定位：仅作发现层（discovery）。站点声明「信息搜集整理自互联网，版权及活动
解释权归主办单位所有，我爱竞赛网仅作媒体支持」，因此抓下来的 source 一律标
aggregator，official_url 需后续核验补全。

注意：该站页面编码是 GB18030，不是 UTF-8。

用法：
    python fetch_52jingsai.py                # 抓全部页
    python fetch_52jingsai.py --max-pages 2  # 只抓前 2 页
    python fetch_52jingsai.py --rate 1.5     # 请求间隔 1.5s
"""

import argparse
import html as H
import json
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path

BASE = "https://www.52jingsai.com/bisai/xkjn/bangdan/"
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# 标题前缀噪声，需要剥离后才是真正的赛事名
TITLE_PREFIXES = [
    r"^【[^】]*】", r"^\[[^\]]*\]", r"^\([^)]*\)", r"^（[^）]*）",
]

# 阶段名里要剔除的噪声词
PHASE_NOISE = ("摘要", "正文", "内容", "详情")

OUT_DIR = Path(__file__).resolve().parent.parent / "data"


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------- 抓取

def fetch(url, retries=3, timeout=25):
    """拉一个页面并解码为 GB18030 文本。"""
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                raw = r.read(600_000)
            # 站点实际编码是 GB18030；先试严格 UTF-8，失败再退 GB18030
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                return raw.decode("gb18030", errors="replace")
        except (urllib.error.URLError, socket.timeout, OSError) as e:
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("抓取失败 %s: %s" % (url, last))


def strip_tags(s):
    return H.unescape(re.sub(r"<[^>]+>", " ", s))


def squeeze(s):
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- 解析

def parse_title(raw_title):
    """剥离【榜单赛事】一类前缀，返回 (clean_title, tags)。"""
    t = squeeze(strip_tags(raw_title))
    tags = []
    changed = True
    while changed:
        changed = False
        for pat in TITLE_PREFIXES:
            m = re.match(pat, t)
            if m:
                inner = m.group(0).strip("【】[]()（） ")
                tags.extend(x.strip() for x in re.split(r"[，,、/]", inner) if x.strip())
                t = t[m.end():].strip()
                changed = True
    return t, tags


DATE_CORE = re.compile(
    r"(20\d{2})\s*年\s*(\d{1,2})\s*月(?:\s*(\d{1,2})\s*日)?"
)


def normalize_date_fragment(frag):
    """
    把中文日期片段规范成 (iso_start, iso_end, precision)。
    precision: day | month | range | unknown
    非标准写法（即日起 / 中午12点 / 下午5点）在此处理。
    """
    frag = squeeze(frag)
    if not frag:
        return None, None, "unknown"

    matches = list(DATE_CORE.finditer(frag))
    if not matches:
        if "即日" in frag or "即日" in frag:
            return None, None, "open"
        return None, None, "unknown"

    if len(matches) == 1:
        m = matches[0]
        y, mo, d = int(m.group(1)), int(m.group(2)), m.group(3)
        try:
            if d:
                iso = date(y, mo, int(d)).isoformat()
                return iso, iso, "day"
            return "%04d-%02d" % (y, mo), "%04d-%02d" % (y, mo), "month"
        except ValueError:
            return "%04d-%02d" % (y, mo), "%04d-%02d" % (y, mo), "month"

    # 两个及以上：区间（如 2026年10月至2027年4月）
    a, b = matches[0], matches[-1]
    if a.group(3):
        start = "%04d-%02d-%02d" % (int(a.group(1)), int(a.group(2)), int(a.group(3)))
        p1 = "day"
    else:
        start = "%04d-%02d" % (int(a.group(1)), int(a.group(2)))
        p1 = "month"
    if b.group(3):
        end = "%04d-%02d-%02d" % (int(b.group(1)), int(b.group(2)), int(b.group(3)))
        p2 = "day"
    else:
        end = "%04d-%02d" % (int(b.group(1)), int(b.group(2)))
        p2 = "month"
    return start, end, "range" if p1 != "day" or p2 != "day" else "day"


# 日期尾巴：必须真的含日期，否则会匹配出一堆空壳
DATE_TAIL = r"((?:即日[^；;，,|]*)?(?:20\d{2}\s*年[^；;，,|]*))"

# 带冒号：报名截止时间：2026年11月20日
PHASE_COLON = re.compile(
    r"([\u4e00-\u9fa5A-Za-z0-9（）()·\-]{2,26}?)\s*[:：]\s*" + DATE_TAIL
)
# 不带冒号：精英赛报名截止2026年11月30日
PHASE_TAIL = re.compile(
    r"([\u4e00-\u9fa5A-Za-z0-9（）()·\-]{2,26}?(?:截止|开始|时间|日期))\s*" + DATE_TAIL
)

ORGANIZER = re.compile(
    r"(?:主办单位|承办单位|主办方|指导单位)\s*[:：]\s*([^\s；;|，,（）()]{2,40})"
)


def parse_summary(summary_html):
    """
    解析 <dd> 里的摘要，抽出阶段列表 + 主办单位。

    摘要形态：赛事名||阶段名：时间；阶段名：时间；主办单位：xxx
    分隔符同时存在 || 和 ；，且时间可能不带冒号紧跟在阶段名后。
    """
    # 先剥掉发布信息块（发布时间 / 浏览量），否则会污染日期解析
    text = re.sub(r'<div class="list_info".*?</div>', " ", summary_html, flags=re.S)
    text = squeeze(strip_tags(text))
    if not text:
        return [], None

    # 主办单位：先抽出来并从文本里移除，避免它挡住同段的阶段
    organizer = None
    mo = ORGANIZER.search(text)
    if mo:
        organizer = mo.group(1).strip("、，,。")
        text = text[:mo.start()] + " " + text[mo.end():]

    phases = []
    for seg in re.split(r"\|\||[；;]", text):
        seg = seg.strip(" ,，。")
        if len(seg) < 6:
            continue

        found = []
        for pat in (PHASE_COLON, PHASE_TAIL):
            for m in pat.finditer(seg):
                name = m.group(1).strip(" :：|、")
                raw_date = m.group(2).strip(" ,，。")
                if len(name) < 2 or len(raw_date) < 6:
                    continue
                if any(n in name for n in PHASE_NOISE):
                    continue
                # 阶段名不该长到是一整句话
                if len(name) > 24:
                    continue
                found.append((m.start(), name, raw_date))

        if found:
            found.sort()
            _, name, raw_date = found[0]
            start, end, prec = normalize_date_fragment(raw_date)
            phases.append({
                "name": name,
                "raw": raw_date,
                "start": start,
                "end": end,
                "precision": prec,
            })

    # 同名阶段保留第一次
    seen, uniq = set(), []
    for p in phases:
        if p["name"] in seen:
            continue
        seen.add(p["name"])
        uniq.append(p)

    return uniq, organizer


RECORD_SPLIT = re.compile(r'(?=<dl class="bbda)')


def parse_page(page_html):
    """从一页 HTML 抽出所有记录。"""
    out = []
    for block in RECORD_SPLIT.split(page_html)[1:]:
        m = re.search(
            r'<dt[^>]*class="[^"]*xs2_tit[^"]*"[^>]*>\s*'
            r'<a[^>]+href="article-(\d+)-1\.html"[^>]*>(.*?)</a>',
            block, re.S,
        )
        if not m:
            continue
        aid, raw_title = m.group(1), m.group(2)

        dd = re.search(r'<dd[^>]*class="[^"]*xs2[^"]*"[^>]*>(.*?)</dd>', block, re.S)
        summary = dd.group(1) if dd else ""

        pub = None
        mp = re.search(r"(20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2})", block)
        if mp:
            pub = mp.group(1)

        title, tags = parse_title(raw_title)
        phases, organizer = parse_summary(summary)

        out.append({
            "id": aid,
            "title_raw": squeeze(strip_tags(raw_title)),
            "title": title,
            "tags": tags,
            "phases": phases,
            "organizer": organizer,
            "published": pub,
            "source": {
                "type": "aggregator",
                "name": "我爱竞赛网",
                "url": "https://www.52jingsai.com/article-%s-1.html" % aid,
            },
            "confidence": "tentative",
            "official_url": None,
        })
    return out


# ---------------------------------------------------------------- 主流程

CERT_HINTS = ("证书", "统考", "水平测试", "答题领", "词汇竞赛", "考试报名",
              "报名费", "培训通知", "讲评")
COMP_HINTS = ("大赛", "竞赛", "杯", "挑战赛", "创新", "设计", "建模",
              "技能", "作品", "赛区", "选拔")


def classify(rec):
    """
    粗分类：证书考试类 vs 学科赛事类。
    证书考试类的时间通常只写在标题里（如【10月24日全国统考】），正文没有阶段赛程，
    不该进赛事时间库。
    """
    title = rec["title"]
    is_cert = any(k in title for k in CERT_HINTS)
    is_comp = any(k in title for k in COMP_HINTS)
    if is_cert and not is_comp:
        return "cert_exam"
    if not is_comp and not rec["phases"]:
        return "other"
    return "competition"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=30)
    ap.add_argument("--rate", type=float, default=1.0, help="请求间隔秒")
    ap.add_argument("--out", default="candidates.json")
    args = ap.parse_args()

    seen = {}
    page = 1
    while page <= args.max_pages:
        url = BASE if page == 1 else "%s?page=%d" % (BASE, page)
        try:
            html = fetch(url)
        except RuntimeError as e:
            log("  page %2d 抓取失败: %s" % (page, e))
            break

        recs = parse_page(html)
        fresh = [r for r in recs if r["id"] not in seen]
        for r in fresh:
            seen[r["id"]] = r
        log("  page %2d: 解析 %2d 条, 新增 %2d, 累计 %3d"
            % (page, len(recs), len(fresh), len(seen)))

        if not fresh:
            break
        page += 1
        time.sleep(args.rate)

    recs = list(seen.values())
    comps = [r for r in recs if classify(r) == "competition"]
    with_time = [r for r in comps if r["phases"]]
    dated = [r for r in comps if any(p["start"] for p in r["phases"])]

    log("")
    log("=== 抓取完成 ===")
    log("总记录            %3d" % len(recs))
    log("学科赛事类        %3d" % len(comps))
    log("  含阶段时间      %3d  (%.0f%%)"
        % (len(with_time), 100.0 * len(with_time) / max(1, len(comps))))
    log("  含可解析日期    %3d  (%.0f%%)"
        % (len(dated), 100.0 * len(dated) / max(1, len(comps))))
    log("证书考试类        %3d" % (len(recs) - len(comps)))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / args.out
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": BASE,
        "counts": {
            "total": len(recs),
            "competition": len(comps),
            "with_phases": len(with_time),
            "with_dates": len(dated),
        },
        "records": recs,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    log("")
    log("写入 %s" % out_path)


if __name__ == "__main__":
    SystemExit(main())
