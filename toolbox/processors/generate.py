"""Generators: UUID, password, QR, lorem, random."""

from __future__ import annotations

import base64
import io
import json
import random
import re
import secrets
import string
import uuid
from typing import Any

import qrcode


LOREM = (
    'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor '
    'incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud '
    'exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure '
    'dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. '
    'Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt '
    'mollit anim id est laborum.'
)


def _count(options: dict[str, Any], default: int = 5) -> int:
    raw = options.get('count') or ''
    if not str(raw).strip():
        # also allow primary text as count for some tools
        return default
    try:
        n = int(str(raw).strip())
    except ValueError:
        n = default
    return max(1, min(n, 200))


def uuid_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'generate':
        raise ValueError(f'未知操作: {action}')
    count = _count(options, 5)
    if text.strip().isdigit():
        count = max(1, min(int(text.strip()), 200))
    upper = str(options.get('upper') or '0') == '1'
    items = []
    for _ in range(count):
        u = str(uuid.uuid4())
        items.append(u.upper() if upper else u)
    return {'result': '\n'.join(items)}


def password_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'generate':
        raise ValueError(f'未知操作: {action}')
    length = int(options.get('length') or (text.strip() if text.strip().isdigit() else 16) or 16)
    length = max(4, min(length, 128))
    count = _count(options, 5)
    use_symbols = str(options.get('symbols') or '1') == '1'
    alphabet = string.ascii_letters + string.digits
    if use_symbols:
        alphabet += '!@#$%^&*()-_=+[]{};:,.?'
    passwords = [''.join(secrets.choice(alphabet) for _ in range(length)) for _ in range(count)]
    return {'result': '\n'.join(passwords)}


def lorem_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    count = _count(options, 3)
    if text.strip().isdigit():
        count = max(1, min(int(text.strip()), 50))
    sentences = [s.strip() for s in LOREM.replace('?', '.').split('.') if s.strip()]
    words = LOREM.replace(',', '').replace('.', '').split()
    if action == 'paragraphs':
        paras = []
        for i in range(count):
            chunk = ' '.join(sentences[i % len(sentences):(i % len(sentences)) + 3])
            if not chunk.endswith('.'):
                chunk += '.'
            paras.append(chunk)
        return {'result': '\n\n'.join(paras)}
    if action == 'sentences':
        out = []
        for i in range(count):
            s = sentences[i % len(sentences)]
            out.append(s if s.endswith('.') else s + '.')
        return {'result': ' '.join(out)}
    if action == 'words':
        return {'result': ' '.join(words[i % len(words)] for i in range(count))}
    raise ValueError(f'未知操作: {action}')


def qrcode_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'generate':
        raise ValueError(f'未知操作: {action}')
    if not text.strip():
        raise ValueError('请输入要生成二维码的内容')
    img = qrcode.make(text)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    return {
        'result': f'data:image/png;base64,{b64}',
        'image': True,
        'meta': '已生成 PNG 二维码',
    }


def random_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    count = _count(options, 5)
    if action == 'int':
        raw = text.strip() or '1-100'
        m = re.fullmatch(r'\s*(-?\d+)\s*-\s*(-?\d+)\s*', raw)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
        elif raw.lstrip('-').isdigit():
            lo, hi = 0, int(raw)
        else:
            lo, hi = 1, 100
        if lo > hi:
            lo, hi = hi, lo
        nums = [str(random.randint(lo, hi)) for _ in range(count)]
        return {'result': '\n'.join(nums)}
    if action == 'hex':
        length = int(text.strip()) if text.strip().isdigit() else 32
        length = max(2, min(length, 256))
        items = [secrets.token_hex(length // 2) for _ in range(count)]
        return {'result': '\n'.join(items)}
    if action == 'token':
        length = int(text.strip()) if text.strip().isdigit() else 32
        length = max(8, min(length, 256))
        items = [secrets.token_urlsafe(length)[:length] for _ in range(count)]
        return {'result': '\n'.join(items)}
    raise ValueError(f'未知操作: {action}')


_ALPHABET = string.ascii_lowercase + string.digits
_BASE = len(_ALPHABET)


def hashids_like(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'encode':
        n = int(text.strip())
        if n < 0:
            raise ValueError('需要非负整数')
        if n == 0:
            return {'result': _ALPHABET[0]}
        chars = []
        while n:
            n, rem = divmod(n, _BASE)
            chars.append(_ALPHABET[rem])
        return {'result': ''.join(reversed(chars))}
    if action == 'decode':
        raw = text.strip()
        n = 0
        for ch in raw:
            n = n * _BASE + _ALPHABET.index(ch)
        return {'result': str(n)}
    raise ValueError(f'未知操作: {action}')


def nanoid_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'generate':
        raise ValueError(f'未知操作: {action}')
    alphabet = string.ascii_letters + string.digits + '_-'
    length = int(options.get('length') or (text.strip() if text.strip().isdigit() else 21) or 21)
    length = max(4, min(length, 128))
    count = _count(options, 5)
    items = [''.join(secrets.choice(alphabet) for _ in range(length)) for _ in range(count)]
    return {'result': '\n'.join(items)}


def fake_data(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    count = _count(options, 5)
    first = ['Ada', 'Grace', 'Alan', 'Linus', 'Guido', 'Ken', 'Dennis', 'Barbara']
    last = ['Lovelace', 'Hopper', 'Turing', 'Torvalds', 'van Rossum', 'Thompson', 'Ritchie', 'Liskov']
    domains = ['example.com', 'mail.dev', 'stackbox.local']
    if action == 'users':
        rows = []
        for i in range(count):
            f, l = random.choice(first), random.choice(last)
            email = f'{f.lower()}.{l.lower().replace(" ", "")}{i}@{random.choice(domains)}'
            rows.append({'id': i + 1, 'name': f'{f} {l}', 'email': email})
        return {'result': json.dumps(rows, ensure_ascii=False, indent=2)}
    if action == 'emails':
        items = []
        for i in range(count):
            f, l = random.choice(first), random.choice(last)
            items.append(f'{f.lower()}.{l.lower().replace(" ", "")}{i}@{random.choice(domains)}')
        return {'result': '\n'.join(items)}
    if action == 'names':
        items = [f'{random.choice(first)} {random.choice(last)}' for _ in range(count)]
        return {'result': '\n'.join(items)}
    raise ValueError(f'未知操作: {action}')


def uuid_v5_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'generate':
        raise ValueError(f'未知操作: {action}')
    ns_name = (options.get('namespace') or 'url').lower()
    ns_map = {
        'dns': uuid.NAMESPACE_DNS,
        'url': uuid.NAMESPACE_URL,
        'oid': uuid.NAMESPACE_OID,
        'x500': uuid.NAMESPACE_X500,
    }
    ns = ns_map.get(ns_name, uuid.NAMESPACE_URL)
    name = text.strip() or 'https://stackbox.local'
    return {'result': str(uuid.uuid5(ns, name))}


def password_strength(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'check':
        raise ValueError(f'未知操作: {action}')
    pw = text
    score = 0
    checks = {
        'length>=8': len(pw) >= 8,
        'length>=12': len(pw) >= 12,
        'has_lower': any(c.islower() for c in pw),
        'has_upper': any(c.isupper() for c in pw),
        'has_digit': any(c.isdigit() for c in pw),
        'has_symbol': any(not c.isalnum() for c in pw),
    }
    score = sum(1 for v in checks.values() if v)
    level = 'weak' if score <= 2 else 'fair' if score <= 4 else 'strong'
    return {'result': json.dumps({'score': score, 'level': level, 'checks': checks}, indent=2)}


def ulid_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'generate':
        raise ValueError(f'未知操作: {action}')
    # Crockford base32 ULID-like: 48-bit time ms + 80-bit randomness
    alphabet = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
    count = _count(options, 5)
    import time
    def one():
        ts = int(time.time() * 1000)
        chars = []
        for _ in range(10):
            chars.append(alphabet[ts & 31])
            ts >>= 5
        time_part = ''.join(reversed(chars))
        rand_part = ''.join(secrets.choice(alphabet) for _ in range(16))
        return time_part + rand_part
    return {'result': chr(10).join(one() for _ in range(count))}
