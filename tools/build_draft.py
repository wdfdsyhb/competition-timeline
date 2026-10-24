#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视觉稿生成器 — 从 data/candidates.json 生成单文件静态站

产出 site/index.html，双击即可打开。数据内嵌，无需服务器。
正式版会是 Astro + Tailwind + motion；这里是视觉稿，用来定调色 / 布局 / 动效。
"""

import json
import re
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SRC = ROOT / "data" / "candidates.json"
OUT = ROOT / "index.html"
ICS_OUT = ROOT / "competitions.ics"

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "candidates.json"
OUT = ROOT / "index.html"

# 分类映射：命中即归类，顺序即优先级
CATS = [
    ("计算机", ("计算机", "软件", "程序设计", "人工智能", "AIGC", "ICT", "算法",
                "数字媒体", "信息", "网络安全", "智能")),
    ("设计艺术", ("设计", "艺术", "美术", "视觉", "米兰", "华灿", "创意设计",
                  "工业设计", "广告")),
    ("语言文学", ("语言", "文学", "汉语", "外语", "英语", "诵读", "写作", "普通话",
                  "规范字", "翻译", "词汇")),
    ("创新创业", ("创新创业", "创业", "创新大赛", "iCAN", "学创杯", "挑战杯",
                  "互联网+", "创客")),
    ("工程机械", ("机械", "工程", "机器人", "电子", "电气", "自动化", "汽车",
                  "航空", "航天", "土木", "建筑", "化工", "材料", "能源")),
    ("数理统计", ("数学", "建模", "统计", "数据", "物理", "化学", "分析")),
    ("商科经管", ("商科", "市场", "经济", "会计", "金融", "管理", "营销",
                  "跨境电商", "调查")),
    ("医学健康", ("医学", "医药", "护理", "健康", "生物", "生命")),
    ("职业技能", ("技能", "职业", "工匠", "金相", "测绘", "烹饪")),
    ("人文社科", ("人文", "社科", "教育", "法学", "思政", "文化旅游", "会展")),
]

# 非赛事：榜单 / 指数 / 报告发布类
REPORT_HINTS = ("指数", "分析报告", "画像", "分档榜", "公布", "发布")


def categorize(title):
    for name, keys in CATS:
        if any(k in title for k in keys):
            return name
    return "其他"


def is_report(title):
    return any(k in title for k in REPORT_HINTS)


def clean(title):
    """标题收尾：去掉「报名通知！」这类尾巴和多余标点。"""
    t = re.sub(r"[！!？?。；;，,、]+$", "", title).strip()
    t = re.sub(r"(报名通知|通知|报名开启|开启报名|火热报名中|报名中)$", "", t).strip()
    t = re.sub(r"\s*[（(]\s*第[一二三四五六七八九十\d]+批\s*[)）]\s*$", "", t).strip()
    return t or title


def month_label(iso):
    if not iso:
        return None
    p = iso.split("-")
    if len(p) < 2:
        return None
    return "%d 月" % int(p[1])


def build_records(raw):
    out = []
    for r in raw:
        if is_report(r["title"]) or not r["phases"]:
            continue
        # 取最早的可解析日期作为主时间（start 或 end 任一有值即可）
        dated = [p for p in r["phases"] if p.get("start") or p.get("end")]
        if not dated:
            continue
        dated.sort(key=lambda p: p.get("start") or p.get("end"))
        lead = dated[0]
        # 报名截止：优先找报名/截止类节点的最晚 end。
        # 「可报名」是问报名还开不开，不是问最早那个节点过没过 ——
        # 报名 3 月开始、10 月底截止的赛事，用 lead 判会误报「已截止」。
        reg_ends = [
            p.get("end") or p.get("start")
            for p in r["phases"]
            if ("报名" in p["name"] or "截止" in p["name"]) and (p.get("end") or p.get("start"))
        ]
        reg_end = max(reg_ends) if reg_ends else None
        phases = []
        for p in r["phases"]:
            phases.append({
                "name": p["name"],
                "start": p.get("start"),
                "end": p.get("end"),
                "precision": p.get("precision", "day"),
                "raw": p.get("raw", ""),
            })
        out.append({
            "id": r["id"],
            "title": clean(r["title"]),
            "raw_title": r.get("title_raw") or r["title"],
            "org": r.get("organizer") or "",
            "tags": r.get("tags") or [],
            "cat": categorize(r["title"]),
            "lead": lead.get("start") or lead.get("end"),
            "lead_end": lead.get("end"),
            "reg_end": reg_end,
            "precision": lead.get("precision", "day"),
            "phases": phases,
            "src": r["source"]["url"],
            "conf": r["confidence"],
            "published": r.get("published") or "",
        })
    out.sort(key=lambda x: (x["lead"] or "9999", x["title"]))
    return out

def ics_fold(line):
    """RFC 5545 折行：超过 75 octets 在 UTF-8 字符边界断行续行。"""
    out = []
    buf = line.encode("utf-8")
    while len(buf) > 75:
        cut = 75
        while cut > 0 and (buf[cut] & 0xC0) == 0x80:
            cut -= 1
        out.append(buf[:cut].decode("utf-8"))
        buf = b" " + buf[cut:]
    out.append(buf.decode("utf-8"))
    return "\r\n".join(out)


def ics_escape(s):
    return (str(s).replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\r\n", "\\n").replace("\n", "\\n"))


def build_ics(recs):
    """全部赛事输出为一个 RFC 5545 日历（site/competitions.ics）。"""
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//competition-timeline//cn//CN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:%s" % ics_escape("全国大学生竞赛时间轴"),
        "X-WR-TIMEZONE:Asia/Shanghai",
    ]
    n = 0
    for r in recs:
        for i, ph in enumerate(r["phases"]):
            start = (ph["start"] or "")[:10]
            end = (ph["end"] or "")[:10]
            # 只有 end 的阶段：把 end 当单日事件开始（截止日提醒语义）
            if len(start) != 10 and len(end) == 10:
                start, end = end, ""
            if len(start) != 10:  # 月精度(YYYY-MM)或全缺失的跳过
                continue
            n += 1
            dtend = ""
            if len(end) == 10 and end != start:
                d = date.fromisoformat(end)
                dtend = "DTEND;VALUE=DATE:%s" % (d + timedelta(days=1)).strftime("%Y%m%d")
            desc = r["org"]
            if r["src"]:
                desc += "\n来源: " + r["src"]
            lines += [
                "BEGIN:VEVENT",
                "UID:%s-%d@competition-timeline" % (r["id"], i),
                "DTSTAMP:" + now,
                "DTSTART;VALUE=DATE:%s" % start.replace("-", ""),
                dtend,
                "SUMMARY:%s" % ics_escape("%s · %s" % (r["title"], ph["name"])),
                "DESCRIPTION:%s" % ics_escape(desc),
                "URL:%s" % r["src"] if r["src"] else "",
                "END:VEVENT",
            ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(x for x in lines if x) + "\r\n", n


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    recs = build_records(data["records"])
    today = date.today().isoformat()

    cat_counts = Counter(r["cat"] for r in recs)
    cats = [{"name": n, "n": c} for n, c in cat_counts.most_common()]
    with_time = len(recs)
    total = data["counts"]["total"]

    payload = json.dumps(recs, ensure_ascii=False, separators=(",", ":"))
    cats_json = json.dumps(cats, ensure_ascii=False)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        TEMPLATE
        .replace("/*__DATA__*/", payload)
        .replace("/*__CATS__*/", cats_json)
        .replace("__TODAY__", today)
        .replace("__TOTAL__", str(total))
        .replace("__DATED__", str(with_time)),
        encoding="utf-8",
    )
    print("写入 %s" % OUT)
    print("赛事 %d 条（源记录 %d）/ 分类 %d 个" % (with_time, total, len(cats)))
    ics, n = build_ics(recs)
    ICS_OUT.write_text("\r\n".join(ics_fold(l) for l in ics.split("\r\n")) + "\r\n",
                       encoding="utf-8")
    print("写入 %s（%d 个日程）" % (ICS_OUT, n))
    for c in cats:
        print("   %-8s %d" % (c["name"], c["n"]))


TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>赛事时间轴 · 全国大学生竞赛节点聚合</title>
<script src="https://unpkg.com/lucide@0.454.0/dist/umd/lucide.js"></script>
<style>
:root{
  --bg:#fbfbfd; --card:#fff; --ink:#0b0b0f; --muted:#6e6e7a; --faint:#9a9aa6;
  --line:#e8e8ed; --line-2:#f0f0f4;
  --blue:#2563eb; --blue-soft:#eff4ff;
  --ok:#10b981; --warn:#f59e0b; --idle:#a1a1af;
  --r:14px; --r-sm:9px;
  --ease:cubic-bezier(.22,1,.36,1);
  --shadow:0 1px 2px rgba(11,11,15,.04),0 8px 24px -12px rgba(11,11,15,.10);
  --shadow-lg:0 2px 4px rgba(11,11,15,.04),0 20px 44px -16px rgba(11,11,15,.18);
}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-font-smoothing:antialiased;scroll-behavior:smooth}
body{
  font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",
       "Hiragino Sans GB","Microsoft YaHei",sans-serif;
  color:var(--ink); background:var(--bg); min-height:100vh;
}
a{color:inherit;text-decoration:none}
svg.i{width:15px;height:15px;stroke-width:2;flex:none;vertical-align:-2px}

/* ── 背景光斑 ───────────────────────────────────────── */
.aura{position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden}
.aura i{position:absolute;border-radius:50%;filter:blur(80px);opacity:.5}
.aura i:nth-child(1){width:520px;height:520px;left:-140px;top:-180px;
  background:radial-gradient(circle,#dbe7ff,transparent 68%)}
.aura i:nth-child(2){width:440px;height:440px;right:-120px;top:60px;
  background:radial-gradient(circle,#e6f0ff,transparent 68%)}
.aura i:nth-child(3){width:380px;height:380px;left:38%;top:-240px;
  background:radial-gradient(circle,#f0e9ff,transparent 70%)}

/* ── 导航 ───────────────────────────────────────────── */
.nav{
  position:sticky;top:0;z-index:60;
  backdrop-filter:saturate(180%) blur(14px);
  background:rgba(251,251,253,.82);
  border-bottom:1px solid transparent;
  transition:border-color .3s var(--ease),background .3s var(--ease);
}
.nav.stuck{border-bottom-color:var(--line);background:rgba(251,251,253,.94)}
.nav-in{max-width:1080px;margin:0 auto;padding:13px 24px;
  display:flex;align-items:center;gap:14px}
.brand{display:flex;align-items:center;gap:9px;font-weight:650;letter-spacing:-.01em}
.brand .mark{
  width:26px;height:26px;border-radius:8px;display:grid;place-items:center;
  background:linear-gradient(140deg,var(--blue),#4f8bff);color:#fff;
  box-shadow:0 4px 12px -4px rgba(37,99,235,.5);
}
.brand .mark svg{width:15px;height:15px;stroke-width:2.4}
.brand small{color:var(--faint);font-weight:450;font-size:12px}
.nav-sp{flex:1}
.search{
  display:flex;align-items:center;gap:7px;
  background:#fff;border:1px solid var(--line);border-radius:999px;
  padding:6px 13px;width:210px;
  transition:border-color .2s var(--ease),box-shadow .2s var(--ease),width .3s var(--ease);
}
.search:focus-within{border-color:var(--blue);box-shadow:0 0 0 3px var(--blue-soft);width:250px}
.search svg{color:var(--faint)}
.search input{border:0;outline:0;background:none;font:inherit;font-size:13px;width:100%}
.search input::placeholder{color:var(--faint)}
.btn-rss{
  display:flex;align-items:center;gap:6px;
  background:var(--ink);color:#fff;border:0;border-radius:999px;
  padding:7px 15px;font:inherit;font-size:13px;font-weight:550;cursor:pointer;
  transition:transform .18s var(--ease),box-shadow .18s var(--ease),opacity .18s;
}
.btn-rss:hover{transform:translateY(-1px);box-shadow:0 8px 18px -8px rgba(11,11,15,.5)}
.btn-rss:active{transform:translateY(0) scale(.97)}

/* ── Hero ───────────────────────────────────────────── */
.hero{position:relative;z-index:1;max-width:1080px;margin:0 auto;padding:60px 24px 30px}
.hero h1{
  font-size:clamp(30px,4.6vw,46px);line-height:1.12;letter-spacing:-.028em;
  font-weight:700;
}
.hero h1 em{
  font-style:normal;color:var(--blue);
  background:linear-gradient(120deg,var(--blue),#6d9dff);
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
}
.hero p{color:var(--muted);margin-top:14px;max-width:520px;font-size:15px}
.stats{display:flex;gap:36px;margin-top:34px;flex-wrap:wrap}
.stat b{
  display:block;font-size:30px;font-weight:680;letter-spacing:-.02em;
  font-variant-numeric:tabular-nums;
}
.stat b .u{font-size:14px;font-weight:500;color:var(--faint);margin-left:3px}
.stat span{font-size:12px;color:var(--faint);letter-spacing:.02em}

/* ── 控件条 ─────────────────────────────────────────── */
.ctl{
  position:sticky;top:53px;z-index:50;
  backdrop-filter:saturate(180%) blur(14px);
  background:rgba(251,251,253,.9);
  border-top:1px solid var(--line-2);border-bottom:1px solid var(--line);
}
.ctl-in{max-width:1080px;margin:0 auto;padding:11px 24px;
  display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.seg{display:flex;background:#f1f1f5;border-radius:999px;padding:3px;gap:2px}
.seg button{
  border:0;background:none;font:inherit;font-size:12.5px;font-weight:520;
  color:var(--muted);padding:5px 13px;border-radius:999px;cursor:pointer;
  transition:color .2s var(--ease),background .25s var(--ease),box-shadow .25s var(--ease);
  white-space:nowrap;
}
.seg button[aria-pressed="true"]{
  background:#fff;color:var(--ink);box-shadow:0 1px 3px rgba(11,11,15,.10);
}
.chips{display:flex;gap:6px;overflow-x:auto;flex:1;min-width:0;
  scrollbar-width:none;padding:1px}
.chips::-webkit-scrollbar{display:none}
.chip{
  border:1px solid var(--line);background:#fff;border-radius:999px;
  font:inherit;font-size:12.5px;color:var(--muted);
  padding:5px 12px;cursor:pointer;white-space:nowrap;flex:none;
  display:flex;align-items:center;gap:5px;
  transition:all .2s var(--ease);
}
.chip:hover{border-color:#cfcfd8;color:var(--ink);transform:translateY(-1px)}
.chip[aria-pressed="true"]{
  background:var(--ink);border-color:var(--ink);color:#fff;
}
.chip .n{font-size:11px;color:var(--faint);font-variant-numeric:tabular-nums}
.chip[aria-pressed="true"] .n{color:rgba(255,255,255,.62)}
.count{font-size:12px;color:var(--faint);margin-left:auto;white-space:nowrap}

/* ── 时间轴 ─────────────────────────────────────────── */
main{position:relative;z-index:1;max-width:1080px;margin:0 auto;padding:26px 24px 80px}
.grp{margin-bottom:34px}
.grp-h{
  display:flex;align-items:baseline;gap:11px;margin-bottom:14px;
  padding-left:2px;position:sticky;top:112px;
}
.grp-h h2{font-size:17px;font-weight:640;letter-spacing:-.015em}
.grp-h .ln{flex:1;height:1px;background:var(--line);margin-bottom:4px}
.grp-h .c{font-size:12px;color:var(--faint);font-variant-numeric:tabular-nums}

.rail{position:relative;padding-left:26px}
.rail::before{
  content:"";position:absolute;left:6px;top:10px;bottom:10px;width:1.5px;
  background:linear-gradient(180deg,var(--line),var(--line-2));
  border-radius:2px;
}

.card{
  position:relative;background:var(--card);border:1px solid var(--line);
  border-radius:var(--r);padding:15px 17px;margin-bottom:10px;
  box-shadow:var(--shadow);cursor:pointer;
  view-transition-name:var(--vt, none);
  transition:transform .26s var(--ease),box-shadow .26s var(--ease),
             border-color .26s var(--ease);
}
.card:hover{transform:translateY(-2px);box-shadow:var(--shadow-lg);border-color:#d8d8e0}
.card:hover .dot{transform:scale(1.5);background:var(--blue)}
.card:hover .go{opacity:1;transform:translate(0,0)}
.card.open{border-color:#c9d8ff;box-shadow:var(--shadow-lg)}
.card.open .dot{transform:scale(1.5);background:var(--blue)}

.dot{
  position:absolute;left:-23.5px;top:22px;width:8px;height:8px;border-radius:50%;
  background:#d8d8e0;border:2px solid var(--bg);
  transition:transform .3s var(--ease),background .3s var(--ease);
}
.card.past .dot{background:#e4e4ea}
.card.soon .dot{background:var(--warn)}
.card.past{opacity:.62}
.card.past .title{color:var(--muted)}

.top{display:flex;align-items:flex-start;gap:11px}
.title{
  font-size:15.5px;font-weight:600;letter-spacing:-.012em;line-height:1.42;flex:1;
}
.title mark{background:#fff3c4;color:inherit;border-radius:3px;padding:0 2px}
.go{
  color:var(--faint);opacity:.55;
  transition:opacity .25s var(--ease),transform .3s var(--ease),color .25s var(--ease);
}
.go svg{width:16px;height:16px;stroke-width:2}
.card:hover .go{opacity:1}
.card.open .go{opacity:1;color:var(--ink);transform:rotate(180deg)}

.badges{display:flex;gap:5px;flex-wrap:wrap;margin-top:9px}
.badge{
  font-size:11px;font-weight:540;border-radius:6px;padding:2.5px 7px;
  display:inline-flex;align-items:center;gap:4px;letter-spacing:.01em;
}
.badge svg{width:11px;height:11px;stroke-width:2.4}
.b-ok{background:#e9f9f2;color:#0a7a55}
.b-warn{background:#fef4e2;color:#9a6300}
.b-idle{background:#f2f2f6;color:#75757f}
.b-cat{background:var(--blue-soft);color:#1d4ed8}
.b-tag{background:#f6f6fa;color:#75757f;font-weight:480}

.org{font-size:12.5px;color:var(--faint);margin-top:7px;
  display:flex;align-items:center;gap:5px}
.org svg{width:13px;height:13px;opacity:.7}

.foot{display:flex;align-items:center;gap:14px;margin-top:11px;
  padding-top:10px;border-top:1px solid var(--line-2);flex-wrap:wrap}
.kd{display:flex;align-items:center;gap:6px;font-size:13px;font-weight:580;
  font-variant-numeric:tabular-nums}
.kd.hot{color:var(--warn)} .kd.over{color:var(--faint);font-weight:500}
.kd svg{width:14px;height:14px;stroke-width:2.2}
.kd.soon-pulse{animation:pulse 1.4s var(--ease) infinite}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.045)}}
.ph-mini{display:flex;gap:10px;margin-left:auto;flex-wrap:wrap}
.ph-mini span{font-size:12px;color:var(--faint);white-space:nowrap}
.ph-mini span i{font-style:normal;color:var(--muted);font-variant-numeric:tabular-nums}

/* 展开区 */
.more{
  display:grid;grid-template-rows:0fr;
  transition:grid-template-rows .38s var(--ease),opacity .3s var(--ease),
             margin-top .38s var(--ease);
  opacity:0;margin-top:0;
}
.card.open .more{grid-template-rows:1fr;opacity:1;margin-top:12px}
.more>div{overflow:hidden}
.ph-list{display:grid;gap:0;border-top:1px solid var(--line-2);padding-top:9px}
.ph-row{
  display:grid;grid-template-columns:1fr auto;gap:12px;align-items:baseline;
  padding:6px 0;font-size:13px;
}
.ph-row+.ph-row{border-top:1px dashed var(--line-2)}
.ph-row .nm{color:var(--muted)}
.ph-row .dt{font-variant-numeric:tabular-nums;font-weight:560;text-align:right}
.ph-row .dt small{color:var(--faint);font-weight:450;margin-left:5px;font-size:11px}
.acts{display:flex;gap:9px;margin-top:11px;flex-wrap:wrap}
.act{
  font-size:12.5px;display:inline-flex;align-items:center;gap:5px;
  border:1px solid var(--line);border-radius:var(--r-sm);padding:5px 11px;
  color:var(--muted);transition:all .2s var(--ease);
}
.act:hover{border-color:#cfcfd8;color:var(--ink);transform:translateY(-1px)}
.act svg{width:13px;height:13px}
.note{font-size:11.5px;color:var(--faint);margin-top:9px;
  display:flex;align-items:flex-start;gap:6px;line-height:1.5}
.note svg{width:12px;height:12px;margin-top:2px}
.ph-mini .mn{color:var(--faint);font-size:11.5px;margin-left:7px}
.conf{font-size:11px;font-weight:540;display:inline-flex;align-items:center;gap:4px;
  border-radius:6px;padding:2.5px 7px;white-space:nowrap}
.conf svg{width:11px;height:11px;stroke-width:2.4}

/* 页脚说明 */
.legend{
  margin:34px auto 0;max-width:820px;padding:18px 20px;
  background:var(--card);border:1px solid var(--line);border-radius:var(--r);
  display:flex;gap:11px;align-items:flex-start;
}
.legend svg{width:15px;height:15px;color:var(--faint);margin-top:2px;flex:none}
.legend p{font-size:12.5px;color:var(--muted);line-height:1.65}
.legend b{color:var(--ink);font-weight:560}

/* 空状态 */
.empty{text-align:center;padding:70px 20px;color:var(--faint)}
.empty svg{width:34px;height:34px;margin:0 auto 14px;display:block;opacity:.4}
.empty p{font-size:13.5px}

/* 进 / 出动画 */
@keyframes rise{
  from{opacity:0;transform:translateY(14px) scale(.985)}
  to{opacity:1;transform:translateY(0) scale(1)}
}
@keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@keyframes out{to{opacity:0;transform:translateY(-6px) scale(.97)}}
@keyframes blurIn{from{opacity:0;filter:blur(9px);transform:translateY(16px)}
  to{opacity:1;filter:blur(0);transform:none}}
.anim{animation:rise .5s var(--ease) both}
.enter{animation:fadeUp .42s var(--ease) both}
.hero h1{animation:blurIn .78s var(--ease) both}
.hero p{animation:blurIn .78s var(--ease) .1s both}
.stat{animation:blurIn .7s var(--ease) both}
.stat:nth-child(1){animation-delay:.18s}
.stat:nth-child(2){animation-delay:.26s}
.stat:nth-child(3){animation-delay:.34s}
@media (prefers-reduced-motion:reduce){
  *{animation-duration:.01ms!important;transition-duration:.01ms!important}
}

/* 滚动进视口 */
.reveal{opacity:0;transform:translateY(16px)}
.reveal.in{
  opacity:1;transform:none;
  transition:opacity .55s var(--ease),transform .55s var(--ease);
}

/* 原生 View Transitions：筛选重排的 morph */
::view-transition-old(root),::view-transition-new(root){animation-duration:.34s}

footer{
  position:relative;z-index:1;max-width:1080px;margin:0 auto;
  padding:0 24px 60px;color:var(--faint);font-size:12.5px;
}
footer .box{border-top:1px solid var(--line);padding-top:22px;display:grid;
  gap:9px}
footer b{color:var(--muted);font-weight:600}
footer .ln{display:flex;gap:7px;align-items:flex-start;line-height:1.6}

.toast{
  position:fixed;left:50%;bottom:28px;transform:translate(-50%,14px);
  background:var(--ink);color:#fff;font-size:13px;padding:9px 17px;
  border-radius:999px;opacity:0;pointer-events:none;z-index:99;
  transition:opacity .28s var(--ease),transform .28s var(--ease);
  display:flex;align-items:center;gap:7px;
}
.toast.on{opacity:1;transform:translate(-50%,0)}

@media(max-width:640px){
  .nav-in,.hero,.ctl-in,main,footer{padding-left:16px;padding-right:16px}
  .search{width:150px}.search:focus-within{width:180px}
  .stats{gap:22px}.stat b{font-size:24px}
  .hero{padding-top:38px}
  .ph-mini{display:none}
  .brand small{display:none}
}
</style>
</head>
<body>

<div class="aura"><i></i><i></i><i></i></div>

<header class="nav" id="nav">
  <div class="nav-in">
    <div class="brand">
      <span class="mark"><i data-lucide="trophy"></i></span>
      赛事时间轴 <small>competition-timeline</small>
    </div>
    <div class="nav-sp"></div>
    <label class="search">
      <i data-lucide="search"></i>
      <input id="q" type="search" placeholder="搜赛事 / 主办单位" autocomplete="off">
    </label>
    <button class="btn-rss" id="ics">
      <i data-lucide="calendar-plus"></i> 订阅
    </button>
  </div>
</header>

<section class="hero">
  <h1>全国大学生竞赛<br><em>时间节点</em>一站式聚合</h1>
  <p>报名截止、校赛、赛区赛、决赛，按月份排到一条时间轴上。每个节点都带来源标注。</p>
  <div class="stats">
    <div class="stat"><b><span id="s-open">0</span><span class="u">项</span></b>
      <span>可报名</span></div>
    <div class="stat"><b><span id="s-soon">0</span><span class="u">项</span></b>
      <span>近 30 天截止</span></div>
    <div class="stat"><b data-count="__DATED__">0<span class="u">项</span></b>
      <span>已收录（含往届）</span></div>
  </div>
</section>

<div class="ctl" id="ctl">
  <div class="ctl-in">
    <div class="seg" id="seg-status">
      <button data-v="open" aria-pressed="true">可报名</button>
      <button data-v="all" aria-pressed="false">全部</button>
      <button data-v="past" aria-pressed="false">已截止</button>
    </div>
    <div class="chips" id="chips"></div>
    <div class="count" id="count"></div>
  </div>
</div>

<main id="list"></main>

<footer>
  <div class="box">
    <div class="ln"><b>数据来源</b>
      <span>发现层：我爱竞赛网榜单竞赛索引（<span id="f-total"></span> 条原始记录）。
      权威层：中国高等教育学会、教育部高教司、各竞赛官网。</span></div>
    <div class="ln"><b>核验状态</b>
      <span>自动导入的记录标「待核验」，链接指向聚合源；经官方通知核验后升级为
      「已核验」，链接改为官方地址。</span></div>
    <div class="ln"><b>这是视觉稿</b>
      <span>数据为自动解析结果，未逐条人工核验，请勿直接据此报名。</span></div>
  </div>
</footer>

<div class="toast" id="toast"><i data-lucide="check"></i><span id="toast-t"></span></div>

<script>
const DATA = /*__DATA__*/;
const CATS = /*__CATS__*/;
const TODAY = new Date("__TODAY__T00:00:00");

/* ── 工具 ─────────────────────────────────────────── */
const $  = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => [...r.querySelectorAll(s)];

function daysFrom(iso){
  if(!iso) return null;
  const p = iso.split("-").map(Number);
  const d = new Date(p[0], (p[1]||1)-1, p[2]||1);
  return Math.round((d - TODAY) / 864e5);
}
function fmtDate(iso){
  if(!iso) return "待定";
  const p = iso.split("-");
  return p.length === 3 ? `${+p[1]}月${+p[2]}日` : `${+p[1]}月`;
}
function fmtKd(n){
  if(n === null) return {t:"时间待定", c:""};
  if(n < 0)   return {t:"已截止", c:"over"};
  if(n === 0) return {t:"今天截止", c:"hot soon-pulse"};
  if(n === 1) return {t:"明天截止", c:"hot soon-pulse"};
  if(n <= 7)  return {t:`还剩 ${n} 天`, c:"hot soon-pulse"};
  if(n <= 30) return {t:`还剩 ${n} 天`, c:"hot"};
  if(n <= 120)return {t:`还剩 ${n} 天`, c:""};
  return {t:`还有 ${n} 天`, c:""};
}
function esc(s){return (s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]))}
function hl(s,q){
  if(!q) return esc(s);
  const i = s.toLowerCase().indexOf(q.toLowerCase());
  if(i < 0) return esc(s);
  return esc(s.slice(0,i)) + "<mark>" + esc(s.slice(i,i+q.length)) + "</mark>"
       + esc(s.slice(i+q.length));
}
const CONF = {
  confirmed:{t:"已核验", c:"b-ok",   i:"badge-check"},
  tentative:{t:"待核验", c:"b-warn", i:"alert-circle"},
  estimated:{t:"推算",   c:"b-idle", i:"help-circle"},
};

/* ── 状态 ─────────────────────────────────────────── */
let state = {status:"open", cat:"全部", q:""};

function statusOf(r){
  // 可报名 = 报名还开着。有报名截止点就看它，没有才退回最早节点。
  const n = daysFrom(r.reg_end || r.lead);
  if(n === null) return "unknown";
  return n < 0 ? "past" : "open";
}
/* 排序/倒计时都用「报名截止」优先，这才对应「还能不能报」 */
function topDate(r){
  return r.reg_end || r.lead;
}
function pass(r){
  if(state.cat !== "全部" && r.cat !== state.cat) return false;
  if(state.status !== "all" && statusOf(r) !== state.status) return false;
  if(state.q){
    const q = state.q.toLowerCase();
    if(!(r.title.toLowerCase().includes(q) || (r.org||"").toLowerCase().includes(q)))
      return false;
  }
  return true;
}

/* 排序：未来的按日期升序在前，已截止的倒序沉底 */
function order(a, b){
  const da = daysFrom(topDate(a)), db = daysFrom(topDate(b));
  const fa = da === null ? 1 : (da >= 0 ? 0 : 1);
  const fb = db === null ? 1 : (db >= 0 ? 0 : 1);
  if(fa !== fb) return fa - fb;
  if(fa === 0) return (da ?? 9e9) - (db ?? 9e9);
  return (db ?? -9e9) - (da ?? -9e9);
}

/* ── 渲染 ─────────────────────────────────────────── */
function cardHTML(r, qi){
  const kd = fmtKd(daysFrom(topDate(r)));
  const cf = CONF[r.conf] || CONF.tentative;
  const st = statusOf(r);
  const tags = (r.tags||[]).filter(t => !/^榜单(赛事|竞赛)$/.test(t)).slice(0,2);
  const mini = `<span>${esc(r.phases[0].name)} <i>${fmtDate(r.phases[0].start)}</i></span>`
    + (r.phases.length > 1
        ? `<span class="mn">共 ${r.phases.length} 个节点</span>` : "");

  const rows = r.phases.map(p => `
    <div class="ph-row">
      <span class="nm">${esc(p.name)}</span>
      <span class="dt">${fmtDate(p.start)}${p.end && p.end!==p.start
        ? ` <small>→ ${fmtDate(p.end)}</small>` : ""}${
        p.precision==="month" ? ` <small>月份精度</small>` : ""}</span>
    </div>`).join("");

  return `
  <article class="card anim ${st}" data-id="${r.id}"
           style="animation-delay:${Math.min(qi*32,420)}ms;--vt:card-${r.id}">
    <span class="dot"></span>
    <div class="top">
      <h3 class="title">${hl(r.title, state.q)}</h3>
      <i class="i go" data-lucide="chevron-down"></i>
    </div>
    ${(tags.length || r.cat) ? `<div class="badges">
      <span class="badge b-cat">${esc(r.cat)}</span>
      ${tags.map(t=>`<span class="badge b-tag">${esc(t)}</span>`).join("")}
    </div>` : ""}
    ${r.org ? `<div class="org"><i data-lucide="building-2"></i>${esc(r.org)}</div>` : ""}
    <div class="foot">
      <span class="kd ${kd.c}"><i data-lucide="clock"></i>${kd.t}</span>
      <div class="ph-mini">${mini}</div>
      <span class="conf ${cf.c}" title="${cf.t}">
        <i data-lucide="${cf.i}"></i>${cf.t}</span>
    </div>
    <div class="more"><div>
      <div class="ph-list">${rows}</div>
      <div class="acts">
        <a class="act" href="${esc(r.src)}" target="_blank" rel="noopener">
          <i data-lucide="external-link"></i>查看来源通知</a>
        <span class="act" data-ics="${r.id}">
          <i data-lucide="calendar-plus"></i>加入日历</span>
      </div>
    </div></div>
  </article>`;
}

function groupKey(r){
  const p = (topDate(r)||"").split("-");
  return p.length >= 2 ? `${p[0]}-${p[1]}` : "9999-99";
}
function monthName(k){
  if(k === "9999-99") return "时间待定";
  const [y,m] = k.split("-").map(Number);
  return `${y} 年 ${m} 月`;
}

function render(){
  const rows = DATA.filter(pass).sort(order);
  const list = $("#list");

  $("#count").textContent = `${rows.length} / ${DATA.length} 项`;

  if(!rows.length){
    list.innerHTML = `<div class="empty">
      <i data-lucide="search-x"></i>
      <p>没有匹配的赛事，换个筛选或关键词试试</p></div>`;
    if(window.lucide) lucide.createIcons();
    return;
  }

  // 按月份分组，靠 rows 的既有顺序保证组顺序（未来在前、已截止沉底）
  const groups = new Map();
  for(const r of rows){
    const k = groupKey(r);
    if(!groups.has(k)) groups.set(k, []);
    groups.get(k).push(r);
  }

  let qi = 0;
  list.innerHTML = [...groups.entries()]
    .map(([k, items]) => `
      <section class="grp">
        <div class="grp-h reveal">
          <h2>${monthName(k)}</h2><span class="ln"></span>
          <span class="c">${items.length} 项</span>
        </div>
        <div class="rail">${items.map(r => cardHTML(r, qi++)).join("")}</div>
      </section>`).join("");

  if(window.lucide) lucide.createIcons();
  observeReveal();
}

/* ── 滚动进视口 ───────────────────────────────────── */
let io;
function observeReveal(){
  if(io) io.disconnect();
  io = new IntersectionObserver(es => {
    for(const e of es){
      if(e.isIntersecting){ e.target.classList.add("in"); io.unobserve(e.target); }
    }
  }, {rootMargin:"0px 0px -8% 0px", threshold:.05});
  $$(".reveal").forEach(el => io.observe(el));
}

/* ── 交互 ─────────────────────────────────────────── */
function morph(fn){
  if(!document.startViewTransition || matchMedia("(prefers-reduced-motion:reduce)").matches){
    fn(); return;
  }
  document.startViewTransition(fn);
}

function apply(patch){
  Object.assign(state, patch);
  $$("#seg-status button").forEach(b =>
    b.setAttribute("aria-pressed", String(b.dataset.v === state.status)));
  $$("#chips button").forEach(b =>
    b.setAttribute("aria-pressed", String(b.dataset.v === state.cat)));
  morph(render);
}

function buildChips(){
  const box = $("#chips");
  const rows = [{name:"全部", n:DATA.length},
                ...CATS.filter(c => c.n > 0).map(c => ({name:c.name, n:c.n}))];
  box.innerHTML = rows.map(c =>
    `<button class="chip" data-v="${esc(c.name)}"
      aria-pressed="${c.name === state.cat}">${esc(c.name)}<span class="n">${c.n}</span>
    </button>`).join("");
}

/* ICS 生成 */
function icsEscape(s){
  return String(s).replace(/\\/g,"\\\\").replace(/;/g,"\\;")
    .replace(/,/g,"\\,").replace(/\r?\n/g,"\\n");
}
function fmtDT(d){
  return d.replace(/-/g,"");
}
function recToICS(r){
  const now = new Date();
  const stamp = now.toISOString().replace(/[-:]/g,"").replace(/\.\d+Z$/,"Z");
  const lines = ["BEGIN:VCALENDAR","VERSION:2.0",
    "PRODID:-//competition-timeline//cn//CN","CALSCALE:GREGORIAN",
    "METHOD:PUBLISH","X-WR-CALNAME:" + icsEscape("大学生竞赛时间轴")];
  (r.phases || []).forEach((ph,i) => {
    if(!ph.start) return;
    // RFC 5545: 全天事件 DTEND 为排他日期，需 +1 天
    let dtEnd = "";
    if(ph.end && ph.end !== ph.start){
      const d = new Date(ph.end + "T00:00:00Z");
      d.setUTCDate(d.getUTCDate() + 1);
      dtEnd = "DTEND;VALUE=DATE:" + d.toISOString().slice(0,10).replace(/-/g,"");
    }
    lines.push("BEGIN:VEVENT",
      "UID:" + r.id + "-" + i + "@competition-timeline",
      "DTSTAMP:" + stamp,
      "DTSTART;VALUE=DATE:" + fmtDT(ph.start),
      dtEnd,
      "SUMMARY:" + icsEscape(r.title + " · " + ph.name),
      "DESCRIPTION:" + icsEscape((r.org || "") + (r.url ? "\n来源: " + r.url : "")),
      "END:VEVENT");
  });
  lines.push("END:VCALENDAR");
  return lines.filter(Boolean).join("\r\n") + "\r\n";
}
function downloadICS(r){
  const blob = new Blob([recToICS(r)], {type:"text/calendar;charset=utf-8"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = r.title.replace(/[\\/:*?"<>|]/g,"_").slice(0,40) + ".ics";
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 3000);
  toast("已下载日历文件，双击导入即可");
}
function downloadAllICS(){
  const blob = new Blob([DATA.filter(r => r.phases && r.phases.some(p => p.start))
    .map(recToICS).join(""), {type:"text/calendar;charset=utf-8"}]);
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "competition-timeline-all.ics";
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 3000);
  toast("已导出全部赛事日历（" + DATA.length + " 项）");
}

/* 卡片展开 / 加入日历 */
$("#list").addEventListener("click", e => {
  const ics = e.target.closest("[data-ics]");
  if(ics){
    e.stopPropagation();
    const r = DATA.find(x => String(x.id) === ics.dataset.ics);
    if(r) downloadICS(r);
    return;
  }
  if(e.target.closest(".act")) return;
  const card = e.target.closest(".card");
  if(card) card.classList.toggle("open");
});

$("#seg-status").addEventListener("click", e => {
  const b = e.target.closest("button");
  if(b) apply({status: b.dataset.v});
});
$("#chips").addEventListener("click", e => {
  const b = e.target.closest("button");
  if(b) apply({cat: b.dataset.v});
});

let qt;
$("#q").addEventListener("input", e => {
  clearTimeout(qt);
  qt = setTimeout(() => apply({q: e.target.value.trim()}), 180);
});

/* 订阅按钮：http(s) 部署时用静态 competitions.ics 供日历软件订阅；file:// 时下载合并日历 */
$("#ics").addEventListener("click", () => {
  if(location.protocol.startsWith("http")){
    const url = new URL("competitions.ics", location.href).href;
    window.open(url, "_blank");
    toast("日历软件里粘贴此 URL 即可长期订阅（已复制）");
    navigator.clipboard && navigator.clipboard.writeText(url).catch(() => {});
  } else {
    downloadAllICS();
  }
});

/* toast */
let tt;
function toast(msg){
  $("#toast-t").textContent = msg;
  $("#toast").classList.add("on");
  clearTimeout(tt);
  tt = setTimeout(() => $("#toast").classList.remove("on"), 1900);
}

/* 导航栏滚动态 */
addEventListener("scroll", () => {
  $("#nav").classList.toggle("stuck", scrollY > 8);
}, {passive:true});

/* 数字滚动 */
function countUp(){
  $$("[data-count]").forEach(el => {
    const target = +el.dataset.count, unit = el.querySelector(".u");
    if(!target){ return; }
    const dur = 900, t0 = performance.now();
    (function step(t){
      const p = Math.min(1, (t - t0) / dur);
      const v = Math.round(target * (1 - Math.pow(1 - p, 3)));
      el.innerHTML = v + (unit ? unit.outerHTML : "");
      if(p < 1) requestAnimationFrame(step);
    })(t0);
  });
}

/* 可报名数 + 近 30 天截止数 */
function computeOpen(){
  const open = DATA.filter(r => {
    const d = daysFrom(topDate(r));
    return d !== null && d >= 0;
  }).length;
  const soon = DATA.filter(r => {
    const d = daysFrom(topDate(r));
    return d !== null && d >= 0 && d <= 30;
  }).length;
  $("#s-open").textContent = open;
  $("#s-soon").textContent = soon;
}

/* 启动 */
buildChips();
computeOpen();
render();
countUp();
$("#f-total").textContent = "__TOTAL__";
</script>
</body>
</html>
"""


if __name__ == "__main__":
    SystemExit(main())
