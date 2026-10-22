# 大学生竞赛时间/日程整合 — GitHub 现成项目调研

- 调研时间：2026-10-22（Asia/Shanghai）
- 检索方式：GitHub Search API（`Invoke-RestMethod` + `User-Agent` + `Accept: application/vnd.github+json`），仓库搜索 `sort=stars&order=desc&per_page=15`
- 未做任何 clone / 安装，全程只读 API
- 关键词 22 组，去重后命中 212 个仓库，全部逐条判定

## 0. 检索记录（可复核）

仓库搜索 `q=` 与返回的 `total_count`：

| 关键词 | total_count | 关键词 | total_count |
|---|---|---|---|
| 竞赛 日历 | 13 | competition calendar | 123 |
| 竞赛 时间表 | **0** | contest calendar | 362 |
| 竞赛 报名 | 89 | hackathon calendar | 360 |
| 学科竞赛 | 407 | competition tracker | 2381 |
| 大学生竞赛 | 1240 | contest reminder | 271 |
| 竞赛 提醒 | 15 | olympiad schedule | 26 |
| 赛事日历 | 38 | contest timeline | 23 |
| 竞赛信息聚合 | 27 | competition deadlines | 99 |
| 竞赛日程 | 32 | 赛事聚合 | 39 |
| 竞赛报名时间 | 17 | 比赛日历 | 31 |
| 竞赛 管理系统 | 364 | 高校竞赛 | 199 |

- `竞赛 时间表` 返回 0：**本轮关键词未命中**任何仓库。
- code search（找 `competitions.json` / `contests.yml` 数据文件）**未能执行**：GitHub code search API 未认证返回 `401`（两次尝试均为 `CODE-SEARCH-STATUS=401`）。该 API 强制要求登录令牌，本机无令牌，故「数据文件线索」这条路线**本轮未覆盖**，结论中不含此来源的证据。
- TurboRace 单独核查（`/repos/jiaoaodeshaonian1/TurboRace`）：stars 71、forks 24、created 2021-11-13、pushed 2026-02-28、updated 2026-10-08、language JavaScript、license 无、无 topics、archived false。

## 1. 命中（做的事就是「竞赛信息聚合 / 时间表 / 截止日历」）

### 1.1 编程/算法竞赛赛道（形态完全命中，但只覆盖 OJ 类赛事）

- **aropan/clist** · ★439 · 2026-10-22 · Python
  一句话：全球编程竞赛指南，跟踪赛事并给详情，配 clist.by 服务。
  判定理由：纯信息聚合 + 赛事跟踪，明确是「赛事时间表」形态；范围是全球 OJ/CP 赛事，不含中国大学生学科竞赛。
  https://github.com/aropan/clist
- **iphysresearch/DataSciComp** · ★1675 · 2026-10-09 · JavaScript
  一句话：热门数据科学竞赛合集，带动截止时间倒计时。
  判定理由：聚合 + 倒计时，命中；只覆盖 DS/Kaggle 类竞赛。
  https://github.com/iphysresearch/DataSciComp
- **LogicJake/MLCompetitionHub** · ★132 · 2026-10-14 · Python
  一句话：机器学习竞赛信息聚合。
  判定理由：自述即为「competition information aggregation」，命中；只覆盖 ML 竞赛。
  https://github.com/LogicJake/MLCompetitionHub
- **ProbiusOfficial/Hello-CTFtime** · ★179 · 2026-10-22 · Python
  一句话：国内外 CTF 赛事聚合。
  判定理由：聚合国内外赛事，命中；赛道仅 CTF。
  https://github.com/ProbiusOfficial/Hello-CTFtime
- **xcpcio/docs** · ★67 · 2026-07-23 · HTML
  一句话：*CPC 系列竞赛的信息聚合站。
  判定理由：明确的信息聚合站，命中；仅 XCPC 系列。
  https://github.com/xcpcio/docs
- **b8l8u8e8/OnlineContestFetcher** · ★2 · 2026-10-22 · Python
  一句话：聚合算法竞赛信息，自动检索各平台比赛时间与报名信息，统一格式并支持导出/订阅日历，另托管静态展示站。
  判定理由：本轮**形态最接近**的一个（抓取 → 结构化 → 日历导出 → 静态站），命中；只覆盖算法竞赛平台。
  https://github.com/b8l8u8e8/OnlineContestFetcher
- **lin-honghui/data-competition-calendar** · ★17 · 2026-10-02 · 无语言标注
  一句话：国内外数据竞赛资讯整理。
  判定理由：资讯聚合，命中；范围仅数据竞赛。
  https://github.com/lin-honghui/data-competition-calendar
- **MaoMaoXia1238/cp-calendar** · ★0 · 2026-06-25 · 无语言标注
  一句话：竞赛日历网站，自动聚合洛谷、牛客、Codeforces、LeetCode、AtCoder 五大平台。
  判定理由：聚合 + 日历，命中；五平台均为编程竞赛。
  https://github.com/MaoMaoXia1238/cp-calendar
- **hhduskhh/cn-contest-radar** · ★1 · 2026-09-19 · Python
  一句话：国内计算机 / AI 赛事信息聚合，每周定时爬取，核心产出是历年赛事时间线。
  判定理由：「历年赛事时间线」正是时间表形态，命中；限于计算机/AI 赛事。
  https://github.com/hhduskhh/cn-contest-radar
- **hust-open-atom-club/open-source-deadlines** · ★80 · 2026-10-14 · TypeScript
  一句话：开源活动、会议和竞赛的截止时间展示网站。
  判定理由：聚合 + 截止时间展示，命中；生态是开源社区活动，不是学科竞赛。
  https://github.com/hust-open-atom-club/open-source-deadlines
- **chaitanya21kumar/contestpulse** · ★16 · 2026-03-15 · JavaScript
  一句话：自动化的编程竞赛跟踪器，带智能提醒和统一 dashboard。
  判定理由：跟踪 + 提醒 + 看板三件套齐全，命中；仅 CP 赛事。
  https://github.com/chaitanya21kumar/contestpulse
- **karanarjunjr/cp-calendar** · ★24 · 2025-07-13 · JavaScript
  一句话：编程竞赛日历网站（Never Miss a Coding Contest Again）。
  判定理由：日历 + 提醒，命中；仅 CP。
  https://github.com/karanarjunjr/cp-calendar
- **sahej-dev/Snow** · ★33 · 2026-08-03 · Dart
  一句话：面向程序员的编程竞赛提醒 App，支持 10+ 平台（Codeforces、AtCoder 等），自述 1000+ 下载。
  判定理由：提醒形态命中、且是成熟度较高的一端；仅 CP 平台。
  https://github.com/sahej-dev/Snow
- **nisarg0/Kontest-Reminder** · ★33 · 2025-08-09 · JavaScript
  一句话：跨浏览器扩展，用于设置、记忆、查看编程竞赛日程。
  判定理由：提醒 + 日程，命中；仅 CP。
  https://github.com/nisarg0/Kontest-Reminder
- **Gowee/lccal-worker** · ★27 · 2025-07-24 · TypeScript
  一句话：Cloudflare Workers 上自动生成的 LeetCode 竞赛 iCal/ICS 日历。
  判定理由：**ICS 导出**命中；单一来源（LeetCode）。
  https://github.com/Gowee/lccal-worker
- **7oSkaaa/CP-Calendar** · ★17 · 2025-06-28 · Python
  一句话：脚本，把站点所有比赛加进 Google Calendar。
  判定理由：ICS/日历集成命中；仅 CP。
  https://github.com/7oSkaaa/CP-Calendar
- **Tanish2000/cpcalendar** · ★17 · 2026-04-15 · 无语言标注
  一句话：覆盖各编程平台即将开始比赛的日历。
  判定理由：日历形态命中；仅 CP。
  https://github.com/Tanish2000/cpcalendar
- **mqnu00/ACM-contest-calender-maker** · ★6 · 2026-10-22 · Python
  一句话：用 Python icalendar 库爬取竞赛时间，生成可订阅日历。
  判定理由：爬取 + ICS 生成命中；仅 ACM/CP。
  https://github.com/mqnu00/ACM-contest-calender-maker
- **InzamZ/Contest2Cal** · ★0 · 2023-02-14 · Python
  一句话：把近期 OI/ACM 竞赛添加到日历。
  判定理由：ICS 订阅命中；仅 OI/ACM。
  https://github.com/InzamZ/Contest2Cal
- **nxy1999/cs-calendar** · ★4 · 2026-10-19 · JavaScript
  一句话：CS 赛事日历，ICS 格式，供 iPhone / Google Calendar / Outlook 订阅。
  判定理由：ICS 导出命中；只覆盖 CS 电竞赛事。
  https://github.com/nxy1999/cs-calendar
- **sdufeACM/ContestWatchman** · ★2 · 2024-05-21 · Rust
  一句话：通过邮箱、RSS、日历订阅通知算法竞赛信息。
  判定理由：多通道提醒命中；仅算法竞赛。
  https://github.com/sdufeACM/ContestWatchman
- **其余同形态的 CP 提醒/日历小项目**（均命中同一形态、体量与覆盖面更小）：`aryanc403/remind` ★52（Discord 提醒 bot）、`omkhalane/eventio` ★7（聚合编程竞赛/黑客松/招聘到一个日历）、`AokabiC/compro-reminder` ★6、`BigOrangeQWQ/nonebot_plugin_acm_reminder` ★6、`ILoveScratch2/Luogu-Contest-Reminder` ★5、`OussamaBenSlama/CF-Notifier` ★13、`prit29/Coders-Calendar` ★8、`azaky/cpbot` ★10、`previouslyanywhere/CodeCalendar` ★5、`DuckyLing-IO/ContestPulse` ★0、`LogicShao/fanta5y-bot` ★2、`Lanly109/CodingReminder` ★18、`demon-Sheriff/ContestBot` ★5、`akshitdesai/ContestReminder` ★8、`Khushikantaria310/bumblebee` ★6、`jeroen-*` 类单平台项目等。

### 1.2 面向中国大学生的竞赛/校园信息聚合（最贴近用户需求的一类）

- **shinji00222/gdut-opportunity-watcher** · ★9 · 2026-10-21 · Python
  一句话：广东工业大学竞赛、实习与出国项目信息提醒工具。
  判定理由：面向大学生的竞赛信息提醒，命中；单一学校、非全国赛事库。
  https://github.com/shinji00222/gdut-opportunity-watcher
- **porridgeowefish/lizhi** · ★3 · 2026-10-18 · Python
  一句话：深圳大学校园机会聚合与搜索，从微信公众号筛出活动、讲座、竞赛、志愿、招募信息并按截止时间排序。
  判定理由：聚合 + 按 DDL 排序，命中；单校 + 依赖公众号抓取。
  https://github.com/porridgeowefish/lizhi
- **sukeleE/Engineer-Compass** · ★2 · 2026-10-18 · JavaScript
  一句话：工科竞赛导航 Web 应用，交互式竞赛时间轴 + AI 问答 + 智能备赛日程规划（Vue3 + Node + SQLite + DeepSeek AI）。
  判定理由：**唯一明确以「工科竞赛」泛类为主体、且做交互式时间轴的项目**，命中；star 极少，竞赛库规模未知。
  https://github.com/sukeleE/Engineer-Compass
- **kelin-gpu/campus-competition-agent** · ★1 · 2026-08-21 · Python
  一句话：面向本校学生的竞赛与校园活动 AI 助手，聚合校外竞赛、校内通知与五育活动，支持结构化检索、个性化推荐、DDL 提醒和保研/综测适配。
  判定理由：聚合 + DDL 提醒 + 保研/综测适配，需求吻合度最高之一，命中；单校、AI 助手形态、star 仅 1。
  https://github.com/kelin-gpu/campus-competition-agent
- **nadiriyesteinmeier-cell/fzu-competition-radar** · ★0 · 2026-10-22 · JavaScript
  一句话：福大竞赛雷达，汇总公开竞赛通知，结构化报名/作品截止/结果时间，支持筛选和一键加入日历。
  判定理由：聚合 + 时间节点结构化 + 一键加日历，需求吻合度高，命中；单校、规模极小。
  https://github.com/nadiriyesteinmeier-cell/fzu-competition-radar
- **CoirRaincoat/DailyNBU** · ★0 · 2026-09-20 · Python
  一句话：宁波大学校园通知聚合、竞赛考试日历与个人提醒桌面应用（Python/PySide6）。
  判定理由：竞赛日历 + 提醒，命中；单校桌面应用。
  https://github.com/CoirRaincoat/DailyNBU
- **ajydxw/sanjiang-radar** · ★0 · 2026-10-16 · JavaScript
  一句话：三江雷达，面向大一新生的校园通知、PU 活动、竞赛考试与日历提醒工具。
  判定理由：竞赛考试 + 日历提醒，命中；单校、面向新生。
  https://github.com/ajydxw/sanjiang-radar
- **weijing321/exam-competition-calendar** · ★0 · 2026-06-10 · TypeScript
  一句话：考赛日历，考试与竞赛信息管理平台。
  判定理由：竞赛日历形态命中；体量极小、无说明细节。
  https://github.com/weijing321/exam-competition-calendar
- **KrisDen2005/Contest** · ★1 · 2025-10-19 · 无语言标注
  一句话：自述「大学生竞赛日历 给迷茫的大学生开启比赛生涯 全程免费 直接开源」。
  判定理由：定位与用户需求一字不差，命中；但 star 1、无语言、无可评估的实现规模。
  https://github.com/KrisDen2005/Contest
- **Nemoyuzx/contest-ddl** · ★5 · 2026-10-02 · Python
  一句话：每日更新的工程竞赛、黑客松与夏令营截止时间雷达，输出 JSON。
  判定理由：DDL 雷达 + JSON 输出，命中；以工程竞赛/黑客松为主，非中国学科竞赛名录。
  https://github.com/Nemoyuzx/contest-ddl
- **Thedan-1/Dragonfly-Pulse** · ★5 · 2026-08-15 · Python
  一句话：开源校园科技竞赛雷达，聚合官方竞赛信息。
  判定理由：校园竞赛信息聚合，命中；非中文语境、规模小。
  https://github.com/Thedan-1/Dragonfly-Pulse
- **MRSHDER/cucn-contests** · ★0 · 2026-10-22 · TypeScript
  一句话：赛事簿 · 设计艺术赛事工作台，按学校竞赛目录整理设计艺术赛事，支持筛选、对比、截止日历与官方来源核验。
  判定理由：竞赛目录 + 截止日历 + 来源核验，形态命中；限定设计艺术类。
  https://github.com/MRSHDER/cucn-contests
- **HairuoLiu/photo-contest-calendar** · ★0 · 2026-09-28 · TypeScript
  一句话：全球摄影赛事日历，开源、无后端、免登录的摄影比赛截止提醒工具。
  判定理由：截止提醒 + 无后端，形态命中，可作为「无后端 ICS 站」的实现参考；限定摄影。
  https://github.com/HairuoLiu/photo-contest-calendar

### 1.3 非学科竞赛，但「日历/ICS 导出」形态可直接复用参考

- `sportclimbing/ifsc-calendar` ★49 · 2026-10-20 · PHP — IFSC 攀岩 iCal 日历生成器
- `sfw185/BJJCal` ★4 · 2026-10-04 · Python — 巴西柔术比赛日历 + ICS feed
- `zx123yyds/01_football` ★22 · 2026-08-15 · HTML — 2026 世界杯赛程 + 一键订阅 ICS
- `Dunky-Z/cycling-races-calender` ★3 · 2026-07-05 · Python — 公路车世巡赛 ICS 生成
- `syzry/c.t.f_ical` ★2 · 2026-10-22 · Python — 基于 Hello-CTFtime 的自用 CTF 赛事订阅日历
- `probablyalexzhu/DebateComps` ★4 · 2026-06-03 · TypeScript — 全球辩论赛日历
- `lisongxuan/Snooker-Calendar` ★3 · 2026-09-04 · Python — 斯诺克赛程日历

判定理由：这些都不解决「大学生学科竞赛时间」，但 ICS 生成/订阅这条工程路径可以直接借鉴。

## 2. 部分命中（做了竞赛信息的管理或展示，但不是「公开赛事时间节点聚合」）

### 2.1 校园/高校竞赛报名与管理系统（含用户特别要求核查的 TurboRace）

- **jiaoaodeshaonian1/TurboRace** · ★71 · 2026-10-08（push 2026-02-28）· JavaScript · 无 license
  一句话：大学校园竞赛小程序（JAVA 版），功能为竞赛项目展示、自主报名/取消报名、后台录入竞赛项目、按竞赛统计报名情况、导出名单、用户与管理员管理；详情页展示竞赛时间、地点、报名方式、参与要求、奖项设置。
  判定理由：**信息由管理员手工后台录入**，比赛数据来自本校自己发布的竞赛，没有对外部赛事时间表的抓取或聚合，也没有 ICS/日历导出；本质是「校内竞赛报名 + 报名统计导出」的管理系统。**不算命中**。另注：无 LICENSE、无 topics、2026-02 之后无 push，直接基于它做二次开发的许可与维护性都不明确。
  https://github.com/jiaoaodeshaonian1/TurboRace
- **emosheeep/competition-system** ★87 + **emosheeep/competition-server** ★22 · 2026-06-25 · Vue / TypeScript
  一句话：竞赛信息管理系统（Vue 前端 + Node/Express/Sequelize 后端），比赛记录与赛事信息增删改查、RBAC 权限。
  判定理由：管理系统式 CRUD，无赛事时间聚合与订阅，部分命中（可作为「赛事信息库 + 权限」的后端骨架）。
  https://github.com/emosheeep/competition-system
- **dormirr/galop-web** ★21 + **dormirr/galop-server** ★9 · 2025/2026 · JavaScript / Java
  一句话：学科竞赛训练管理系统，提供比赛报名、成绩录入、自由组队、水平分析。
  判定理由：训练/报名管理，非时间表，部分命中。
  https://github.com/dormirr/galop-web
- **Gao-Ge-Ryan/exam-registration-system** ★35 · 2026-10-20 · Java
  一句话：基于 Spring Boot + Vue 的可定制化报名系统，明示适用于考试/活动/竞赛/岗位报名，支持私有化部署。
  判定理由：是通用「报名」引擎，跟赛事时间聚合无关，部分命中（若后续要做报名入口可参考）。
  https://github.com/Gao-Ge-Ryan/exam-registration-system
- 同类的毕设/课程设计型「高校学科竞赛管理系统 / 报名系统」（均部分命中，判定理由同为「后台录入 + 报名统计，无公开赛事时间库、无日历订阅」）：`Descartes007/no060_UniversityDisciplineCompetitionPlatform` ★25、`JiuJiangFirstDeepLove/051-Springboot` ★27、`westzyan/register` ★28、`Micah-Jiang/collage-contest-manage-system` ★16、`RABITBABY/CompSystem` ★13、`BYFOR/competition-system-of-hbfu` ★12、`net936/python_bm` ★12、`net936/java_bm` ★11、`Chenzhanshang/competition_apply_system` ★15、`wzq-55552/dachuang` ★14、`yyyy960/research-competition-system` ★0、`metahy/itcompetition` ★5、`Gao-Ge-Ryan/*`、`coursehero/google-calendar-display` ★24（仅会议室状态）；另有 `swifuUI/PowerAss` ★36（校园社团活动小程序，同款报名统计逻辑）、`beijingxiaotanjiang/SmartSport` ★2（奥赛报名缴费小程序）。
  https://github.com/Descartes007/no060_UniversityDisciplineCompetitionPlatform
- **Science Olympiad 排程器一族**（把学生分配到赛事项目、生成优化赛程）：`KilometersFan/SciOlyScheduler` ★2、`raghav198/Scioly-Scheduler` ★2、`ssingh730/Science-Olympiad-Scheduler` ★0、`adityapatn/science-olympiad-event-scheduler` ★1、`PeterHall16/scheduler` ★1、`ASpacesys/science-olympiad-rostermaking-tool` ★0、`alvictor21/Olympiad-Admin` ★0、`noinsts/lyceum-3` ★0、`Mathew5555/The-Olympiad-schedule` ★0。
  判定理由：**组织方办赛的排程/名单工具**，不是「学生视角的赛事时间表」，部分命中。注意它与用户的「大学生竞赛」不是一回事（Science Olympiad 是美国中学生科学竞赛），关键词 `olympiad schedule` 主要通过这条线命中。
  https://github.com/KilometersFan/SciOlyScheduler
- **MOAzeemKhan/Unstop-Hackathon-Scraper** ★1 · 2023-01-10 · Python — 抓取生成 `competition.csv`（竞赛名/主办方等字段）。
  判定理由：抓取 + 结构化输出与需求方向一致，但单站点、无时间节点与日历，部分命中。
  https://github.com/MOAzeemKhan/Unstop-Hackathon-Scraper
- **keonzhu/competition-rag-customer-service** ★1 · 2026-09-10 · Python — 从竞赛规程 PDF 抽取赛项名称、赛道、发布时间、报名时间、组织单位、官网并输出结构化 Excel。
  判定理由：**「从规程 PDF 抽报名时间」这一步正好是国内赛事数据源的真实痛点**，值得参考但本身不是时间表产品，部分命中。
  https://github.com/keonzhu/competition-rag-customer-service
- **WorldtoFy/cxcy-monitor** ★0 · 2026-10-22 · Python — 辽宁省大学生创新创业竞赛监控：报名截止提醒 + 获奖公示推送（含附件下载）。
  判定理由：省级赛事 DDL 提醒，方向命中但仅辽宁大创一项，属部分命中。
  https://github.com/WorldtoFy/cxcy-monitor
- **StevenLin0732/Teammate-Reputation-System-TRS-** ★3 · 2026-02-25 · TypeScript — 学生竞赛组队信誉系统。
  判定理由：组队环节，不是时间表，部分命中。
  https://github.com/StevenLin0732/Teammate-Reputation-System-TRS-
- **wangluodandan/WeRace** ★5 · 2026-10-18 · JavaScript — 「挑战杯」参赛者信息填写/项目申报流程。
  判定理由：单一赛事的申报页，部分命中。
  https://github.com/wangluodandan/WeRace

**TurboRace 结论（按要求单独核查）**：它是**校园竞赛报名管理系统**，不是竞赛时间/日程聚合工具。若用户目标是「把各类大学生竞赛的时间节点整合在一起」，TurboRace 只能提供「单校内部竞赛的发布 + 报名 + 统计」能力，赛事数据靠管理员手工录入，没有全国/省级赛事名录，没有抓取，也没有 ICS。**明确排除出「命中」档。**

## 3. 不相关（关键词命中但不解决该问题，逐类排除）

- **数学建模模板 / 论文 LaTeX 模板 / 备赛资料** — 解决的是「怎么写参赛论文」，不是「什么时候报名」：
  `zhanwen/MathModel` ★12372、`personqianduixue/Math_Model` ★5291、`latexstudio/CUMCMThesis` ★1437、`Iamnotphage/CMC-SpeedRun` ★242、`zhaohaobingSUI/ZHB_project_diansai` ★227、`FredBill1/RT1064_Smartcar` ★194、`boatchanting/Wheel-legged-autocar` ★17、`CCBP/NUEDC_Topic` ★1012（历年赛题汇编）、`zhangkeo1111-gif/CHU-CV` ★11（简历模板，含"竞赛报名"字样）。
- **题解 / 刷题 / 训练工具** — 解决的是「怎么练」，不是「赛事时间」：
  `lillee1126/Algorithm` ★50、`Fantasy0504/Algorithm-Workbench` ★2、`Apricity1128/OI-Notes` ★0、`Iamnotphage/CMC-SpeedRun` ★242。
- **AI 数学建模 / 科研写作 Agent 与绘图 skill** — `N-allpass/modex-mh-agent` ★287、`hrdZhu/modelviz-skill` ★279。
- **Kaggle / 天池等竞赛的获奖方案与 baseline** — 赛后代码，不是赛事日程：
  `DLLXW/data-science-competition` ★1387、`liupengsay/DataScience` ★164、`librauee/myDataCompetition` ★141、`yiming-qing/Research-Agent-...-Competition` ★149、`XiangJinyu/Math-Multi-Agent` ★79、`flyingmarkk/OWM_CL` ★104、`pfnet-research/nips17-adversarial-attack` ★148、`otroshi/edgeface` ★186、`MCG-NJU/SportsMOT` ★233、`DrewNF/Tensorflow_Object_Tracking_Video` ★503、`yarongmu-google/MLSys` ★360、`hack-r/kaggle_telstra` ★2、`datascicamp/DataSciCamp` ★15（虽为 deadlines 站，但与 iphysresearch 同源且更旧，本轮不单列）。
- **单赛事/单一活动的 SDK、赛事官网代码、成绩系统**：
  `chrisneagu/FTC-Skystone-...` ★319、`skylines-project/skylines` ★407、`scottwillson/racing_on_rails` ★41、`sportclimbing/ifsc-calendar`（已列 1.3）、`FoliageOwO/QingJiaoHelper` ★49、`payMeQuiz/payMe-Project` ★14、`gaerae/facebook-contest-winner` ★13、`Lucas-Erkana/Capstone2-Project-Competition-page` ★10、`Vincen1994/-` ★1、`JigyasuRajput/GSoC-spy` ★85（追踪 GSoC PR 活跃度，不是赛事日历）。
- **体育/电竞/其他领域赛事数据与日历（已把可借鉴的 ICS 实现单列到 1.3）**：`suiiki888/football-ai-analysis` ★4、`abandroid/soccer-calendar-bundle` ★2、`xyzpuli4869/esports-calendar` ★0、`BTFAA/cs-reminder` ★0、`figure-skating-discord/ISUDiscordCalendar` ★3。
- **中文关键词噪声（README/描述是巨型文本转储，被"竞赛/赛事/日历"字样命中，与本主题无关）** — 这类占了本轮 212 条中的绝大多数：
  `fighting41love/funNLP` ★84071（词库合集）、`Dujltqzv/Some-Many-Books` ★25068（书籍 PDF 列表）、`cirosantilli/china-dictatorship` ★3285 及 `cirosantilli/china-dictatroship-7` ★376、`mRFWq7LwNPZjaVv5v6eo/cihna-dictattorshrip-8` ★211、`panbinibn/OpenPacketFix_` ★206、`zpc1314521/PCL2` ★131（均为政治宣传/备份类仓库）、`gege-circle/.github` ★2059、`pxvr-official/1` ★543、`Alvin9999/new-pac` / `jaityron/new-pac-wiki` ★84、`akiralereal/iptv` ★1442（赛事=直播频道）、`Descartes007/allProject` ★43、`nature924/allproject` ★112、`666bears/competition` ★36、`small-bears/knowledges` ★106（毕设大礼包类仓库，描述里堆满"竞赛管理系统"关键词）。
- **其他被关键词带出的无关项目**：`alfaarghya/alfa-leetcode-api` ★835（LeetCode 数据 API）、`ayush-sleeping/Every-Open-Source-Programs` ★420（开源项目清单）、`Frankcastleauditor/Solana-Audit-Arena` ★122、`coursehero/google-calendar-display` ★24、`ndd365/showup` ★34、`HannahMitt/SpaceCalendar` ★11、`DuckLing-IO/ContestPulse`（已列 1.1）、`lucky8197/dsh-devquest` ★8（工具无关）。

## 4. 结论

**没有找到「完全现成可用」的项目。** 22 组关键词 + 212 个去重仓库中，没有一个是「中国大学生各类学科竞赛（校赛/省赛/国赛）时间节点的统一聚合 + 提醒 + 日历导出」。现有项目全部落在两个错位方向上：

1. **赛事聚合/日历这一侧，覆盖的都是编程类平台赛事**（Codeforces / AtCoder / 牛客 / 洛谷 / LeetCode / CTF / Kaggle / 天池 / 黑客松），没有中国学科竞赛名录。代表：`aropan/clist` ★439、`ProbiusOfficial/Hello-CTFtime` ★179、`LogicJake/MLCompetitionHub` ★132、`xcpcio/docs` ★67，以及做 ICS 导出的 `Gowee/lccal-worker` ★27 / `mqnu00/ACM-contest-calender-maker` ★6。
2. **中国高校这一侧，只有单校、单赛事的工具**，且都是「后台录入 + 报名统计」的管理系统（典型即 TurboRace），不是时间表。代表：`jiaoaodeshaonian1/TurboRace` ★71、`emosheeep/competition-system` ★87、`dormirr/galop-web` ★21。

**最接近的 2-3 个，以及它们缺什么：**

- **`b8l8u8e8/OnlineContestFetcher`** · ★2 · Python — 形态最接近（自动抓取 → 统一格式 → 导出/订阅日历 → 托管静态站）。**缺**：只抓算法竞赛平台，没有中国学科竞赛数据源；star 2、无可评估的生态与文档。
- **`kelin-gpu/campus-competition-agent`** · ★1 · Python — 需求语义最接近（校外竞赛 + 校内通知聚合、结构化检索、DDL 提醒、保研/综测适配）。**缺**：单校范围、AI 助手形态而非「赛事库 + 日历」，star 1，没有全国赛事库。
- **`sukeleE/Engineer-Compass`** · ★2 · JavaScript — 主体定位最接近（工科竞赛导航 + 交互式竞赛时间轴 + 备赛日程规划，Vue3/Node/SQLite）。**缺**：赛事库规模与数据来源未经验证，star 2，未证明有 ICS 导出与持续更新机制。
- 次选参考：`nadiriyesteinmeier-cell/fzu-competition-radar`（★0，福大竞赛雷达：结构化报名/作品截止/结果时间 + 一键加日历，与目标功能对齐但有单校局限）、`HairuoLiu/photo-contest-calendar`（★0，无后端免登录的截止提醒站，架构可直接抄）、`hust-open-atom-club/open-source-deadlines`（★80，deadlines 展示站，前端与数据结构可复用）、`keonzhu/competition-rag-customer-service`（★1，从竞赛规程 PDF 抽"报名时间"字段，解决国内赛事数据源问题的一环）。

**综上：需要自己写，但不必从零写。** 合理的做法是自建「全国大学生学科竞赛时间库」（数据结构 = 赛事名 / 级别 / 主办方 / 报名开始·截止 / 校赛·省赛·国赛时间 / 官网 / 来源），数据源参考 `keonzhu/competition-rag-customer-service` 的“规程 PDF 抽取”思路 + 官方通知页抓取，前端/展示参考 `hust-open-atom-club/open-source-deadlines`，日历导出参考 `Gowee/lccal-worker` 或 `mqnu00/ACM-contest-calender-maker` 的 ICS 生成，提醒通道参考 `sdufeACM/ContestWatchman`（邮箱/RSS/日历三通道）。TurboRace 只适合作为「如果还要做校内报名管理」的取经对象，不适合作为时间聚合项目的基础。

## 附：本轮方法的置信度边界

- 只用了 GitHub 仓库搜索的 name/description/topics 索引，**无法验证任何项目的实际功能与数据完整性**（未读 README、未读代码、未运行）。
- code search 路线因缺令牌未执行（401），因此「是否存在 `competitions.json` / `contests.yml` / `.ics` 竞赛数据集」**本轮未查**，可能存在未被仓库搜索覆盖的纯数据仓库。
- `竞赛 时间表` 零命中；`竞赛 提醒`（15）、`竞赛 日历`（13）、`竞赛报名时间`（17）、`contest timeline`（23）、`olympiad schedule`（26）等低命中量关键词的覆盖面已接近穷尽。