"""Central catalog of developer tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class Tool:
    slug: str
    name: str
    description: str
    category: str
    icon: str
    actions: tuple[str, ...] = ()
    template: str = 'toolbox/tool_generic.html'
    dual_input: bool = False
    dual_labels: tuple[str, str] = ('输入 A', '输入 B')
    placeholder: str = ''
    placeholder_b: str = ''
    options: tuple[dict, ...] = ()
    tags: tuple[str, ...] = ()


CATEGORIES = [
    ('json', 'JSON / 数据'),
    ('encode', '编码加密'),
    ('convert', '转换工具'),
    ('text', '文本代码'),
    ('generate', '生成工具'),
    ('network', '网络运维'),
    ('reference', '速查参考'),
]


TOOLS: list[Tool] = [
    # JSON / Data
    Tool(
        slug='json-format',
        name='JSON 格式化',
        description='校验、美化、压缩 JSON，支持 Unicode 转义与排序键。',
        category='json',
        icon='{}',
        actions=('format', 'minify', 'validate', 'sort'),
        placeholder='{"name":"StackBox","ok":true}',
        tags=('json', '格式化', '校验'),
    ),
    Tool(
        slug='json-yaml',
        name='JSON ↔ YAML',
        description='JSON 与 YAML 双向转换，适合配置文件与 DevOps。',
        category='json',
        icon='Y',
        actions=('to_yaml', 'to_json'),
        placeholder='{"env":"prod","replicas":3}',
        tags=('yaml', '配置'),
    ),
    Tool(
        slug='json-xml',
        name='JSON ↔ XML',
        description='JSON 与 XML 互相转换。',
        category='json',
        icon='X',
        actions=('to_xml', 'to_json'),
        placeholder='{"user":{"id":1,"name":"Ada"}}',
        tags=('xml',),
    ),
    Tool(
        slug='json-csv',
        name='JSON ↔ CSV',
        description='对象数组与 CSV 表格互转。',
        category='json',
        icon='C',
        actions=('to_csv', 'to_json'),
        placeholder='[{"id":1,"name":"Ada"},{"id":2,"name":"Grace"}]',
        tags=('csv', '表格'),
    ),
    Tool(
        slug='json-query',
        name='JSON ↔ QueryString',
        description='JSON 对象与 URL 查询参数互转。',
        category='json',
        icon='?',
        actions=('to_query', 'to_json'),
        placeholder='{"page":1,"q":"django"}',
        tags=('get', 'query'),
    ),
    Tool(
        slug='json-codegen',
        name='JSON 转代码',
        description='从 JSON 生成 Python / Go / TypeScript / Java / C# 类型定义。',
        category='json',
        icon='</>',
        actions=('python', 'go', 'typescript', 'java', 'csharp'),
        placeholder='{"id":1,"name":"Ada","tags":["dev"],"active":true}',
        options=(
            {'key': 'root_name', 'label': '根类型名', 'default': 'Root', 'type': 'text'},
        ),
        tags=('代码生成', '实体类'),
    ),
    Tool(
        slug='json-diff',
        name='JSON / 文本 Diff',
        description='对比两段文本或 JSON 的差异。',
        category='json',
        icon='±',
        actions=('diff',),
        dual_input=True,
        dual_labels=('左侧原文', '右侧对比'),
        placeholder='{"a":1,"b":2}',
        placeholder_b='{"a":1,"b":3,"c":4}',
        tags=('diff', '对比'),
    ),
    Tool(
        slug='toml-json',
        name='TOML ↔ JSON',
        description='TOML 与 JSON 互转（基于简易解析，适合常见配置）。',
        category='json',
        icon='T',
        actions=('to_json', 'to_toml'),
        placeholder='title = "StackBox"\n[server]\nport = 8000',
        tags=('toml',),
    ),
    Tool(
        slug='json-sql',
        name='JSON → SQL INSERT',
        description='把对象数组转成 SQL INSERT 语句。',
        category='json',
        icon='SQL',
        actions=('insert',),
        placeholder='[{"id":1,"name":"Ada"},{"id":2,"name":"Grace"}]',
        options=(
            {'key': 'table', 'label': '表名', 'default': 'users', 'type': 'text'},
        ),
        tags=('sql', 'insert'),
    ),
    Tool(
        slug='xml-format',
        name='XML 格式化',
        description='美化或压缩 XML。',
        category='json',
        icon='XML',
        actions=('format', 'minify'),
        placeholder='<root><user id="1"><name>Ada</name></user></root>',
        tags=('xml', '格式化'),
    ),

    # Encode / Crypto
    Tool(
        slug='base64',
        name='Base64 编解码',
        description='文本 Base64 编码与解码，支持 URL-safe 变体。',
        category='encode',
        icon='64',
        actions=('encode', 'decode', 'url_encode', 'url_decode'),
        placeholder='Hello, StackBox!',
        tags=('base64',),
    ),
    Tool(
        slug='url-codec',
        name='URL 编解码',
        description='URL / 百分号编码与解码。',
        category='encode',
        icon='%',
        actions=('encode', 'decode', 'encode_component', 'decode_component'),
        placeholder='https://example.com/搜索?q=django tools',
        tags=('url', '编码'),
    ),
    Tool(
        slug='html-entities',
        name='HTML 实体编解码',
        description='HTML 特殊字符实体编码与解码。',
        category='encode',
        icon='&',
        actions=('encode', 'decode'),
        placeholder='<div class="box">Hello & "world"</div>',
        tags=('html', '实体'),
    ),
    Tool(
        slug='unicode',
        name='Unicode 中文互转',
        description='中文与 \\uXXXX Unicode 转义互转。',
        category='encode',
        icon='U',
        actions=('to_unicode', 'to_chinese', 'escape', 'unescape'),
        placeholder='你好，世界',
        tags=('unicode', '中文'),
    ),
    Tool(
        slug='hex',
        name='Hex 编解码',
        description='文本与十六进制互转。',
        category='encode',
        icon='0x',
        actions=('encode', 'decode'),
        placeholder='StackBox',
        tags=('hex', '十六进制'),
    ),
    Tool(
        slug='hash',
        name='哈希生成',
        description='MD5 / SHA1 / SHA256 / SHA384 / SHA512 摘要。',
        category='encode',
        icon='#',
        actions=('hash',),
        placeholder='password123',
        options=(
            {
                'key': 'algo',
                'label': '算法',
                'type': 'select',
                'default': 'all',
                'choices': [
                    ('all', '全部'),
                    ('md5', 'MD5'),
                    ('sha1', 'SHA1'),
                    ('sha256', 'SHA256'),
                    ('sha384', 'SHA384'),
                    ('sha512', 'SHA512'),
                ],
            },
        ),
        tags=('md5', 'sha', '摘要'),
    ),
    Tool(
        slug='jwt',
        name='JWT 解码',
        description='解析 JWT Header / Payload（不验签，仅查看）。',
        category='encode',
        icon='JWT',
        actions=('decode',),
        placeholder='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c',
        tags=('jwt', 'token'),
    ),
    Tool(
        slug='password-hash',
        name='密码哈希 (bcrypt 风格说明)',
        description='生成 PBKDF2 / SHA 加盐哈希（演示用途）。',
        category='encode',
        icon='*',
        actions=('pbkdf2', 'sha256_salt'),
        placeholder='my-secret-password',
        tags=('password', 'salt'),
    ),

    # Convert
    Tool(
        slug='timestamp',
        name='Unix 时间戳',
        description='时间戳与可读时间互转，支持秒/毫秒。',
        category='convert',
        icon='⏱',
        actions=('now', 'to_datetime', 'to_timestamp'),
        placeholder='1710000000',
        options=(
            {
                'key': 'unit',
                'label': '单位',
                'type': 'select',
                'default': 'auto',
                'choices': [('auto', '自动'), ('s', '秒'), ('ms', '毫秒')],
            },
        ),
        tags=('时间戳', 'unix'),
    ),
    Tool(
        slug='number-base',
        name='进制转换',
        description='二进制 / 八进制 / 十进制 / 十六进制互转。',
        category='convert',
        icon='2↔16',
        actions=('convert',),
        placeholder='255',
        options=(
            {
                'key': 'from_base',
                'label': '输入进制',
                'type': 'select',
                'default': '10',
                'choices': [('2', '2'), ('8', '8'), ('10', '10'), ('16', '16')],
            },
        ),
        tags=('进制', 'binary'),
    ),
    Tool(
        slug='color',
        name='颜色转换',
        description='HEX / RGB / HSL 颜色互转。',
        category='convert',
        icon='◎',
        actions=('convert',),
        placeholder='#0F766E',
        tags=('color', 'hex', 'rgb'),
    ),
    Tool(
        slug='case',
        name='命名风格转换',
        description='camelCase / snake_case / kebab-case / PascalCase 等互转。',
        category='convert',
        icon='Aa',
        actions=(
            'snake', 'camel', 'pascal', 'kebab', 'constant', 'title', 'upper', 'lower',
        ),
        placeholder='helloWorldExample',
        tags=('命名', 'case'),
    ),
    Tool(
        slug='bytes-size',
        name='字节单位换算',
        description='B / KB / MB / GB / TB 换算。',
        category='convert',
        icon='B',
        actions=('convert',),
        placeholder='1048576',
        options=(
            {
                'key': 'unit',
                'label': '输入单位',
                'type': 'select',
                'default': 'B',
                'choices': [('B', 'B'), ('KB', 'KB'), ('MB', 'MB'), ('GB', 'GB'), ('TB', 'TB')],
            },
        ),
        tags=('字节', 'size'),
    ),
    Tool(
        slug='cron',
        name='Cron 表达式解析',
        description='解析 Cron 表达式并给出接下来的运行时间。',
        category='convert',
        icon='CR',
        actions=('parse',),
        placeholder='*/5 * * * *',
        tags=('cron', '定时'),
    ),

    # Text / Code
    Tool(
        slug='regex',
        name='正则测试',
        description='测试正则表达式匹配、分组与替换。',
        category='text',
        icon='.*',
        actions=('match', 'findall', 'replace'),
        dual_input=True,
        dual_labels=('正则表达式', '测试文本'),
        placeholder=r'(\w+)@(\w+\.\w+)',
        placeholder_b='contact ada@example.com or grace@lab.org',
        options=(
            {'key': 'flags', 'label': '标志 (i/m/s/x)', 'default': 'i', 'type': 'text'},
            {'key': 'repl', 'label': '替换为', 'default': '[$1]', 'type': 'text'},
        ),
        tags=('regex', '正则'),
    ),
    Tool(
        slug='sql-format',
        name='SQL 格式化',
        description='美化 / 压缩 SQL 语句。',
        category='text',
        icon='SQL',
        actions=('format', 'minify'),
        placeholder='select id,name from users where active=1 order by id desc',
        tags=('sql',),
    ),
    Tool(
        slug='markdown',
        name='Markdown 预览',
        description='将 Markdown 渲染为 HTML 预览。',
        category='text',
        icon='MD',
        actions=('render',),
        placeholder='# Hello\n\n- item 1\n- **bold**\n\n`code`',
        tags=('markdown',),
    ),
    Tool(
        slug='text-stats',
        name='字数统计',
        description='统计字符、单词、行数、字节与中文字数。',
        category='text',
        icon='∑',
        actions=('stats',),
        placeholder='在这里粘贴文本……',
        tags=('统计', '字数'),
    ),
    Tool(
        slug='escape',
        name='转义 / 反转义',
        description='JSON / Python / C 风格字符串转义。',
        category='text',
        icon='\\',
        actions=('json_escape', 'json_unescape', 'python_escape', 'python_unescape'),
        placeholder='line1\nline2\t"quoted"',
        tags=('escape', '转义'),
    ),
    Tool(
        slug='line-tools',
        name='行处理工具',
        description='去重、排序、去空行、加序号、反转行序。',
        category='text',
        icon='≡',
        actions=('unique', 'sort', 'sort_desc', 'trim_empty', 'number', 'reverse'),
        placeholder='banana\napple\napple\ncherry\n',
        tags=('行', '去重', '排序'),
    ),
    Tool(
        slug='css-js-minify',
        name='CSS / JS 压缩',
        description='简易压缩 CSS 与 JavaScript（去注释与空白）。',
        category='text',
        icon='{}',
        actions=('css', 'js'),
        placeholder='/* comment */\n.box {\n  color: #0f766e;\n  margin: 0;\n}',
        tags=('minify', 'css', 'js'),
    ),
    Tool(
        slug='slugify',
        name='Slugify / 路径化',
        description='把标题转成 URL 友好 slug（支持中文转拼音近似：保留可读片段）。',
        category='text',
        icon='/',
        actions=('slugify', 'filename'),
        placeholder='Hello StackBox 开发者工具',
        tags=('slug', 'url'),
    ),

    # Generate
    Tool(
        slug='uuid',
        name='UUID 生成',
        description='批量生成 UUID v4。',
        category='generate',
        icon='ID',
        actions=('generate',),
        placeholder='数量（默认 5）',
        options=(
            {'key': 'count', 'label': '数量', 'default': '5', 'type': 'text'},
            {
                'key': 'upper',
                'label': '大写',
                'type': 'select',
                'default': '0',
                'choices': [('0', '否'), ('1', '是')],
            },
        ),
        tags=('uuid', 'guid'),
    ),
    Tool(
        slug='password',
        name='密码生成',
        description='生成高强度随机密码。',
        category='generate',
        icon='*',
        actions=('generate',),
        placeholder='长度（默认 16）',
        options=(
            {'key': 'length', 'label': '长度', 'default': '16', 'type': 'text'},
            {
                'key': 'symbols',
                'label': '含符号',
                'type': 'select',
                'default': '1',
                'choices': [('1', '是'), ('0', '否')],
            },
            {'key': 'count', 'label': '数量', 'default': '5', 'type': 'text'},
        ),
        tags=('password', '随机'),
    ),
    Tool(
        slug='lorem',
        name='Lorem Ipsum',
        description='生成占位假文。',
        category='generate',
        icon='L',
        actions=('paragraphs', 'sentences', 'words'),
        placeholder='段落数（默认 3）',
        options=(
            {'key': 'count', 'label': '数量', 'default': '3', 'type': 'text'},
        ),
        tags=('lorem', '假文'),
    ),
    Tool(
        slug='qrcode',
        name='二维码生成',
        description='将文本生成 PNG 二维码（Base64 展示）。',
        category='generate',
        icon='▣',
        actions=('generate',),
        placeholder='https://example.com',
        tags=('qr', '二维码'),
    ),
    Tool(
        slug='random',
        name='随机数 / 字符串',
        description='生成随机整数、十六进制串、Token。',
        category='generate',
        icon='?',
        actions=('int', 'hex', 'token'),
        placeholder='1-100',
        options=(
            {'key': 'count', 'label': '数量', 'default': '5', 'type': 'text'},
        ),
        tags=('random', 'token'),
    ),
    Tool(
        slug='hashids-like',
        name='短 ID 生成',
        description='基于数字生成可读短码（可逆演示）。',
        category='generate',
        icon='ID',
        actions=('encode', 'decode'),
        placeholder='123456',
        tags=('短链', 'id'),
    ),

    # Network
    Tool(
        slug='ip-cidr',
        name='IP / CIDR 计算',
        description='解析 IPv4 地址与 CIDR 网段信息。',
        category='network',
        icon='IP',
        actions=('parse',),
        placeholder='192.168.1.10/24',
        tags=('ip', 'cidr', '子网'),
    ),
    Tool(
        slug='user-agent',
        name='User-Agent 解析',
        description='粗解析常见 UA 字符串中的浏览器与系统信息。',
        category='network',
        icon='UA',
        actions=('parse',),
        placeholder='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        tags=('ua', '浏览器'),
    ),
    Tool(
        slug='jwt-claims-time',
        name='JWT 时间声明',
        description='把 JWT 的 iat/exp/nbf 等时间字段可读化（粘贴完整 JWT 或 payload JSON）。',
        category='network',
        icon='⏱',
        actions=('explain',),
        placeholder='{"iat":1516239022,"exp":1710000000,"nbf":1516239022}',
        tags=('jwt', 'exp'),
    ),

    # Reference
    Tool(
        slug='http-status',
        name='HTTP 状态码',
        description='常见 HTTP 状态码速查。',
        category='reference',
        icon='HTTP',
        actions=('lookup', 'list'),
        placeholder='404',
        template='toolbox/tool_reference.html',
        tags=('http', '状态码'),
    ),
    Tool(
        slug='mime-types',
        name='MIME 类型速查',
        description='常见文件扩展名与 MIME Type 对照。',
        category='reference',
        icon='MIME',
        actions=('lookup', 'list'),
        placeholder='json',
        template='toolbox/tool_reference.html',
        tags=('mime', 'content-type'),
    ),
    Tool(
        slug='content-headers',
        name='常用 HTTP 头',
        description='开发中常见请求/响应头说明。',
        category='reference',
        icon='HDR',
        actions=('list',),
        placeholder='',
        template='toolbox/tool_reference.html',
        tags=('header',),
    ),
]


_TOOL_MAP = {t.slug: t for t in TOOLS}


def get_tool(slug: str) -> Tool | None:
    return _TOOL_MAP.get(slug)


def tools_by_category() -> list[tuple[str, str, list[Tool]]]:
    result = []
    for key, label in CATEGORIES:
        items = [t for t in TOOLS if t.category == key]
        if items:
            result.append((key, label, items))
    return result


def search_tools(query: str) -> list[Tool]:
    q = query.strip().lower()
    if not q:
        return list(TOOLS)
    out = []
    for t in TOOLS:
        blob = ' '.join([t.name, t.description, t.slug, *t.tags]).lower()
        if q in blob:
            out.append(t)
    return out
