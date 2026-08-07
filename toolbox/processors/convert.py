"""Conversion tools: time, color, case, cron, etc."""

from __future__ import annotations

import colorsys
import json
import re
from datetime import datetime, timezone
from typing import Any

from croniter import croniter


def timestamp_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    unit = options.get('unit') or 'auto'
    now = datetime.now(timezone.utc)
    local = datetime.now().astimezone()

    if action == 'now':
        result = {
            'utc_iso': now.isoformat(),
            'local_iso': local.isoformat(),
            'unix_s': int(now.timestamp()),
            'unix_ms': int(now.timestamp() * 1000),
        }
        return {'result': json.dumps(result, ensure_ascii=False, indent=2)}

    raw = text.strip()
    if action == 'to_datetime':
        if not raw:
            raise ValueError('请输入时间戳')
        num = float(raw)
        if unit == 'auto':
            unit = 'ms' if num > 1e12 else 's'
        ts = num / 1000.0 if unit == 'ms' else num
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        local_dt = dt.astimezone()
        result = {
            'input_unit': unit,
            'utc': dt.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'local': local_dt.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'iso': dt.isoformat(),
        }
        return {'result': json.dumps(result, ensure_ascii=False, indent=2)}

    if action == 'to_timestamp':
        # Accept ISO or "YYYY-mm-dd HH:MM:SS"
        try:
            if raw.endswith('Z'):
                dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(raw)
        except ValueError:
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d'):
                try:
                    dt = datetime.strptime(raw, fmt).astimezone()
                    break
                except ValueError:
                    dt = None
            if dt is None:
                raise ValueError('无法解析时间，请使用 ISO 或 YYYY-mm-dd HH:MM:SS') from None
        if dt.tzinfo is None:
            dt = dt.astimezone()
        result = {
            'unix_s': int(dt.timestamp()),
            'unix_ms': int(dt.timestamp() * 1000),
            'iso': dt.isoformat(),
        }
        return {'result': json.dumps(result, ensure_ascii=False, indent=2)}

    raise ValueError(f'未知操作: {action}')


def number_base(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'convert':
        raise ValueError(f'未知操作: {action}')
    raw = text.strip().replace(' ', '')
    from_base = int(options.get('from_base') or 10)
    if raw.lower().startswith('0x'):
        from_base = 16
        raw = raw[2:]
    elif raw.lower().startswith('0b'):
        from_base = 2
        raw = raw[2:]
    value = int(raw, from_base)
    result = {
        'decimal': str(value),
        'binary': bin(value),
        'octal': oct(value),
        'hex': hex(value),
        'hex_upper': hex(value).upper().replace('0X', '0x'),
    }
    return {'result': json.dumps(result, indent=2)}


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.strip().lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError('无效的 HEX 颜色')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def color_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'convert':
        raise ValueError(f'未知操作: {action}')
    raw = text.strip()
    r = g = b = None
    if raw.startswith('#') or re.fullmatch(r'[0-9a-fA-F]{3,8}', raw):
        r, g, b = _hex_to_rgb(raw if raw.startswith('#') else f'#{raw}')
    else:
        m = re.search(r'rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)', raw, re.I)
        if m:
            r, g, b = int(float(m.group(1))), int(float(m.group(2))), int(float(m.group(3)))
        else:
            m = re.search(r'hsla?\(\s*([\d.]+)\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%', raw, re.I)
            if not m:
                raise ValueError('请输入 #HEX、rgb() 或 hsl()')
            h, s, l = float(m.group(1)) / 360.0, float(m.group(2)) / 100.0, float(m.group(3)) / 100.0
            r_f, g_f, b_f = colorsys.hls_to_rgb(h, l, s)
            r, g, b = int(r_f * 255), int(g_f * 255), int(b_f * 255)

    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    result = {
        'hex': f'#{r:02X}{g:02X}{b:02X}',
        'rgb': f'rgb({r}, {g}, {b})',
        'hsl': f'hsl({round(h * 360)}, {round(s * 100)}%, {round(l * 100)}%)',
        'r': r,
        'g': g,
        'b': b,
    }
    return {'result': json.dumps(result, indent=2)}


def _split_words(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if '_' in text or '-' in text or ' ' in text:
        parts = re.split(r'[_\-\s]+', text)
        return [p for p in parts if p]
    # camel / pascal
    parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+', text)
    return [p for p in parts if p]


def case_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    words = _split_words(text)
    lower = [w.lower() for w in words]
    if action == 'snake':
        return {'result': '_'.join(lower)}
    if action == 'camel':
        if not lower:
            return {'result': ''}
        return {'result': lower[0] + ''.join(w.capitalize() for w in lower[1:])}
    if action == 'pascal':
        return {'result': ''.join(w.capitalize() for w in lower)}
    if action == 'kebab':
        return {'result': '-'.join(lower)}
    if action == 'constant':
        return {'result': '_'.join(w.upper() for w in lower)}
    if action == 'title':
        return {'result': ' '.join(w.capitalize() for w in lower)}
    if action == 'upper':
        return {'result': text.upper()}
    if action == 'lower':
        return {'result': text.lower()}
    raise ValueError(f'未知操作: {action}')


def bytes_size(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'convert':
        raise ValueError(f'未知操作: {action}')
    value = float(text.strip())
    unit = (options.get('unit') or 'B').upper()
    factors = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
    if unit not in factors:
        raise ValueError('单位无效')
    bytes_val = value * factors[unit]
    result = {u: bytes_val / f for u, f in factors.items()}
    pretty = {k: (int(v) if abs(v - int(v)) < 1e-9 else round(v, 6)) for k, v in result.items()}
    return {'result': json.dumps(pretty, indent=2)}


def cron_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'parse':
        raise ValueError(f'未知操作: {action}')
    expr = text.strip()
    if not croniter.is_valid(expr):
        raise ValueError('无效的 Cron 表达式（需要 5 段：分 时 日 月 周）')
    base = datetime.now()
    it = croniter(expr, base)
    next_runs = [it.get_next(datetime).strftime('%Y-%m-%d %H:%M:%S') for _ in range(8)]
    parts = expr.split()
    labels = ['分钟', '小时', '日', '月', '星期']
    explain = dict(zip(labels, parts))
    result = {
        'expression': expr,
        'fields': explain,
        'next_runs': next_runs,
    }
    return {'result': json.dumps(result, ensure_ascii=False, indent=2)}
