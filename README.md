# 全国大学生竞赛时间轴

一个面向全国大学生的竞赛时间聚合静态站点：收录正在报名 / 即将截止的学科竞赛，提供按月份分组的时间轴视图、筛选、倒计时，以及**可直接订阅的日历（.ics）**。

线上地址：**https://wdfdsyhb.github.io/competition-timeline/**

## 这个项目解决什么问题

全国大学生竞赛（数模、电赛、蓝桥杯、挑战杯、各类设计/写作/编程大赛…）的报名时间散落在几百个官网、公众号和聚合站里，没有一个统一的「什么时候截止」视图。本项目的做法：

1. **抓取**：从「我爱竞赛网」榜单竞赛索引抓取结构化的赛事+阶段时间（列表页自带 `赛事名||阶段名：时间` 格式，可直接正则解析）
2. **回源补漏**：对列表页没带时间的记录，回抓其文章页正文，解析「阶段名：日期」「即日起至X」「X前」三类时间行，同时抽取真实的赛事官网链接
3. **构建**：校验、分类（11 类学科）、按 lead 日期排序，产出单文件静态站 + RFC 5545 日历
4. **部署**：纯静态托管 GitHub Pages，零后端

## 当前数据规模

| 指标 | 数值 |
|---|---|
| 源记录 | 208 条 |
| 站点条目（有具体时间） | 166 条 |
| 日历日程（VEVENT） | 245 个 |
| 数据可信度 | 学生赛事 `tentative`（自动解析）；企业赛 `confirmed`（官方接口/官方赛程表） |

### 数据来源构成

| 源 | 条数 | 置信度 | 类型 |
|---|---|---|---|
| 我爱竞赛网榜单索引 | 172 | tentative | 聚合站（GB18030 页面） |
| 中国研究生创新实践系列大赛（cpipc） | 21 | confirmed | 官方赛程表 HTML |
| 阿里云天池 | 13 | confirmed | 官方列表 API（免登录） |
| 百度之星 | 1 | confirmed | webpack chunk 内嵌数据 |
| 华为软件精英挑战赛 | 1 | confirmed | vite chunk 内嵌数据 |

## 快速开始

### 浏览

直接访问线上站点，或双击 `index.html`（纯离线单文件，数据内嵌）。

### 订阅日历

- 手机/电脑日历 App 里「添加订阅日历」，粘贴：
  `https://wdfdsyhb.github.io/competition-timeline/competitions.ics`
- 本地 file:// 打开时，「订阅」按钮会降级为下载合并 ics 文件

### 本地构建

```bash
pip install nothing    # 纯标准库，零依赖
python tools/fetch_52jingsai.py      # 抓列表 → data/candidates.json
python tools/enrich_articles.py      # 回源文章页补时间
python tools/enrich_official.py      # 官网直连补时（命中率低，可选）

# 企业赛专源（各抓各的，最后统一合并）
python tools/fetch_cpipc.py          # 研究生创新实践系列大赛
python tools/fetch_baidustar.py      # 百度之星（webpack chunk 静态提取）
python tools/fetch_codecraft.py      # 华为软挑（vite chunk 静态提取）
python tools/fetch_tianchi.py        # 阿里云天池（官方 API）
python tools/merge_corporate.py      # 合并进 candidates.json（幂等）

python tools/build_draft.py          # 生成 index.html + competitions.ics
```

## 仓库结构

```
├── index.html              # 单文件站点（数据内嵌，双击可开）
├── competitions.ics        # 全量日历（订阅用）
├── data/
│   ├── candidates.json     # 主数据（52jingsai + 合并后的企业赛）
│   ├── cpipc.json          # 研究生系列赛
│   ├── candidates_baidustar.json
│   ├── candidates_codecraft.json
│   └── candidates_tianchi.json
├── tools/
│   ├── fetch_52jingsai.py  # S 级源：榜单竞赛索引抓取
│   ├── enrich_articles.py  # 回源文章页补时间/官网链接
│   ├── enrich_official.py  # 官网直连补时（P2）
│   ├── fetch_cpipc.py      # 企业赛：官方赛程表 HTML
│   ├── fetch_baidustar.py  # 企业赛：webpack chunk 静态提取
│   ├── fetch_codecraft.py  # 企业赛：vite chunk 静态提取
│   ├── fetch_tianchi.py    # 企业赛：官方 JSON API
│   ├── merge_corporate.py  # 专源合并（标题归一化去重 + id 幂等）
│   └── build_draft.py      # 构建器：candidates → 站点 + ics
├── docs/
│   ├── DATASOURCES-2026-10-22.md   # 数据源实测报告（含源分级、参数表、坑）
│   ├── GITHUB-SURVEY-2026-10-22.md # 同类项目调研（无成品，本项目的差异化）
│   └── PROGRESS.md                 # 进度与决策日志
```

## 数据可信度说明

`confidence` 三档（与 GithHub 上 deadline 类项目惯例一致）：

- `confirmed` 已核验 — 与官网原文对照过（当前暂无）
- `tentative` 待核验 — 来自聚合站/文章页自动解析，**绝大多数来源**
- `estimated` 推算 — 官网直连自动解析

站点上每张卡片都带可信度徽章。**自动解析的时间可能不准（尤其「即日起至X」的语义、跨年份混淆），重要赛事请以官网为准**——数据里保留了 `source` 字段，点击卡片可回溯源页面。

## 架构取舍（写给想 fork/贡献的人）

- **零依赖、零后端**：标准库 urllib + 正则，不用 Scrapy/Playwright。代价是 JS 渲染的站点（蓝桥杯等）抓不到，这点在 `docs/DATASOURCES` 里有分级结论
- ** GB18030**：国内老站编码混乱，fetcher 统一按 charset 声明嗅探 + utf-8/gbk 回退
- **列表页结构化时间 > 正文解析**：实测 52jingsai 列表摘要自带时间字段，命中率 69%；文章页回源补到 77%
- **官网直连性价比低**：大部分竞赛官网是 SPA 或日期图片化，P2 实测 21 条仅命中 1 条，见 PROGRESS.md
- **年度巡检**：竞赛日期每年更新，建议每年 9 月新一届发布季重跑一次 fetch 链路

## Roadmap

- [ ] 人工核验 top 高价值竞赛（数模/电赛/挑战杯/互联网+）→ confirmed
- [ ] 每年 9 月自动巡检（GitHub Actions cron + 自动 PR）
- [ ] 更多源：中国大学生在线、全国大学生创业服务网
- [x] 企业赛专源：cpipc / 百度之星 / 华为软挑 / 阿里天池
- [ ] 腾讯开悟（接口 403，赛事页 chunk 404，暂搁置）
- [ ] 小程序端（同一份 JSON 数据）

## 企业赛抓取的三种套路

企业赛官网几乎都是 SPA，但赛程数据往往藏在能静态拿到的地方。本项目验证过的三条路：

| 套路 | 适用 | 实现 |
|---|---|---|
| 官方 JSON API | 后端接口免登录 | `fetch_tianchi.py`：`/v3/proxy/competition/api/race/page`，参数 `isActive` 必须传数字 `1` |
| webpack chunk 静态提取 | 编译产物里内嵌了 SSR/模板数据 | `fetch_baidustar.py`：从 `_buildManifest` 拿 hash 表（**取最后一个匹配**，css/js 各一张），拉路由 chunk，正则抠赛程 |
| vite chunk 静态提取 | Vite 打包，env 变量里带赛事 ID | `fetch_codecraft.py`：主 bundle 挖 `VITE_APP_CompetitionId_2026`，路由 chunk 里 `mu=[{id,date}]` 给全赛程 |

反面案例：腾讯开悟（`aiarena.tencent.com`）的 `/api/v5/fe/AIArena/ListMatch` 等接口一律 403，`/match` 路由 chunk 404，只有新闻列表 API 可用 —— 拿不到结构化赛程，已记录放弃理由。

## 相关文档

- 数据源实测：[docs/DATASOURCES-2026-10-22.md](docs/DATASOURCES-2026-10-22.md)
- 同类项目调研：[docs/GITHUB-SURVEY-2026-10-22.md](docs/GITHUB-SURVEY-2026-10-22.md)
- 进度与决策：[docs/PROGRESS.md](docs/PROGRESS.md)

## License

数据抓取自公开网页，版权归原发布单位；代码 MIT。
