#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""百度之星（star.baidu.com）纯壳 SPA 抓取器。

思路：不跑浏览器。百度之星是 Vue Router webpack 分包站：
  1. 壳 HTML 引出 manifest.js
  2. manifest 里有 chunk id -> hash 映射
  3. 主包 6.js 里有路由表，/program-design-match2026 懒加载 chunk 14
  4. chunk 14 的渲染模板 _v("...") 里静态内嵌全部赛程文本
提取 _v 字符串拼出可读文本，正则抽日期与阶段。
"""
import re, json, ssl, html, urllib.request, datetime, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

BASE = "https://star.baidu.com"
ROUTE = "/program-design-match2026"


def get(url):
    # chunk URL 需要 js 后缀；baidu 的 CDN 对某些 UA/路径 302 到 500 页
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": BASE + "/",
    })
    return urllib.request.urlopen(req, timeout=20, context=CTX).read().decode("utf-8", errors="replace")


def find_route_chunk(shell_html: str) -> str | None:
    """从路由表 JS 里解析 /program-design-match2026 对应的页面 chunk id（最后一个 n.e(N)）。

    壳里加载 3 个 JS：manifest / 8 / 6。路由表在 app 主包（6.js）里，
    扫全部非 manifest 的 script 直到找到 ROUTE。
    """
    chunks = re.findall(r'<script[^>]*src=([^ >]+\.js)[^>]*>', shell_html)
    for c in chunks:
        c = c.strip('"\'')
        if "manifest" in c:
            continue
        url = BASE + c if c.startswith("/") else c
        body = get(url)
        if ROUTE not in body:
            continue
        seg = body[body.find(ROUTE):body.find(ROUTE) + 600]
        m2 = re.search(r'Promise\.all\(\[([^\]]+)\]', seg)
        if not m2:
            continue
        ids = re.findall(r'n\.e\((\d+)\)', m2.group(1))
        if ids:
            return ids[-1]  # 最后一个 e() 是页面 chunk
    return None


def find_chunk_hash(manifest_js: str, chunk_id: str) -> str | None:
    """manifest 里有两张 hash 表（css 在前 js 在后）。取该 id 的**最后一个** hash，
    即 webpack 运行时实际拼接 JS URL 用的那张。"""
    hashes = re.findall(chunk_id + r'\s*:\s*"([0-9a-f]{16,24})"', manifest_js)
    return hashes[-1] if hashes else None


def extract_text(chunk_js: str) -> str:
    """拼出 _v() 渲染串文本。注意：_v 串内的 \\n 是字面反斜杠+双写，先归一为空格。"""
    texts = re.findall(r'_v\("((?:[^"\\]|\\.)*)"\)', chunk_js)
    txt = html.unescape(" ".join(t for t in texts if re.search(r"[\u4e00-\u9fff]", t)))
    # 日期被「2026年8月 23\n日」式换行拆断：去掉 \n 字面量与多余空格前，先修日期
    txt = txt.replace("\\n", " ")
    txt = re.sub(r"(20\d{2}年\d{1,2}月)\s+(\d{1,2})\s*日", r"\1\2日", txt)
    return re.sub(r"\s+", " ", txt)


DATE_RE = re.compile(r"20\d{2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日")


def parse_phases(txt: str) -> list[dict]:
    phases = []
    for m in re.finditer(r"[^。;]{0,120}(?:初赛|决赛|报名)[^。;]{0,160}", txt):
        s = m.group(0)
        dates = DATE_RE.findall(s)
        times = re.findall(r"\d{1,2}:\d{2}-\d{1,2}:\d{2}", s)
        if not dates:
            continue
        for d in dates:  # 「第一场…第二场…」可能同段出现两个日期
            name = "初赛（线上）" if ("初赛" in s and "线上" in s) else ("初赛" if "初赛" in s else ("决赛" if "决赛" in s else "报名"))
            phases.append({
                "name": name,
                "date": d.replace(" ", ""),
                "time": times[0] if times else None,
                "context": s.strip()[:140],
            })
    # 去重
    seen, out = set(), []
    for p in phases:
        k = (p["name"], p["date"], p["time"])
        if k not in seen:
            seen.add(k)
            out.append(p)
    return out


def to_iso(d: str) -> str:
    m = re.match(r"(20\d{2})年(\d{1,2})月(\d{1,2})日", d)
    return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"


def main():
    shell = get(BASE + "/")
    manifest_url = re.search(r'src=(/astar_index/js/manifest\.[0-9a-f]+\.js)', shell)
    if not manifest_url:
        print("FATAL: no manifest found"); return 1
    manifest = get(BASE + manifest_url.group(1))
    chunk_id = find_route_chunk(shell)
    if not chunk_id:
        print("FATAL: route chunk not found"); return 1
    chunk_hash = find_chunk_hash(manifest, chunk_id)
    chunk_url = f"{BASE}/astar_index/js/{chunk_id}.{chunk_hash}.js"
    chunk = get(chunk_url)
    txt = extract_text(chunk)
    phases = parse_phases(txt)
    print(f"chunk: {chunk_url}  ({len(chunk)} B)")
    for p in phases:
        print(f"  {p['name']}  {p['date']}  {p['time'] or ''}")

    # 组装成项目 record 格式（与 candidates.json 同构）
    now = datetime.date.today().isoformat()
    rec = {
        "id": f"baidustar-2026-{datetime.date.today().year}",
        "title": "百度之星程序设计大赛",
        "organizer": "百度公司",
        "category": "计算机",
        "tags": ["算法", "企业赛"],
        "confidence": "confirmed",
        "phases": [
            {
                "name": p["name"],
                "start": to_iso(p["date"]) if "报名" not in p["name"] else None,
                "end": to_iso(p["date"]),
                "precision": "day",
                "raw": p["context"],
                "source": {"type": "official", "name": "百度之星官网",
                           "url": BASE + ROUTE},
            }
            for p in phases
        ],
        "source": {"type": "official", "name": "百度之星官网", "url": BASE + ROUTE},
    }
    out = ROOT / "data" / "candidates_baidustar.json"
    payload = {
        "generated_at": now + "T00:00:00+08:00",
        "source": {"name": "star.baidu.com", "method": "webpack-chunk-static"},
        "records": [rec],
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written: {out.relative_to(ROOT)}  phases={len(rec['phases'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
