# StackBox

面向开发者的在线工具箱（参考 [BeJSON](https://www.bejson.com/) 与开源 DevToolbox 一类站点），用 **Django** 实现，**无数据库**。

## 功能概览

覆盖常见编程工具（70+，持续增长），按分类组织：

- **JSON / 数据**：格式化、YAML/XML/CSV/TOML/Properties 互转、JSONPath、Schema、代码生成、Diff、SQL INSERT
- **编码加密**：Base64/32/58、AES/RSA、HMAC、JWT 编解码验签、Gzip、摩斯/ROT13、Unicode 正规化
- **转换工具**：时间戳、进制、颜色、命名、chmod、docker run→compose、cURL→Python、Cron、罗马数字
- **文本代码**：正则、SQL、Markdown/HTML、.env、字数统计、转义、行处理、压缩、Slugify
- **生成工具**：UUID/ULID/NanoID、密码、TOTP、SSH 密钥、假数据、二维码
- **网络运维**：IP/CIDR、URL 解析、UA、PEM 证书、JWT 时间声明
- **速查参考**：HTTP 状态码、MIME、Header、正则速查

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 manage.py runserver 0.0.0.0:8000
```

打开 http://127.0.0.1:8000/

不需要 `migrate`，项目未配置持久化数据库。

## 架构

- `toolbox/registry.py`：工具目录（名称、分类、操作按钮）
- `toolbox/processors/`：各工具的 Python 实现
- `toolbox/views.py`：首页 / 工具页 / JSON API
- 前端通过 `POST /api/tools/<slug>/` 调用，CSRF Cookie 校验

## 说明

多数工具在服务端即时计算，不落库、不保存用户输入。二维码等以 Base64 图片返回；Markdown 在页面内渲染 HTML 预览。

## 定时扫描（不断完善）

| 任务 | 时间（上海） | 命令 / 工作流 |
|------|--------------|---------------|
| 每晚轻量扫描 | 每天 01:00 | `nightly-tool-scan.yml` |
| **每周全网扫描** | **周日 01:00** | `weekly-global-scan.yml`（国内+国外） |
| 每周集成提醒 | 周四 01:00 | `weekly-integrate-remind.yml` |

```bash
python scripts/weekly_global_scan.py          # 全网扫描（推荐）
python scripts/nightly_tool_scan.py --live-github
python scripts/integrate_candidates.py
```

- 源清单：`toolbox/discovery/sources_global.json`
- 文档：`docs/TIMERS.md`
