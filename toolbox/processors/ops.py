"""Ops / DevOps oriented tools."""

from __future__ import annotations

import base64
import json
import re
import shlex
from typing import Any
from urllib.parse import urlparse, parse_qs

import pyotp
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


def url_parser(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'parse':
        raise ValueError(f'未知操作: {action}')
    u = urlparse(text.strip())
    result = {
        'scheme': u.scheme,
        'netloc': u.netloc,
        'hostname': u.hostname,
        'port': u.port,
        'path': u.path,
        'params': u.params,
        'query': u.query,
        'query_dict': {k: (v[0] if len(v) == 1 else v) for k, v in parse_qs(u.query, keep_blank_values=True).items()},
        'fragment': u.fragment,
        'username': u.username,
        'password': u.password,
    }
    return {'result': json.dumps(result, ensure_ascii=False, indent=2)}


def chmod_calc(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'convert':
        raise ValueError(f'未知操作: {action}')
    raw = text.strip()
    # numeric -> symbolic
    if re.fullmatch(r'[0-7]{3,4}', raw):
        mode = int(raw[-3:], 8)
        def bits(n):
            return ('r' if n & 4 else '-') + ('w' if n & 2 else '-') + ('x' if n & 1 else '-')
        owner, group, other = bits(mode >> 6), bits((mode >> 3) & 7), bits(mode & 7)
        symbolic = f'-{owner}{group}{other}'
        return {'result': json.dumps({'octal': f'{mode:03o}', 'symbolic': symbolic}, indent=2)}
    # symbolic like rwxr-xr--
    m = re.search(r'([r-][w-][x-])([r-][w-][x-])([r-][w-][x-])', raw)
    if not m:
        raise ValueError('请输入如 755 或 rwxr-xr-x')

    def score(s):
        return (4 if s[0] == 'r' else 0) + (2 if s[1] == 'w' else 0) + (1 if s[2] == 'x' else 0)

    octal = f'{score(m.group(1))}{score(m.group(2))}{score(m.group(3))}'
    return {'result': json.dumps({'octal': octal, 'symbolic': f'-{m.group(1)}{m.group(2)}{m.group(3)}'}, indent=2)}


def docker_run_compose(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'convert':
        raise ValueError(f'未知操作: {action}')
    cmd = text.strip()
    if cmd.startswith('docker run'):
        cmd = cmd[len('docker run'):].strip()
    try:
        tokens = shlex.split(cmd)
    except ValueError as exc:
        raise ValueError(f'命令解析失败: {exc}') from exc

    service: dict[str, Any] = {'image': '', 'ports': [], 'environment': [], 'volumes': [], 'command': []}
    name = 'app'
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in ('-d', '--detach', '--rm', '-it', '-i', '-t', '--privileged'):
            i += 1
            continue
        if t in ('--name',) and i + 1 < len(tokens):
            name = tokens[i + 1]
            i += 2
            continue
        if t in ('-p', '--publish') and i + 1 < len(tokens):
            service['ports'].append(tokens[i + 1])
            i += 2
            continue
        if t in ('-e', '--env') and i + 1 < len(tokens):
            service['environment'].append(tokens[i + 1])
            i += 2
            continue
        if t in ('-v', '--volume') and i + 1 < len(tokens):
            service['volumes'].append(tokens[i + 1])
            i += 2
            continue
        if t.startswith('-'):
            # skip unknown flags with or without value
            if i + 1 < len(tokens) and not tokens[i + 1].startswith('-') and '=' not in t:
                i += 2
            else:
                i += 1
            continue
        # image and command
        service['image'] = t
        service['command'] = tokens[i + 1:]
        break

    if not service['image']:
        raise ValueError('未能解析镜像名，请粘贴完整 docker run 命令')

    lines = ['services:', f'  {name}:', f'    image: {service["image"]}']
    if service['ports']:
        lines.append('    ports:')
        for p in service['ports']:
            lines.append(f'      - "{p}"')
    if service['environment']:
        lines.append('    environment:')
        for e in service['environment']:
            lines.append(f'      - {e}')
    if service['volumes']:
        lines.append('    volumes:')
        for v in service['volumes']:
            lines.append(f'      - {v}')
    if service['command']:
        cmd_str = ' '.join(shlex.quote(c) for c in service['command'])
        lines.append(f'    command: {cmd_str}')
    return {'result': '\n'.join(lines) + '\n'}


def basic_auth(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'encode':
        user = options.get('user') or 'user'
        password = text if text.strip() else (options.get('password') or 'pass')
        # allow user:pass in text
        if ':' in text and not options.get('user'):
            user, password = text.split(':', 1)
        token = base64.b64encode(f'{user}:{password}'.encode('utf-8')).decode('ascii')
        return {'result': f'Authorization: Basic {token}\n{token}'}
    if action == 'decode':
        raw = text.strip()
        raw = raw.replace('Authorization:', '').replace('Basic', '').strip()
        decoded = base64.b64decode(raw).decode('utf-8')
        return {'result': decoded}
    raise ValueError(f'未知操作: {action}')


def env_format(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'format':
        lines = []
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith('#'):
                lines.append(line.rstrip())
                continue
            if '=' not in s:
                lines.append(s)
                continue
            k, v = s.split('=', 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if re.search(r'\s|#', v) or not v:
                v = json.dumps(v)
            lines.append(f'{k}={v}')
        return {'result': '\n'.join(lines)}
    if action == 'to_json':
        data = {}
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith('#') or '=' not in s:
                continue
            k, v = s.split('=', 1)
            v = v.strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            data[k.strip()] = v
        return {'result': json.dumps(data, ensure_ascii=False, indent=2)}
    raise ValueError(f'未知操作: {action}')


def pem_decode(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'decode':
        raise ValueError(f'未知操作: {action}')
    pem = text.strip().encode('utf-8')
    if b'BEGIN CERTIFICATE' in pem:
        cert = x509.load_pem_x509_certificate(pem, default_backend())
        result = {
            'type': 'certificate',
            'subject': cert.subject.rfc4514_string(),
            'issuer': cert.issuer.rfc4514_string(),
            'serial_number': str(cert.serial_number),
            'not_valid_before': cert.not_valid_before_utc.isoformat(),
            'not_valid_after': cert.not_valid_after_utc.isoformat(),
            'signature_algorithm': cert.signature_hash_algorithm.name if cert.signature_hash_algorithm else None,
        }
        return {'result': json.dumps(result, ensure_ascii=False, indent=2)}
    if b'BEGIN' in pem and b'PRIVATE KEY' in pem:
        key = serialization.load_pem_private_key(pem, password=None, backend=default_backend())
        result = {
            'type': 'private_key',
            'key_size': getattr(key, 'key_size', None),
        }
        return {'result': json.dumps(result, indent=2)}
    if b'BEGIN PUBLIC KEY' in pem or b'BEGIN RSA PUBLIC KEY' in pem:
        key = serialization.load_pem_public_key(pem, backend=default_backend())
        result = {
            'type': 'public_key',
            'key_size': getattr(key, 'key_size', None),
        }
        return {'result': json.dumps(result, indent=2)}
    raise ValueError('未识别的 PEM（支持证书 / 公私钥）')


def totp_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    secret = text.strip().replace(' ', '') or 'JBSWY3DPEHPK3PXP'
    if action == 'now':
        totp = pyotp.TOTP(secret)
        return {'result': json.dumps({'code': totp.now(), 'secret': secret, 'interval': 30}, indent=2)}
    if action == 'uri':
        name = options.get('name') or 'StackBox'
        issuer = options.get('issuer') or 'StackBox'
        totp = pyotp.TOTP(secret)
        return {'result': totp.provisioning_uri(name=name, issuer_name=issuer)}
    if action == 'random_secret':
        return {'result': pyotp.random_base32()}
    raise ValueError(f'未知操作: {action}')


def curl_to_python(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'convert':
        raise ValueError(f'未知操作: {action}')
    cmd = text.strip()
    if not cmd.lower().startswith('curl'):
        cmd = 'curl ' + cmd
    try:
        tokens = shlex.split(cmd)
    except ValueError as exc:
        raise ValueError(f'解析失败: {exc}') from exc
    method = 'GET'
    url = ''
    headers = []
    data = None
    i = 1
    while i < len(tokens):
        t = tokens[i]
        if t in ('-X', '--request') and i + 1 < len(tokens):
            method = tokens[i + 1].upper()
            i += 2
            continue
        if t in ('-H', '--header') and i + 1 < len(tokens):
            headers.append(tokens[i + 1])
            i += 2
            continue
        if t in ('-d', '--data', '--data-raw', '--data-binary') and i + 1 < len(tokens):
            data = tokens[i + 1]
            if method == 'GET':
                method = 'POST'
            i += 2
            continue
        if t.startswith('-'):
            if i + 1 < len(tokens) and not tokens[i + 1].startswith('-') and not t.startswith('--') and len(t) == 2:
                i += 2
            else:
                i += 1
            continue
        url = t
        i += 1
    if not url:
        raise ValueError('未找到 URL')
    hdr_dict = {}
    for h in headers:
        if ':' in h:
            k, v = h.split(':', 1)
            hdr_dict[k.strip()] = v.strip()
    lines = [
        'import requests',
        '',
        f'url = {url!r}',
        f'headers = {json.dumps(hdr_dict, ensure_ascii=False, indent=4)}',
    ]
    if data is not None:
        lines.append(f'data = {data!r}')
        lines.append(f'resp = requests.request({method!r}, url, headers=headers, data=data)')
    else:
        lines.append(f'resp = requests.request({method!r}, url, headers=headers)')
    lines += ['print(resp.status_code)', 'print(resp.text)']
    return {'result': '\n'.join(lines) + '\n'}


def ssh_keygen(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'generate':
        raise ValueError(f'未知操作: {action}')
    from cryptography.hazmat.primitives.asymmetric import rsa, ed25519
    from cryptography.hazmat.primitives import serialization

    algo = (options.get('algo') or 'ed25519').lower()
    comment = text.strip() or (options.get('comment') or 'stackbox@local')
    if algo == 'rsa':
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    else:
        key = ed25519.Ed25519PrivateKey.generate()
    priv = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode('ascii')
    pub = key.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    ).decode('ascii') + f' {comment}'
    return {'result': priv + chr(10) + pub + chr(10)}
