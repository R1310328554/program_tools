"""Reference lookup tools."""

from __future__ import annotations

import json
from typing import Any

HTTP_STATUS = {
    100: 'Continue',
    101: 'Switching Protocols',
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    204: 'No Content',
    206: 'Partial Content',
    301: 'Moved Permanently',
    302: 'Found',
    304: 'Not Modified',
    307: 'Temporary Redirect',
    308: 'Permanent Redirect',
    400: 'Bad Request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    413: 'Payload Too Large',
    415: 'Unsupported Media Type',
    422: 'Unprocessable Entity',
    429: 'Too Many Requests',
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
}

MIME_TYPES = {
    'html': 'text/html',
    'htm': 'text/html',
    'css': 'text/css',
    'js': 'text/javascript',
    'mjs': 'text/javascript',
    'json': 'application/json',
    'xml': 'application/xml',
    'txt': 'text/plain',
    'csv': 'text/csv',
    'md': 'text/markdown',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'webp': 'image/webp',
    'svg': 'image/svg+xml',
    'ico': 'image/x-icon',
    'pdf': 'application/pdf',
    'zip': 'application/zip',
    'gz': 'application/gzip',
    'tar': 'application/x-tar',
    'mp3': 'audio/mpeg',
    'mp4': 'video/mp4',
    'webm': 'video/webm',
    'woff': 'font/woff',
    'woff2': 'font/woff2',
    'ttf': 'font/ttf',
    'wasm': 'application/wasm',
    'yaml': 'application/yaml',
    'yml': 'application/yaml',
    'toml': 'application/toml',
    'form': 'application/x-www-form-urlencoded',
    'multipart': 'multipart/form-data',
}

HEADERS = [
    ('Accept', '客户端可接受的响应内容类型'),
    ('Authorization', '认证信息，如 Bearer Token'),
    ('Content-Type', '请求/响应体的媒体类型'),
    ('Content-Length', '正文长度（字节）'),
    ('Cache-Control', '缓存策略'),
    ('Cookie', '浏览器发送的 Cookie'),
    ('Set-Cookie', '服务器设置 Cookie'),
    ('ETag', '资源版本标识，用于缓存校验'),
    ('If-None-Match', '条件请求，配合 ETag'),
    ('Last-Modified', '资源最后修改时间'),
    ('Location', '重定向目标地址'),
    ('Origin', '跨域请求来源'),
    ('Access-Control-Allow-Origin', 'CORS 允许的来源'),
    ('User-Agent', '客户端标识'),
    ('X-Request-Id', '请求追踪 ID（常见自定义头）'),
    ('X-Forwarded-For', '代理链中的原始客户端 IP'),
    ('X-Real-IP', '反向代理传递的真实 IP'),
    ('Referer', '来源页面'),
    ('Host', '目标主机名'),
]


def http_status(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'list':
        rows = [f'{code}  {name}' for code, name in sorted(HTTP_STATUS.items())]
        return {'result': '\n'.join(rows)}
    if action == 'lookup':
        raw = text.strip()
        if not raw:
            return http_status('list', '', options)
        code = int(raw)
        name = HTTP_STATUS.get(code)
        if not name:
            return {'ok': False, 'error': f'未收录状态码 {code}'}
        return {'result': f'{code}  {name}'}
    raise ValueError(f'未知操作: {action}')


def mime_types(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'list':
        rows = [f'.{ext:12} {mime}' for ext, mime in sorted(MIME_TYPES.items())]
        return {'result': '\n'.join(rows)}
    if action == 'lookup':
        key = text.strip().lower().lstrip('.')
        if not key:
            return mime_types('list', '', options)
        if key in MIME_TYPES:
            return {'result': f'.{key} → {MIME_TYPES[key]}'}
        # reverse lookup by mime
        hits = [f'.{ext} → {mime}' for ext, mime in MIME_TYPES.items() if key in mime]
        if hits:
            return {'result': '\n'.join(hits)}
        return {'ok': False, 'error': f'未找到: {key}'}
    raise ValueError(f'未知操作: {action}')


def content_headers(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'list':
        raise ValueError(f'未知操作: {action}')
    q = text.strip().lower()
    rows = HEADERS
    if q:
        rows = [h for h in HEADERS if q in h[0].lower() or q in h[1].lower()]
    result = [{'name': n, 'desc': d} for n, d in rows]
    pretty = '\n'.join(f'{n:28} {d}' for n, d in rows)
    return {'result': pretty, 'rows': result}
