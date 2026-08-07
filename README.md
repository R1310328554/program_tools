# StackBox

面向开发者的在线工具箱（参考 [BeJSON](https://www.bejson.com/) 与开源 DevToolbox 一类站点），用 **Django** 实现，**无数据库**。

## 功能概览

覆盖常见编程工具（40+），按分类组织：

- **JSON / 数据**：格式化、YAML/XML/CSV/TOML 互转、QueryString、代码生成、Diff、SQL INSERT、XML 格式化
- **编码加密**：Base64、URL、HTML 实体、Unicode、Hex、Hash、JWT、密码哈希
- **转换工具**：时间戳、进制、颜色、命名风格、字节单位、Cron
- **文本代码**：正则、SQL、Markdown、字数统计、转义、行处理、CSS/JS 压缩、Slugify
- **生成工具**：UUID、密码、Lorem、二维码、随机数、短 ID
- **网络运维**：IP/CIDR、User-Agent、JWT 时间声明
- **速查参考**：HTTP 状态码、MIME、常用 Header

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
