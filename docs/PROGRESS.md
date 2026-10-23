# 项目进度日志

## P1 收尾（2026-10-22）

### 完成
- `site/competitions.ics`：构建层产出静态 RFC 5545 日历（120 VEVENT / ~36KB）
  - UTF-8 按 75 octet 折行续行（字符边界不断开）
  - 多天事件 DTEND 为排他日期（end +1 天）
  - 月精度（YYYY-MM）模糊日期跳过，不进日历（`date.fromisoformat` 不接受 '2027-04'）
- 前端订阅双模：http(s) 下打开/复制 `competitions.ics` URL（长期订阅）；`file://` 降级为 Blob 下载合并 ics
- 卡片级「加入日历」：按赛事单独下载 ics
- E2E：python http.server 拉取 ics 200 OK；折行展开 VEVENT 配对完整
- git 仓库初始化：首提交 `6fec3a7`（main 分支），忽略 `__pycache__/`、`.dsh-switchman/`

### 环境坑（勿重复踩）
- bash 里 `>nul` 是 cmd 语法，bash 会创建名为 `nul` 的真文件；删除需扩展路径：
  `[System.IO.File]::Delete("\\?\D:\...\site\nul")`（普通 Remove-Item 报路径不存在）
- Python 端 `date.fromisoformat` 不接受月精度 '2027-04'，ics 生成前按 start/end 长度过滤

### 下一步（用户确认顺序 2→3→1）
2. 部署 GitHub Pages（本地提交是占位身份 yg@local，需用户提供 GitHub 仓库）
3. 回源补漏：54 条无时间记录抓 52jingsai 文章页 `article-<id>-1.html`
1. P2 扩源：cahe.edu.cn（教育学会 `/site/content/<id>.html`）、mcm.edu.cn（数模）


## 回源补漏完成（2026-10-22 晚）

### 结果
- `tools/enrich_articles.py`：抓 52jingsai 文章页（GB18030）补时间 + 官网链接
- 54 条无时间记录 → 35 条命中（12 条补出阶段时间，21 条只补到官网 URL，2 条纯噪声过滤后无发现）
- 数据面：133/173 条有阶段；站点条目 118 → **131**；ics 日程 120 → **162**
- enrich 产出的阶段多为 start=null、仅 end（截止日语义）→ build_draft/ics 增加 end 回退：
  - build_records：lead = start or end；dated 排序键同
  - build_ics：只有 end 的阶段把 end 当单日事件 DTSTART（截止提醒）
- 已部署上线（commit 15f51ec）

### 关键坑
- enrich 的 phases 结构无 precision/raw 键 → build_records KeyError，用 .get 默认值修复
- 文章页底部推荐栏「XX活动||征集截止时间：…||主办...」是噪声，extract_phases 里 `||` 行直接跳过
- candidates.json 的 source 字段是 dict（type/name/url），不是 str，取 source['url']
- build_draft.py 的 SRC 一度读旧 candidates.json 导致「enrich 无效」假象，cp enriched 覆盖后正常

### 剩余
- 19 条 nofind（文章页正文无可解析日期，多为纯通知类或规则文件）——留人工或后续扩源覆盖
- P2 扩源：cahe.edu.cn / mcm.edu.cn


## P2 官网直连补时（2026-10-22 晚）

### 结果
- `tools/enrich_official.py`：对 21 条有 official_url 无时间的记录抓官网首页+通知列表页（深度 1），解析时间行
- 产出：+1 条（2025 年第十七届全国大学生数学竞赛：报名截止 2026-05-09、考试 2026-05-10 等多阶段）
- 2 条 fetch fail（nuedc.xjtu.edu.cn 仅 http、cmes-imic.org.cn），18 条 nofind（官网多为 JS 渲染/无明确年度日期）
- 数据面：站点 131 → **132**；ics 162 → **166**

### 评估（诚实结论）
- cahe.edu.cn（学会）：主站栏目是课题/招聘/论坛，竞赛通知含量低，评估云（竞赛目录权威源）反爬不可抓
- mcm.edu.cn（数模）：列表页由 JS 加载无静态接口；赛程规则稳定（每年 9 月第二个周末周四 18:00~周日 20:00）但官方未公布 2027 具体
- 官网直连的边际收益低：大多数竞赛官网是 Vue/React SPA 或资讯图片化。**S 级 52jingsai 列表页已覆盖大部分**，剩余时间缺口靠人工核验或年度巡检更划算

### 建议（供后续决定）
1. 年度巡检：52jingsai 榜单每年 9 月重抓一次（新一届发布季）
2. 人工核验通道：high-value 竞赛（数模/电赛/挑战杯/互联网+）单独维护 confirmed 档案
3. 若要扩：优先「中国大学生在线」和「全国大学生创业服务网」而非 cahe/mcm


## 企业赛专源扩张（2026-10-23）

### 数据面
| 阶段 | 站点条目 | 源记录 | VEVENT | 企业赛专源 |
|---|---|---|---|---|
| P1 完成 | 118 | 173 | 166 | — |
| + cpipc | 153 | 195 | 226 | cpipc 21 |
| + 百度之星 | 167 | 208 | 229 | +baidustar 1 |
| + 华为软挑 | 153 | 195 | 228 | +codecraft 1 |
| + 阿里天池 | **166** | **208** | **245** | +tianchi 13 |

### 抓取套路沉淀（三种）
1. **官方 JSON API**（天池）：`GET /v3/proxy/competition/api/race/page?visualTab={1|2}&pageNum={n}&isActive=1`
   - `isActive` 必须传数字 `1`，传 `true` 报 `TST-SYS-ILL_ARGS`
   - `visualTab` 必须数字（1=AI大模型赛，2=其它）
   - `pages` 字段不可信（报 1 实际 2 页）→ 翻到空页为止
   - 返回体自带 `signupStartTime/EndTime` + `raceStartTime/EndTime`，无需解析 HTML
2. **webpack chunk 静态提取**（百度之星）：`_buildManifest.js` 里 css/js 各一张 id→hash 表，`find_chunk_hash` 必须取**最后一个**匹配
3. **vite chunk 静态提取**（华为软挑）：主 bundle 挖 `VITE_APP_CompetitionId_2026`，路由 chunk 里 `mu=[{id,date}]`

### 失败案例：腾讯开悟（aiarena.tencent.com）
- 后端 Next.js SSR，`/api/v5/fe/AIArena/ListMatch|ListGame|ListCompetition` 等全部 **403**
- `ListArticle` 可用（POST `{page:{current,size}, skipCheckLogin:true}`）但只有新闻（63 条，type 全 news/paper）
- `/[lang]/match` 路由 chunk 用百分号编码拉取仍 404
- 结论：拿不到结构化赛程，暂搁置

### 修复
- `build_ics` 兼容带时分秒的 ISO 日期（`2026-03-16T09:00:00`）：`start[:10]` 截断，否则软挑 4 阶段全被跳过
- `merge_corporate.py`：id 幂等（重复跑不追加）+ `official_url` 改 `.get`（百度之星记录无此键）
- `build_draft.py`：`title_raw/organizer/tags/published` 全改 `.get`，兼容专源记录缺键
- 去重：`2025年第七届全国高校计算机能力挑战赛` 同质双条（22452/22454）删一条

### 坑
- `git commit --amend` 改写已推送提交 → push 被拒（non-fast-forward）→ 用 `git reset --hard origin/main` 回退后另起提交
- 50jingsai 抓取中间文件 `_tmp_*` 一度被 commit 进仓库 → `git rm --cached` + `.gitignore` 补 `_tmp_*`
