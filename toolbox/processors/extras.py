"""Extra tools integrated from weekly CN/INTL discovery gaps."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import re
import socket
from typing import Any


def bcrypt_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    try:
        import bcrypt
    except ImportError as exc:
        raise ValueError('需要安装 bcrypt 包') from exc
    if action == 'hash':
        rounds = int(options.get('rounds') or 12)
        rounds = max(4, min(rounds, 16))
        hashed = bcrypt.hashpw(text.encode('utf-8'), bcrypt.gensalt(rounds=rounds))
        return {'result': hashed.decode('ascii')}
    if action == 'verify':
        hashed = (options.get('hash') or options.get('_text_b') or '').strip()
        if not hashed:
            raise ValueError('请在选项 hash 或第二输入框提供 bcrypt 哈希')
        ok = bcrypt.checkpw(text.encode('utf-8'), hashed.encode('ascii'))
        return {'result': json.dumps({'match': bool(ok)}, indent=2)}
    raise ValueError(f'未知操作: {action}')


def htpasswd_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    user = (options.get('user') or 'admin').strip() or 'admin'
    password = text
    if ':' in text and not options.get('user'):
        user, password = text.split(':', 1)
    algo = (options.get('algo') or 'apr1').lower()
    if action != 'generate':
        raise ValueError(f'未知操作: {action}')
    if algo == 'sha1':
        digest = base64.b64encode(hashlib.sha1(password.encode('utf-8')).digest()).decode('ascii')
        return {'result': f'{user}:{{SHA}}{digest}'}
    # Apache MD5 apr1-like simplified using md5 iterated (not full apr1, but usable demo)
    # Prefer bcrypt htpasswd style if bcrypt available
    try:
        import bcrypt

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=10)).decode('ascii')
        return {'result': f'{user}:{hashed}'}
    except ImportError:
        salt = hashlib.md5(f'{user}{password}'.encode()).hexdigest()[:8]
        digest = hashlib.md5(f'{password}{salt}'.encode()).hexdigest()
        return {'result': f'{user}:$apr1${salt}${digest[:22]}'}


def css_beautify(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'beautify':
        raw = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
        raw = raw.replace('{', '{\n').replace('}', '\n}\n').replace(';', ';\n')
        lines = []
        indent = 0
        for line in raw.splitlines():
            s = line.strip()
            if not s:
                continue
            if s.startswith('}'):
                indent = max(indent - 1, 0)
            lines.append('  ' * indent + s)
            if s.endswith('{'):
                indent += 1
        return {'result': '\n'.join(lines) + '\n'}
    if action == 'minify':
        out = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
        out = re.sub(r'\s+', ' ', out)
        out = re.sub(r'\s*([{};:,])\s*', r'\1', out)
        return {'result': out.strip()}
    raise ValueError(f'未知操作: {action}')


def js_beautify(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'beautify':
        # lightweight brace-based formatter
        out = []
        indent = 0
        i = 0
        buf = ''
        in_str = None
        while i < len(text):
            ch = text[i]
            if in_str:
                buf += ch
                if ch == in_str and text[i - 1] != '\\':
                    in_str = None
                i += 1
                continue
            if ch in ('"', "'", '`'):
                in_str = ch
                buf += ch
                i += 1
                continue
            if ch in '{':
                buf = buf.strip()
                if buf:
                    out.append('  ' * indent + buf)
                out.append('  ' * indent + '{')
                indent += 1
                buf = ''
            elif ch in '}':
                buf = buf.strip()
                if buf:
                    out.append('  ' * indent + buf)
                    buf = ''
                indent = max(indent - 1, 0)
                out.append('  ' * indent + '}')
            elif ch == ';':
                buf = buf.strip()
                out.append('  ' * indent + buf + ';')
                buf = ''
            elif ch == '\n':
                if buf.strip():
                    out.append('  ' * indent + buf.strip())
                    buf = ''
            else:
                buf += ch
            i += 1
        if buf.strip():
            out.append('  ' * indent + buf.strip())
        return {'result': '\n'.join(out) + '\n'}
    if action == 'minify':
        out = re.sub(r'//.*?$', '', text, flags=re.M)
        out = re.sub(r'/\*.*?\*/', '', out, flags=re.S)
        out = re.sub(r'\s+', ' ', out)
        return {'result': out.strip()}
    raise ValueError(f'未知操作: {action}')


def dns_lookup(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    host = text.strip()
    if not host:
        raise ValueError('请输入域名或主机名')
    if action not in ('lookup', 'resolve'):
        raise ValueError(f'未知操作: {action}')
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise ValueError(f'DNS 查询失败: {exc}') from exc
    addrs = sorted({item[4][0] for item in infos})
    families = sorted({('IPv6' if ':' in a else 'IPv4') for a in addrs})
    try:
        hostname, aliases, ipaddrs = socket.gethostbyname_ex(host)
    except Exception:
        hostname, aliases, ipaddrs = host, [], [a for a in addrs if ':' not in a]
    result = {
        'host': host,
        'canonical_name': hostname,
        'aliases': aliases,
        'addresses': addrs,
        'ipv4': ipaddrs,
        'families': list(families),
    }
    return {'result': json.dumps(result, ensure_ascii=False, indent=2)}


def contrast_check(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'check':
        raise ValueError(f'未知操作: {action}')
    fg = text.strip()
    bg = (options.get('bg') or options.get('_text_b') or '#ffffff').strip()

    def parse(c: str) -> tuple[int, int, int]:
        c = c.lstrip('#')
        if len(c) == 3:
            c = ''.join(ch * 2 for ch in c)
        if len(c) != 6:
            raise ValueError(f'无效颜色: {c}')
        return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)

    def lin(v):
        v = v / 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    def lum(rgb):
        r, g, b = rgb
        return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)

    l1, l2 = lum(parse(fg)), lum(parse(bg))
    lighter, darker = max(l1, l2), min(l1, l2)
    ratio = (lighter + 0.05) / (darker + 0.05)
    result = {
        'foreground': fg if fg.startswith('#') else f'#{fg}',
        'background': bg if bg.startswith('#') else f'#{bg}',
        'contrast_ratio': round(ratio, 3),
        'aa_normal': ratio >= 4.5,
        'aa_large': ratio >= 3.0,
        'aaa_normal': ratio >= 7.0,
        'aaa_large': ratio >= 4.5,
    }
    return {'result': json.dumps(result, ensure_ascii=False, indent=2)}


def csv_viewer(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action not in ('preview', 'stats'):
        raise ValueError(f'未知操作: {action}')
    reader = csv.reader(io.StringIO(text.strip()))
    rows = list(reader)
    if not rows:
        return {'result': '空 CSV'}
    header, body = rows[0], rows[1:]
    if action == 'stats':
        result = {'columns': len(header), 'rows': len(body), 'header': header}
        return {'result': json.dumps(result, ensure_ascii=False, indent=2)}
    # markdown table preview
    lines = [
        '| ' + ' | '.join(header) + ' |',
        '| ' + ' | '.join(['---'] * len(header)) + ' |',
    ]
    for row in body[:50]:
        padded = row + [''] * (len(header) - len(row))
        lines.append('| ' + ' | '.join(padded[: len(header)]) + ' |')
    if len(body) > 50:
        lines.append(f'\n… 共 {len(body)} 行，仅预览前 50 行')
    return {'result': '\n'.join(lines)}


def graphql_format(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'minify':
        return {'result': re.sub(r'\s+', ' ', text).strip()}
    if action != 'format':
        raise ValueError(f'未知操作: {action}')
    out = []
    indent = 0
    for raw in text.replace('{', '{\n').replace('}', '\n}\n').replace('(', '(\n').replace(')', '\n)\n').splitlines():
        s = raw.strip()
        if not s:
            continue
        if s.startswith('}') or s.startswith(')'):
            indent = max(indent - 1, 0)
        out.append('  ' * indent + s)
        if s.endswith('{') or s.endswith('('):
            indent += 1
    return {'result': '\n'.join(out) + '\n'}


def image_base64(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'to_data_uri':
        mime = (options.get('mime') or 'image/png').strip()
        raw = text.strip()
        # if already raw base64 without header
        if raw.startswith('data:'):
            return {'result': raw}
        return {'result': f'data:{mime};base64,{raw}'}
    if action == 'from_data_uri':
        raw = text.strip()
        m = re.match(r'data:([^;]+);base64,(.+)$', raw, re.S)
        if not m:
            raise ValueError('需要 data:*;base64,... 格式')
        b64 = m.group(2)
        meta = {
            'mime': m.group(1),
            'base64_length': len(b64),
            'approx_bytes': len(base64.b64decode(b64 + '===')),
            'base64': b64[:120] + ('...' if len(b64) > 120 else ''),
        }
        return {'result': json.dumps(meta, ensure_ascii=False, indent=2), 'image': True if False else False}
    if action == 'preview':
        raw = text.strip()
        if not raw.startswith('data:'):
            mime = (options.get('mime') or 'image/png').strip()
            raw = f'data:{mime};base64,{raw}'
        return {'result': raw, 'image': True, 'meta': '图片预览（Base64 Data URI）'}
    raise ValueError(f'未知操作: {action}')


def ini_json(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'to_json':
        data: dict[str, Any] = {}
        section = ''
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith('#') or s.startswith(';'):
                continue
            if s.startswith('[') and s.endswith(']'):
                section = s[1:-1].strip()
                data.setdefault(section, {})
                continue
            if '=' in s:
                k, v = s.split('=', 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if section:
                    data[section][k] = v
                else:
                    data[k] = v
        return {'result': json.dumps(data, ensure_ascii=False, indent=2)}
    if action == 'to_ini':
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError('需要 JSON 对象')
        lines = []
        # top-level scalars first
        for k, v in data.items():
            if not isinstance(v, dict):
                lines.append(f'{k}={v}')
        for k, v in data.items():
            if isinstance(v, dict):
                lines.append(f'[{k}]')
                for sk, sv in v.items():
                    lines.append(f'{sk}={sv}')
                lines.append('')
        return {'result': '\n'.join(lines).strip() + '\n'}
    raise ValueError(f'未知操作: {action}')


def sql_to_json(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'convert':
        raise ValueError(f'未知操作: {action}')
    # Very small INSERT parser: INSERT INTO t (a,b) VALUES (1,'x'),(2,'y');
    m = re.search(
        r'insert\s+into\s+[`"\[]?(\w+)[`"\]]?\s*\(([^)]+)\)\s*values\s*(.+);?\s*$',
        text.strip(),
        re.I | re.S,
    )
    if not m:
        raise ValueError('仅支持简单 INSERT INTO table (cols) VALUES (...); 语句')
    table = m.group(1)
    cols = [c.strip().strip('`"[]') for c in m.group(2).split(',')]
    values_blob = m.group(3).strip().rstrip(';')
    rows = []
    for vm in re.finditer(r'\((.*?)\)(?=,|\s*$)', values_blob, re.S):
        parts = next(csv.reader([vm.group(1)], skipinitialspace=True))
        row = {}
        for i, col in enumerate(cols):
            val = parts[i].strip() if i < len(parts) else None
            if val is None or val.upper() == 'NULL':
                row[col] = None
            elif re.fullmatch(r'-?\d+', val or ''):
                row[col] = int(val)
            elif re.fullmatch(r'-?\d+\.\d+', val or ''):
                row[col] = float(val)
            else:
                row[col] = val.strip("'\"")
        rows.append(row)
    return {'result': json.dumps({'table': table, 'rows': rows}, ensure_ascii=False, indent=2)}


_CN_DIGITS = '零一二三四五六七八九'
_CN_UNITS = ['', '十', '百', '千']
_CN_SECTIONS = ['', '万', '亿', '兆']


def number_chinese(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    raw = text.strip().replace(',', '')
    if action == 'lowercase':
        # 简易小写中文数字
        if not re.fullmatch(r'\d+', raw):
            raise ValueError('请输入非负整数')
        n = int(raw)
        if n == 0:
            return {'result': '零'}

        def section_to_cn(num: int) -> str:
            s = ''
            unit_pos = 0
            zero = False
            while num > 0:
                d = num % 10
                if d == 0:
                    if not zero and s:
                        zero = True
                        s = '零' + s
                else:
                    zero = False
                    s = _CN_DIGITS[d] + _CN_UNITS[unit_pos] + s
                unit_pos += 1
                num //= 10
            return s.replace('一十', '十')

        parts = []
        sec = 0
        while n > 0:
            n, rem = divmod(n, 10000)
            if rem:
                parts.append(section_to_cn(rem) + _CN_SECTIONS[sec])
            elif parts:
                parts.append('零')
            sec += 1
        result = ''.join(reversed(parts))
        result = re.sub(r'零+', '零', result).rstrip('零')
        return {'result': result or '零'}

    if action == 'currency':
        # 人民币大写
        if not re.fullmatch(r'\d+(\.\d{1,2})?', raw):
            raise ValueError('请输入金额，最多两位小数')
        digits = '零壹贰叁肆伍陆柒捌玖'
        units = ['', '拾', '佰', '仟']
        sections = ['', '万', '亿']
        yuan, _, fen = raw.partition('.')
        fen = (fen + '00')[:2]
        n = int(yuan)

        def sec(num: int) -> str:
            s = ''
            pos = 0
            zero = False
            while num:
                d = num % 10
                if d == 0:
                    if not zero and s:
                        s = '零' + s
                        zero = True
                else:
                    zero = False
                    s = digits[d] + units[pos] + s
                pos += 1
                num //= 10
            return s

        if n == 0:
            int_part = '零'
        else:
            parts = []
            si = 0
            while n:
                n, rem = divmod(n, 10000)
                if rem:
                    parts.append(sec(rem) + sections[si])
                si += 1
            int_part = ''.join(reversed(parts))
        jiao, fen_d = int(fen[0]), int(fen[1])
        frac = ''
        if jiao == 0 and fen_d == 0:
            frac = '整'
        else:
            if jiao:
                frac += digits[jiao] + '角'
            elif fen_d:
                frac += '零'
            if fen_d:
                frac += digits[fen_d] + '分'
        return {'result': f'{int_part}元{frac}'}
    raise ValueError(f'未知操作: {action}')


def luhn_check(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    digits = re.sub(r'\D', '', text)
    if not digits:
        raise ValueError('请输入数字')
    if action == 'check':
        total = 0
        reverse = digits[::-1]
        for i, ch in enumerate(reverse):
            n = int(ch)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        ok = total % 10 == 0
        return {'result': json.dumps({'valid': ok, 'digits': digits, 'checksum_ok': ok}, indent=2)}
    if action == 'complete':
        base = digits
        for d in range(10):
            cand = base + str(d)
            total = 0
            for i, ch in enumerate(cand[::-1]):
                n = int(ch)
                if i % 2 == 1:
                    n *= 2
                    if n > 9:
                        n -= 9
                total += n
            if total % 10 == 0:
                return {'result': cand}
        raise ValueError('无法补全')
    raise ValueError(f'未知操作: {action}')


def ascii_table(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'list':
        rows = []
        for code in range(32, 127):
            rows.append(f'{code:3}  0x{code:02X}  {chr(code)}')
        return {'result': '\n'.join(rows)}
    if action == 'lookup':
        q = text.strip()
        if not q:
            return ascii_table('list', '', options)
        if q.isdigit():
            code = int(q)
            if not 0 <= code <= 127:
                raise ValueError('ASCII 范围 0-127')
            return {'result': f'{code}  0x{code:02X}  {chr(code) if code >= 32 else "?"}' }
        ch = q[0]
        return {'result': f'{ord(ch)}  0x{ord(ch):02X}  {ch}'}
    raise ValueError(f'未知操作: {action}')


PORT_REF = {
    20: 'FTP data',
    21: 'FTP control',
    22: 'SSH',
    23: 'Telnet',
    25: 'SMTP',
    53: 'DNS',
    80: 'HTTP',
    110: 'POP3',
    143: 'IMAP',
    443: 'HTTPS',
    465: 'SMTPS',
    587: 'SMTP submission',
    993: 'IMAPS',
    995: 'POP3S',
    1433: 'MSSQL',
    1521: 'Oracle',
    3306: 'MySQL',
    3389: 'RDP',
    5432: 'PostgreSQL',
    5672: 'AMQP',
    6379: 'Redis',
    8080: 'HTTP-alt',
    8443: 'HTTPS-alt',
    9200: 'Elasticsearch',
    27017: 'MongoDB',
}


def port_ref(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'list':
        rows = [f'{p:<6} {name}' for p, name in sorted(PORT_REF.items())]
        return {'result': '\n'.join(rows)}
    if action == 'lookup':
        q = text.strip().lower()
        if not q:
            return port_ref('list', '', options)
        if q.isdigit():
            p = int(q)
            name = PORT_REF.get(p)
            if not name:
                return {'ok': False, 'error': f'未收录端口 {p}'}
            return {'result': f'{p}  {name}'}
        hits = [f'{p}  {n}' for p, n in PORT_REF.items() if q in n.lower()]
        if not hits:
            return {'ok': False, 'error': f'未找到: {q}'}
        return {'result': '\n'.join(hits)}
    raise ValueError(f'未知操作: {action}')


def punycode_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'encode':
        # idna encode domain
        host = text.strip()
        try:
            return {'result': host.encode('idna').decode('ascii')}
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f'Punycode 编码失败: {exc}') from exc
    if action == 'decode':
        host = text.strip()
        try:
            return {'result': host.encode('ascii').decode('idna')}
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f'Punycode 解码失败: {exc}') from exc
    raise ValueError(f'未知操作: {action}')
