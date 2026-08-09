# StackBox 定时器

用 GitHub Actions（可选配合 Cursor Automation）持续扫描国内外开源社区，发现并集成工具。

## 定时任务一览

| 定时器 | 时间（上海） | Cron (UTC) | 工作流 | 作用 |
|--------|--------------|------------|--------|------|
| 每晚轻量扫描 | 每天 01:00 | `0 17 * * *` | `nightly-tool-scan.yml` | 对照本地清单 + GitHub topic，更新候选 |
| **每周全网扫描** | **周日 01:00** | `0 17 * * 6` | `weekly-global-scan.yml` | 扫描国内站 + 国际站/仓库，分类缺口报告 |
| 每周集成提醒 | 周四 01:00 | `0 17 * * 3` | `weekly-integrate-remind.yml` | 按候选清单开 Issue，推动补齐 |

## 每周全网扫描覆盖

### 国内
- BeJSON / SOJSON / tool.lu / JSON.cn / 开源中国工具 / CMD5
- Gitee 开发者工具探索
- GitHub 中文关键词：在线工具箱、开发者工具箱
- 开源仓库：Website-Tools、utils.fun 等

### 国外/国际
- DevToys、dev-utilities、dev-toolkit、CyberChef、spoold-tools
- GitHub topics：`developer-tools`、`online-tools`
- README 表格/列表自动抽取工具名

## 本地手动跑

```bash
# 每周全网扫描（推荐）
python scripts/weekly_global_scan.py

# 每晚轻量扫描
python scripts/nightly_tool_scan.py --live-github

# 查看待集成清单
python scripts/integrate_candidates.py
```

产物：
- `reports/weekly-global-scan-YYYYMMDD.md`
- `toolbox/discovery/weekly_candidates.json`
- `toolbox/discovery/candidates.json`

## Cursor Automation（可选）

已完成外部配置后，建议保留两个 Automation：

1. **周日 01:00** — 运行 `weekly_global_scan.py`，阅读报告，实现 `priority=high` 工具并提 PR  
2. **周四 01:00** — 运行 `integrate_candidates.py`，补齐 medium 缺口  

提示词模板见 `docs/NIGHTLY_SCAN.md`（把脚本名换成 weekly 即可）。

## 分类原则

新工具按下列类别归入首页：

- JSON / 数据
- 编码加密
- 转换工具
- 文本代码
- 生成工具
- 网络运维
- 速查参考
- 前端视觉
- 安全校验

只集成适合「纯 Django、无数据库、瞬时处理」的工具；依赖付费 API 或重客户端运行时的能力仅记录为候选。
