"""Network / IP / UA tools."""

from __future__ import annotations

import ipaddress
import json
import re
from datetime import datetime, timezone
from typing import Any

import jwt


def ip_cidr(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'parse':
        raise ValueError(f'未知操作: {action}')
    raw = text.strip()
    if '/' in raw:
        net = ipaddress.ip_network(raw, strict=False)
        hosts = list(net.hosts())
        result = {
            'network': str(net.network_address),
            'broadcast': str(net.broadcast_address) if net.version == 4 else None,
            'netmask': str(net.netmask),
            'wildcard': str(net.hostmask) if net.version == 4 else None,
            'prefixlen': net.prefixlen,
            'num_addresses': net.num_addresses,
            'host_min': str(hosts[0]) if hosts else str(net.network_address),
            'host_max': str(hosts[-1]) if hosts else str(net.broadcast_address),
            'version': net.version,
        }
        return {'result': json.dumps(result, ensure_ascii=False, indent=2)}

    ip = ipaddress.ip_address(raw)
    result = {
        'address': str(ip),
        'version': ip.version,
        'is_private': ip.is_private,
        'is_global': ip.is_global,
        'is_loopback': ip.is_loopback,
        'is_multicast': ip.is_multicast,
        'exploded': ip.exploded,
        'reverse_pointer': ip.reverse_pointer,
    }
    return {'result': json.dumps(result, ensure_ascii=False, indent=2)}


def user_agent(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'parse':
        raise ValueError(f'未知操作: {action}')
    ua = text.strip()
    browser = 'Unknown'
    os_name = 'Unknown'
    engine = 'Unknown'

    if 'Edg/' in ua:
        browser = 'Microsoft Edge ' + (re.search(r'Edg/([\d.]+)', ua).group(1) if re.search(r'Edg/([\d.]+)', ua) else '')
    elif 'Chrome/' in ua and 'Chromium' not in ua:
        browser = 'Chrome ' + (re.search(r'Chrome/([\d.]+)', ua).group(1) if re.search(r'Chrome/([\d.]+)', ua) else '')
    elif 'Firefox/' in ua:
        browser = 'Firefox ' + (re.search(r'Firefox/([\d.]+)', ua).group(1) if re.search(r'Firefox/([\d.]+)', ua) else '')
    elif 'Safari/' in ua and 'Chrome' not in ua:
        browser = 'Safari ' + (re.search(r'Version/([\d.]+)', ua).group(1) if re.search(r'Version/([\d.]+)', ua) else '')
    elif 'MSIE' in ua or 'Trident/' in ua:
        browser = 'Internet Explorer'

    if 'Windows NT 10' in ua:
        os_name = 'Windows 10/11'
    elif 'Windows NT' in ua:
        os_name = 'Windows'
    elif 'Mac OS X' in ua:
        m = re.search(r'Mac OS X ([0-9_]+)', ua)
        os_name = 'macOS ' + (m.group(1).replace('_', '.') if m else '')
    elif 'Android' in ua:
        m = re.search(r'Android ([\d.]+)', ua)
        os_name = 'Android ' + (m.group(1) if m else '')
    elif 'iPhone' in ua or 'iPad' in ua:
        os_name = 'iOS'
    elif 'Linux' in ua:
        os_name = 'Linux'

    if 'AppleWebKit' in ua:
        engine = 'Blink/WebKit'
    elif 'Gecko/' in ua:
        engine = 'Gecko'
    elif 'Trident/' in ua:
        engine = 'Trident'

    device = 'Mobile' if re.search(r'Mobile|Android|iPhone|iPad', ua) else 'Desktop'
    result = {
        'browser': browser.strip(),
        'os': os_name.strip(),
        'engine': engine,
        'device': device,
        'raw': ua,
    }
    return {'result': json.dumps(result, ensure_ascii=False, indent=2)}


def jwt_claims_time(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'explain':
        raise ValueError(f'未知操作: {action}')
    raw = text.strip()
    if raw.count('.') >= 2:
        payload = jwt.decode(raw, options={'verify_signature': False})
    else:
        payload = json.loads(raw)

    def fmt(v):
        if not isinstance(v, (int, float)):
            return v
        dt = datetime.fromtimestamp(v, tz=timezone.utc)
        return {
            'unix': int(v),
            'utc': dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'local': dt.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z'),
        }

    explained = {}
    for key in ('iat', 'exp', 'nbf', 'auth_time'):
        if key in payload:
            explained[key] = fmt(payload[key])
    result = {'claims': payload, 'time_fields': explained}
    return {'result': json.dumps(result, ensure_ascii=False, indent=2)}
