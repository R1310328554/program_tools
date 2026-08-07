"""JSON and data-format tools."""

from __future__ import annotations

import csv
import difflib
import io
import json
import re
from typing import Any
from urllib.parse import parse_qs, urlencode

import xmltodict
import yaml


def _loads(text: str) -> Any:
    return json.loads(text)


def _dumps(data: Any, *, indent: int | None = 2, sort_keys: bool = False, ensure_ascii: bool = False) -> str:
    if indent is None:
        return json.dumps(data, ensure_ascii=ensure_ascii, sort_keys=sort_keys, separators=(',', ':'))
    return json.dumps(data, ensure_ascii=ensure_ascii, sort_keys=sort_keys, indent=indent)


def json_format(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'validate':
        try:
            _loads(text)
            return {'ok': True, 'result': '✓ JSON 合法'}
        except json.JSONDecodeError as exc:
            return {'ok': False, 'error': f'JSON 无效: {exc}'}
    data = _loads(text)
    if action == 'format':
        return {'result': _dumps(data, indent=2)}
    if action == 'minify':
        return {'result': _dumps(data, indent=None)}
    if action == 'sort':
        return {'result': _dumps(data, indent=2, sort_keys=True)}
    raise ValueError(f'未知操作: {action}')


def json_yaml(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'to_yaml':
        data = _loads(text)
        return {'result': yaml.safe_dump(data, allow_unicode=True, sort_keys=False)}
    if action == 'to_json':
        data = yaml.safe_load(text)
        return {'result': _dumps(data)}
    raise ValueError(f'未知操作: {action}')


def json_xml(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'to_xml':
        data = _loads(text)
        if not isinstance(data, dict):
            data = {'root': data}
        xml = xmltodict.unparse(data, pretty=True)
        return {'result': xml}
    if action == 'to_json':
        data = xmltodict.parse(text)
        return {'result': _dumps(data)}
    raise ValueError(f'未知操作: {action}')


def json_csv(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'to_csv':
        data = _loads(text)
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list) or not data:
            raise ValueError('需要非空对象数组')
        if not all(isinstance(x, dict) for x in data):
            raise ValueError('数组元素必须是对象')
        fieldnames: list[str] = []
        for row in data:
            for k in row:
                if k not in fieldnames:
                    fieldnames.append(k)
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in data:
            writer.writerow({k: '' if row.get(k) is None else row.get(k) for k in fieldnames})
        return {'result': buf.getvalue()}
    if action == 'to_json':
        reader = csv.DictReader(io.StringIO(text.strip()))
        rows = list(reader)
        return {'result': _dumps(rows)}
    raise ValueError(f'未知操作: {action}')


def json_query(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'to_query':
        data = _loads(text)
        if not isinstance(data, dict):
            raise ValueError('需要 JSON 对象')
        flat = {k: v if isinstance(v, (str, int, float, bool)) else json.dumps(v, ensure_ascii=False) for k, v in data.items()}
        return {'result': urlencode(flat, doseq=True)}
    if action == 'to_json':
        raw = text.strip()
        if raw.startswith('?'):
            raw = raw[1:]
        parsed = parse_qs(raw, keep_blank_values=True)
        out = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
        return {'result': _dumps(out)}
    raise ValueError(f'未知操作: {action}')


def _py_type(v: Any) -> str:
    if isinstance(v, bool):
        return 'bool'
    if isinstance(v, int):
        return 'int'
    if isinstance(v, float):
        return 'float'
    if isinstance(v, str):
        return 'str'
    if isinstance(v, list):
        if not v:
            return 'list[Any]'
        return f'list[{_py_type(v[0])}]'
    if isinstance(v, dict):
        return 'dict[str, Any]'
    return 'Any'


def _ts_type(v: Any) -> str:
    if isinstance(v, bool):
        return 'boolean'
    if isinstance(v, int | float):
        return 'number'
    if isinstance(v, str):
        return 'string'
    if isinstance(v, list):
        if not v:
            return 'any[]'
        return f'{_ts_type(v[0])}[]'
    if isinstance(v, dict):
        return 'Record<string, any>'
    return 'any'


def _go_type(v: Any) -> str:
    if isinstance(v, bool):
        return 'bool'
    if isinstance(v, int):
        return 'int'
    if isinstance(v, float):
        return 'float64'
    if isinstance(v, str):
        return 'string'
    if isinstance(v, list):
        if not v:
            return '[]any'
        return f'[]{_go_type(v[0])}'
    if isinstance(v, dict):
        return 'map[string]any'
    return 'any'


def _java_type(v: Any) -> str:
    if isinstance(v, bool):
        return 'Boolean'
    if isinstance(v, int):
        return 'Integer'
    if isinstance(v, float):
        return 'Double'
    if isinstance(v, str):
        return 'String'
    if isinstance(v, list):
        if not v:
            return 'List<Object>'
        return f'List<{_java_type(v[0])}>'
    if isinstance(v, dict):
        return 'Map<String, Object>'
    return 'Object'


def _cs_type(v: Any) -> str:
    if isinstance(v, bool):
        return 'bool'
    if isinstance(v, int):
        return 'int'
    if isinstance(v, float):
        return 'double'
    if isinstance(v, str):
        return 'string'
    if isinstance(v, list):
        if not v:
            return 'List<object>'
        return f'List<{_cs_type(v[0])}>'
    if isinstance(v, dict):
        return 'Dictionary<string, object>'
    return 'object'


def _pascal(name: str) -> str:
    parts = re.split(r'[^0-9A-Za-z]+', name)
    return ''.join(p[:1].upper() + p[1:] for p in parts if p) or 'Root'


def json_codegen(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    data = _loads(text)
    root = options.get('root_name') or 'Root'
    root = _pascal(str(root))
    if not isinstance(data, dict):
        data = {'value': data}

    if action == 'python':
        lines = ['from __future__ import annotations', '', 'from dataclasses import dataclass', 'from typing import Any', '', f'@dataclass', f'class {root}:']
        for k, v in data.items():
            lines.append(f'    {k}: {_py_type(v)}')
        return {'result': '\n'.join(lines) + '\n'}

    if action == 'typescript':
        lines = [f'export interface {root} {{']
        for k, v in data.items():
            key = k if re.match(r'^[A-Za-z_]\w*$', k) else json.dumps(k)
            lines.append(f'  {key}: {_ts_type(v)};')
        lines.append('}')
        return {'result': '\n'.join(lines) + '\n'}

    if action == 'go':
        lines = [f'type {root} struct {{']
        for k, v in data.items():
            field = _pascal(k)
            lines.append(f'\t{field} {_go_type(v)} `json:"{k}"`')
        lines.append('}')
        return {'result': '\n'.join(lines) + '\n'}

    if action == 'java':
        lines = [f'public class {root} {{']
        for k, v in data.items():
            lines.append(f'    private {_java_type(v)} {k};')
        for k, v in data.items():
            t = _java_type(v)
            prop = _pascal(k)
            lines.append('')
            lines.append(f'    public {t} get{prop}() {{ return {k}; }}')
            lines.append(f'    public void set{prop}({t} {k}) {{ this.{k} = {k}; }}')
        lines.append('}')
        return {'result': '\n'.join(lines) + '\n'}

    if action == 'csharp':
        lines = [f'public class {root}', '{']
        for k, v in data.items():
            lines.append(f'    public {_cs_type(v)} {_pascal(k)} {{ get; set; }}')
        lines.append('}')
        return {'result': '\n'.join(lines) + '\n'}

    raise ValueError(f'未知操作: {action}')


def json_diff(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    left = text
    right = options.get('_text_b', '')
    try:
        left_j = _dumps(_loads(left), sort_keys=True)
        right_j = _dumps(_loads(right), sort_keys=True)
        left, right = left_j, right_j
    except Exception:
        pass
    diff = difflib.unified_diff(
        left.splitlines(),
        right.splitlines(),
        fromfile='left',
        tofile='right',
        lineterm='',
    )
    out = '\n'.join(diff)
    return {'result': out or '（无差异）'}


def _toml_escape(s: str) -> str:
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def _to_toml(data: Any, prefix: str = '') -> str:
    if not isinstance(data, dict):
        raise ValueError('根节点需要是对象')
    lines: list[str] = []
    tables: list[tuple[str, dict]] = []
    for k, v in data.items():
        key = k if re.match(r'^[A-Za-z0-9_-]+$', k) else _toml_escape(k)
        path = f'{prefix}.{key}' if prefix else key
        if isinstance(v, dict):
            tables.append((path, v))
        elif isinstance(v, bool):
            lines.append(f'{key} = {"true" if v else "false"}')
        elif isinstance(v, int | float):
            lines.append(f'{key} = {v}')
        elif isinstance(v, str):
            lines.append(f'{key} = {_toml_escape(v)}')
        elif isinstance(v, list):
            if all(isinstance(i, (str, int, float, bool)) for i in v):
                parts = []
                for i in v:
                    if isinstance(i, bool):
                        parts.append('true' if i else 'false')
                    elif isinstance(i, str):
                        parts.append(_toml_escape(i))
                    else:
                        parts.append(str(i))
                lines.append(f'{key} = [{", ".join(parts)}]')
            else:
                lines.append(f'# unsupported nested array: {key}')
        elif v is None:
            lines.append(f'# {key} = null')
        else:
            lines.append(f'# unsupported: {key}')
    chunks = ['\n'.join(lines)] if lines else []
    for path, table in tables:
        chunks.append(f'[{path}]')
        chunks.append(_to_toml(table, path).replace(f'[{path}]\n', '') if False else _simple_table(table))
    return '\n'.join(c for c in chunks if c).strip() + '\n'


def _simple_table(data: dict) -> str:
    lines = []
    for k, v in data.items():
        key = k if re.match(r'^[A-Za-z0-9_-]+$', k) else _toml_escape(k)
        if isinstance(v, bool):
            lines.append(f'{key} = {"true" if v else "false"}')
        elif isinstance(v, int | float):
            lines.append(f'{key} = {v}')
        elif isinstance(v, str):
            lines.append(f'{key} = {_toml_escape(v)}')
        elif isinstance(v, list) and all(isinstance(i, (str, int, float, bool)) for i in v):
            parts = []
            for i in v:
                if isinstance(i, bool):
                    parts.append('true' if i else 'false')
                elif isinstance(i, str):
                    parts.append(_toml_escape(i))
                else:
                    parts.append(str(i))
            lines.append(f'{key} = [{", ".join(parts)}]')
        elif isinstance(v, dict):
            lines.append(f'# nested table skipped: {key}')
        else:
            lines.append(f'# skipped: {key}')
    return '\n'.join(lines)


def toml_json(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    # Prefer tomllib (3.11+) when available.
    try:
        import tomllib
    except ImportError:  # pragma: no cover
        tomllib = None

    if action == 'to_json':
        if tomllib is None:
            raise ValueError('当前环境不支持 TOML 解析')
        data = tomllib.loads(text)
        return {'result': _dumps(data)}
    if action == 'to_toml':
        data = _loads(text)
        return {'result': _to_toml(data)}
    raise ValueError(f'未知操作: {action}')
