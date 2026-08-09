from __future__ import annotations

import json

from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from .processors import run_tool
from .registry import TOOLS, get_tool, search_tools, tools_by_category


@ensure_csrf_cookie
def home(request):
    q = request.GET.get('q', '').strip()
    tools = search_tools(q) if q else TOOLS
    grouped = []
    for key, label, items in tools_by_category():
        filtered = [t for t in items if t in tools]
        if filtered:
            grouped.append((key, label, filtered))
    return render(
        request,
        'toolbox/home.html',
        {
            'grouped': grouped,
            'query': q,
            'tool_count': len(TOOLS),
        },
    )


@ensure_csrf_cookie
def tool_page(request, slug: str):
    tool = get_tool(slug)
    if not tool:
        raise Http404('工具不存在')
    related = [t for t in TOOLS if t.category == tool.category and t.slug != tool.slug][:6]
    return render(
        request,
        tool.template,
        {
            'tool': tool,
            'related': related,
            'action_labels': _action_labels(tool.actions),
        },
    )


def _action_labels(actions: tuple[str, ...]) -> list[tuple[str, str]]:
    labels = {
        'format': '格式化',
        'minify': '压缩',
        'validate': '校验',
        'sort': '键排序',
        'to_yaml': '→ YAML',
        'to_json': '→ JSON',
        'to_xml': '→ XML',
        'to_csv': '→ CSV',
        'to_query': '→ Query',
        'to_toml': '→ TOML',
        'insert': '生成 INSERT',
        'slugify': 'Slugify',
        'filename': '文件名净化',
        'python': 'Python',
        'go': 'Go',
        'typescript': 'TypeScript',
        'java': 'Java',
        'csharp': 'C#',
        'diff': '对比',
        'encode': '编码',
        'decode': '解码',
        'url_encode': 'URL-Safe 编码',
        'url_decode': 'URL-Safe 解码',
        'encode_component': '组件编码',
        'decode_component': '组件解码',
        'to_unicode': '→ Unicode',
        'to_chinese': '→ 中文',
        'escape': '转义',
        'unescape': '反转义',
        'hash': '生成哈希',
        'pbkdf2': 'PBKDF2',
        'sha256_salt': 'SHA256+Salt',
        'now': '当前',
        'to_datetime': '时间戳→时间',
        'to_timestamp': '时间→时间戳',
        'convert': '转换',
        'snake': 'snake_case',
        'camel': 'camelCase',
        'pascal': 'PascalCase',
        'kebab': 'kebab-case',
        'constant': 'CONSTANT_CASE',
        'title': 'Title Case',
        'upper': 'UPPER',
        'lower': 'lower',
        'parse': '解析',
        'match': '匹配',
        'findall': '全部匹配',
        'replace': '替换',
        'render': '渲染预览',
        'stats': '统计',
        'json_escape': 'JSON 转义',
        'json_unescape': 'JSON 反转义',
        'python_escape': 'Python 转义',
        'python_unescape': 'Python 反转义',
        'unique': '去重',
        'sort_desc': '降序',
        'trim_empty': '去空行',
        'number': '加序号',
        'reverse': '反转',
        'css': '压缩 CSS',
        'js': '压缩 JS',
        'generate': '生成',
        'paragraphs': '段落',
        'sentences': '句子',
        'words': '单词',
        'int': '随机整数',
        'hex': '随机 Hex',
        'token': '随机 Token',
        'lookup': '查询',
        'list': '全部列表',
        'explain': '解析时间字段',
        'query': '查询',
        'sign': '签名/签发',
        'encrypt': '加密',
        'decrypt': '解密',
        'rot13': 'ROT13',
        'caesar': 'Caesar',
        'to_roman': '→ 罗马',
        'to_int': '→ 数字',
        'md_to_html': 'MD → HTML',
        'strip_html': '去 HTML 标签',
        'users': '用户 JSON',
        'emails': '邮箱列表',
        'names': '姓名列表',
        'uri': 'otpauth URI',
        'random_secret': '随机密钥',
        'compress': '压缩',
        'decompress': '解压',
        'to_properties': '→ Properties',
        'check': '检测/校验',
        'verify': '校验',
        'keygen': '生成密钥',
        'nfc': 'NFC',
        'nfd': 'NFD',
        'nfkc': 'NFKC',
        'nfkd': 'NFKD',
        'beautify': '美化',
        'preview': '预览',
        'lowercase': '中文小写',
        'currency': '人民币大写',
        'to_data_uri': '→ Data URI',
        'from_data_uri': '解析 Data URI',
        'complete': '补全校验位',
        'to_ini': '→ INI',
        'resolve': '解析',
    }
    return [(a, labels.get(a, a)) for a in actions]


@require_http_methods(['POST'])
def tool_api(request, slug: str):
    tool = get_tool(slug)
    if not tool:
        return JsonResponse({'ok': False, 'error': '工具不存在'}, status=404)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': '请求体必须是 JSON'}, status=400)

    action = payload.get('action') or (tool.actions[0] if tool.actions else '')
    text = payload.get('text', '')
    text_b = payload.get('text_b', '')
    options = payload.get('options') or {}
    if not isinstance(options, dict):
        options = {}

    result = run_tool(slug, action, text, options, text_b=text_b)
    status = 200 if result.get('ok', True) else 400
    return JsonResponse(result, status=status, json_dumps_params={'ensure_ascii': False})
