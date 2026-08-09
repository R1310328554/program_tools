# 扫描与集成说明

> 完整定时器列表见 [`TIMERS.md`](./TIMERS.md)。

## 每晚扫描（01:00 上海）

```bash
python scripts/nightly_tool_scan.py --live-github
```

- 工作流：`.github/workflows/nightly-tool-scan.yml`
- 对照 `community_catalog.json` + GitHub topic
- 输出 `reports/tool-scan-*.md`、`candidates.json`

## 每周全网扫描（周日 01:00 上海）

```bash
python scripts/weekly_global_scan.py --create-issue
```

- 工作流：`.github/workflows/weekly-global-scan.yml`
- 覆盖国内（BeJSON / tool.lu / SOJSON / Gitee…）与国外（DevToys / CyberChef / GitHub topics…）
- README 挖掘 + 多查询 GitHub Search
- 按类别 / 地区输出 `reports/weekly-global-scan-*.md`

## Cursor Automation 提示词（每周）

```
你是 StackBox 维护代理。请：
1. 运行 python scripts/weekly_global_scan.py
2. 阅读 reports/weekly-global-scan-*.md 与 toolbox/discovery/weekly_candidates.json
3. 优先实现 priority=high，来源可为国内或国外开源工具的能力
4. 新工具必须：更新 registry + processors + 测试；无数据库；无付费 API
5. 提交推送并更新 PR
```
