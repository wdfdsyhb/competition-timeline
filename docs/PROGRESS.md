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
