"""Encoding, hashing, JWT tools."""

from __future__ import annotations

import base64
import binascii
import hashlib
import html
import json
import secrets
from typing import Any
from urllib.parse import quote, unquote, quote_plus, unquote_plus

import jwt


def base64_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'encode':
        return {'result': base64.b64encode(text.encode('utf-8')).decode('ascii')}
    if action == 'decode':
        raw = text.strip()
        pad = '=' * (-len(raw) % 4)
        return {'result': base64.b64decode(raw + pad).decode('utf-8')}
    if action == 'url_encode':
        return {'result': base64.urlsafe_b64encode(text.encode('utf-8')).decode('ascii').rstrip('=')}
    if action == 'url_decode':
        raw = text.strip()
        pad = '=' * (-len(raw) % 4)
        return {'result': base64.urlsafe_b64decode(raw + pad).decode('utf-8')}
    raise ValueError(f'未知操作: {action}')


def url_codec(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'encode':
        return {'result': quote(text, safe=':/?#[]@!$&\'()*+,;=')}
    if action == 'decode':
        return {'result': unquote(text)}
    if action == 'encode_component':
        return {'result': quote(text, safe='')}
    if action == 'decode_component':
        return {'result': unquote_plus(text)}
    raise ValueError(f'未知操作: {action}')


def html_entities(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'encode':
        return {'result': html.escape(text, quote=True)}
    if action == 'decode':
        return {'result': html.unescape(text)}
    raise ValueError(f'未知操作: {action}')


def unicode_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'to_unicode':
        return {'result': ''.join(f'\\u{ord(c):04x}' for c in text)}
    if action == 'to_chinese':
        # Interpret \uXXXX sequences
        try:
            return {'result': text.encode('utf-8').decode('unicode_escape')}
        except Exception:
            # Fallback: replace sequences manually
            import re

            def repl(m):
                return chr(int(m.group(1), 16))

            return {'result': re.sub(r'\\u([0-9a-fA-F]{4})', repl, text)}
    if action == 'escape':
        return {'result': text.encode('unicode_escape').decode('ascii')}
    if action == 'unescape':
        return {'result': text.encode('utf-8').decode('unicode_escape')}
    raise ValueError(f'未知操作: {action}')


def hex_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'encode':
        return {'result': text.encode('utf-8').hex()}
    if action == 'decode':
        cleaned = text.strip().replace(' ', '').replace('0x', '')
        return {'result': bytes.fromhex(cleaned).decode('utf-8')}
    raise ValueError(f'未知操作: {action}')


def hash_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    algo = (options.get('algo') or 'all').lower()
    algos = ['md5', 'sha1', 'sha256', 'sha384', 'sha512']
    if algo != 'all':
        if algo not in algos:
            raise ValueError(f'不支持的算法: {algo}')
        algos = [algo]
    data = text.encode('utf-8')
    lines = []
    for name in algos:
        h = hashlib.new(name, data).hexdigest()
        lines.append(f'{name.upper()}: {h}')
    return {'result': '\n'.join(lines)}


def jwt_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'decode':
        raise ValueError(f'未知操作: {action}')
    token = text.strip()
    parts = token.split('.')
    if len(parts) < 2:
        raise ValueError('无效的 JWT')
    header = jwt.get_unverified_header(token)
    payload = jwt.decode(token, options={'verify_signature': False})
    out = {
        'header': header,
        'payload': payload,
        'signature': parts[2] if len(parts) > 2 else '',
    }
    return {'result': json.dumps(out, ensure_ascii=False, indent=2)}


def password_hash(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    password = text.encode('utf-8')
    salt = secrets.token_bytes(16)
    if action == 'pbkdf2':
        dk = hashlib.pbkdf2_hmac('sha256', password, salt, 120000)
        result = {
            'algo': 'pbkdf2_sha256',
            'iterations': 120000,
            'salt_hex': salt.hex(),
            'hash_hex': dk.hex(),
        }
        return {'result': json.dumps(result, indent=2)}
    if action == 'sha256_salt':
        digest = hashlib.sha256(salt + password).hexdigest()
        result = {
            'algo': 'sha256(salt+password)',
            'salt_hex': salt.hex(),
            'hash_hex': digest,
        }
        return {'result': json.dumps(result, indent=2)}
    raise ValueError(f'未知操作: {action}')
