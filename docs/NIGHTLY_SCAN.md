# 每晚工具扫描（01:00 Asia/Shanghai）

StackBox 通过自动化扫描开源社区 / 同类站点，持续发现可补充的开发者工具。

## 调度

| 方式 | 时间 | 说明 |
|------|------|------|
| GitHub Actions | 每天 **01:00（上海）** = `cron: '0 17 * * *'` UTC | `.github/workflows/nightly-tool-scan.yml` |
| 手动 | 任意 | `python scripts/nightly_tool_scan.py --live-github` |
| Cursor Automation | 建议同样设为每天 01:00 | 提示词见下方 |

## 扫描做什么

1. 读取 `toolbox/discovery/community_catalog.json`（BeJSON、DevToys、dev-utilities 等社区工具清单）
2. 与当前 `toolbox/registry.py` 对比，找出缺失工具
3. 可选请求 GitHub `developer-tools` 主题仓库脉搏
4. 写出：
   - `reports/tool-scan-YYYYMMDD.md`
   - `toolbox/discovery/candidates.json`
5. 在 Actions 中可自动开 Issue，并把结果提交回仓库

## 本地运行

```bash
pip install -r requirements.txt
python scripts/nightly_tool_scan.py --live-github
```

## Cursor Automation 建议提示词

若在 Cursor 中创建每日 01:00 的 Automation，可用：

```
你是 StackBox 维护代理。请：
1. 在仓库根目录运行 `python scripts/nightly_tool_scan.py --live-github`
2. 阅读生成的 reports/tool-scan-*.md 与 toolbox/discovery/candidates.json
3. 优先实现 priority=high 且适合「纯 Django、无数据库、即时处理」的工具
4. 每个新工具更新 registry + processors + 测试
5. 提交并推送，更新 PR 说明
不要引入数据库；不要实现依赖外部付费 API 的工具。
```

## 更新社区清单

发现新的优质工具站 / GitHub 仓库时，把来源和工具名追加到
`toolbox/discovery/community_catalog.json`。
