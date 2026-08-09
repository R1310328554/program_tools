"""Text and code tools."""

from __future__ import annotations

import html
import json
import re
from typing import Any

import markdown
import sqlparse


def regex_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    pattern = text
    sample = options.get('_text_b', '')
    flags_raw = (options.get('flags') or '').lower()
    flags = 0
    if 'i' in flags_raw:
        flags |= re.IGNORECASE
    if 'm' in flags_raw:
        flags |= re.MULTILINE
    if 's' in flags_raw:
        flags |= re.DOTALL
    if 'x' in flags_raw:
        flags |= re.VERBOSE
    try:
        rx = re.compile(pattern, flags)
    except re.error as exc:
        raise ValueError(f'正则错误: {exc}') from exc

    if action == 'match':
        m = rx.search(sample)
        if not m:
            return {'result': '无匹配'}
        groups = {
            'full': m.group(0),
            'span': list(m.span()),
            'groups': list(m.groups()),
            'groupdict': m.groupdict(),
        }
        return {'result': json.dumps(groups, ensure_ascii=False, indent=2)}

    if action == 'findall':
        found = rx.findall(sample)
        return {'result': json.dumps(found, ensure_ascii=False, indent=2)}

    if action == 'replace':
        repl = options.get('repl', '')
        out = rx.sub(repl, sample)
        return {'result': out}

    raise ValueError(f'未知操作: {action}')


def sql_format(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'format':
        return {'result': sqlparse.format(text, reindent=True, keyword_case='upper')}
    if action == 'minify':
        return {'result': sqlparse.format(text, strip_comments=True, strip_whitespace=True)}
    raise ValueError(f'未知操作: {action}')


def markdown_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'render':
        raise ValueError(f'未知操作: {action}')
    html = markdown.markdown(text, extensions=['fenced_code', 'tables', 'nl2br'])
    return {'result': html, 'html': True}


def text_stats(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'stats':
        raise ValueError(f'未知操作: {action}')
    lines = text.splitlines()
    words = re.findall(r'\S+', text)
    chinese = re.findall(r'[\u4e00-\u9fff]', text)
    result = {
        'chars': len(text),
        'chars_no_space': len(re.sub(r'\s', '', text)),
        'words': len(words),
        'lines': len(lines),
        'chinese_chars': len(chinese),
        'bytes_utf8': len(text.encode('utf-8')),
    }
    return {'result': json.dumps(result, ensure_ascii=False, indent=2)}


def escape_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'json_escape':
        return {'result': json.dumps(text, ensure_ascii=False)[1:-1]}
    if action == 'json_unescape':
        return {'result': json.loads(f'"{text}"')}
    if action == 'python_escape':
        return {'result': text.encode('unicode_escape').decode('ascii')}
    if action == 'python_unescape':
        return {'result': text.encode('utf-8').decode('unicode_escape')}
    raise ValueError(f'未知操作: {action}')


def line_tools(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    lines = text.splitlines()
    if action == 'unique':
        seen = set()
        out = []
        for line in lines:
            if line not in seen:
                seen.add(line)
                out.append(line)
        return {'result': '\n'.join(out)}
    if action == 'sort':
        return {'result': '\n'.join(sorted(lines))}
    if action == 'sort_desc':
        return {'result': '\n'.join(sorted(lines, reverse=True))}
    if action == 'trim_empty':
        return {'result': '\n'.join(line for line in lines if line.strip())}
    if action == 'number':
        width = len(str(len(lines)))
        return {'result': '\n'.join(f'{i:>{width}} | {line}' for i, line in enumerate(lines, 1))}
    if action == 'reverse':
        return {'result': '\n'.join(reversed(lines))}
    raise ValueError(f'未知操作: {action}')


def slugify_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    raw = text.strip().lower()
    # Keep ascii letters/digits; map spaces and others to hyphen; keep CJK as-is joined
    raw = re.sub(r'[\s_]+', '-', raw)
    if action == 'slugify':
        out = re.sub(r'[^a-z0-9\u4e00-\u9fff-]+', '', raw)
        out = re.sub(r'-{2,}', '-', out).strip('-')
        return {'result': out or 'item'}
    if action == 'filename':
        out = re.sub(r'[\\/:*?"<>|]+', '-', text.strip())
        out = re.sub(r'\s+', '_', out)
        return {'result': out or 'file'}
    raise ValueError(f'未知操作: {action}')


def css_js_minify(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'css':
        out = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
        out = re.sub(r'\s+', ' ', out)
        out = re.sub(r'\s*([{};:,>~+])\s*', r'\1', out)
        return {'result': out.strip()}
    if action == 'js':
        out = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
        out = re.sub(r'(?m)^\s*//.*?$', '', out)
        out = re.sub(r'\s+', ' ', out)
        return {'result': out.strip()}
    raise ValueError(f'未知操作: {action}')


def html_format(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'minify':
        out = re.sub(r'<!--.*?-->', '', text, flags=re.S)
        out = re.sub(r'>\s+<', '><', out)
        out = re.sub(r'\s+', ' ', out)
        return {'result': out.strip()}
    if action == 'format':
        # lightweight indent based on tags
        raw = re.sub(r'>\s+<', '><', text.strip())
        parts = re.split(r'(<[^>]+>)', raw)
        indent = 0
        lines = []
        for part in parts:
            if not part:
                continue
            if part.startswith('</'):
                indent = max(indent - 1, 0)
                lines.append('  ' * indent + part)
            elif part.startswith('<') and part.endswith('/>'):
                lines.append('  ' * indent + part)
            elif part.startswith('<') and not part.startswith('<!'):
                lines.append('  ' * indent + part)
                if not part.startswith('<?') and not re.match(r'<(br|hr|img|input|meta|link)\b', part, re.I):
                    indent += 1
            else:
                if part.strip():
                    lines.append('  ' * indent + part.strip())
        return {'result': '\n'.join(lines)}
    raise ValueError(f'未知操作: {action}')


def markdown_html(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'md_to_html':
        html = markdown.markdown(text, extensions=['fenced_code', 'tables', 'nl2br'])
        return {'result': html}
    if action == 'strip_html':
        out = re.sub(r'<script[\s\S]*?</script>', '', text, flags=re.I)
        out = re.sub(r'<style[\s\S]*?</style>', '', out, flags=re.I)
        out = re.sub(r'<[^>]+>', '', out)
        return {'result': html.unescape(out)}
    raise ValueError(f'未知操作: {action}')
