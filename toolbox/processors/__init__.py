"""Tool processors — map slug + action to handler functions."""

from __future__ import annotations

from typing import Any, Callable

from . import convert, encode, generate, json_data, network, reference, text

Handler = Callable[[str, str, dict[str, Any]], dict[str, Any]]

PROCESSORS: dict[str, Handler] = {
    'json-format': json_data.json_format,
    'json-yaml': json_data.json_yaml,
    'json-xml': json_data.json_xml,
    'json-csv': json_data.json_csv,
    'json-query': json_data.json_query,
    'json-codegen': json_data.json_codegen,
    'json-diff': json_data.json_diff,
    'toml-json': json_data.toml_json,
    'base64': encode.base64_tool,
    'url-codec': encode.url_codec,
    'html-entities': encode.html_entities,
    'unicode': encode.unicode_tool,
    'hex': encode.hex_tool,
    'hash': encode.hash_tool,
    'jwt': encode.jwt_tool,
    'password-hash': encode.password_hash,
    'timestamp': convert.timestamp_tool,
    'number-base': convert.number_base,
    'color': convert.color_tool,
    'case': convert.case_tool,
    'bytes-size': convert.bytes_size,
    'cron': convert.cron_tool,
    'regex': text.regex_tool,
    'sql-format': text.sql_format,
    'markdown': text.markdown_tool,
    'text-stats': text.text_stats,
    'escape': text.escape_tool,
    'line-tools': text.line_tools,
    'css-js-minify': text.css_js_minify,
    'uuid': generate.uuid_tool,
    'password': generate.password_tool,
    'lorem': generate.lorem_tool,
    'qrcode': generate.qrcode_tool,
    'random': generate.random_tool,
    'hashids-like': generate.hashids_like,
    'ip-cidr': network.ip_cidr,
    'user-agent': network.user_agent,
    'jwt-claims-time': network.jwt_claims_time,
    'http-status': reference.http_status,
    'mime-types': reference.mime_types,
    'content-headers': reference.content_headers,
}


def run_tool(slug: str, action: str, text: str, options: dict[str, Any] | None = None, text_b: str = '') -> dict[str, Any]:
    handler = PROCESSORS.get(slug)
    if not handler:
        return {'ok': False, 'error': f'未知工具: {slug}'}
    opts = dict(options or {})
    if text_b:
        opts['_text_b'] = text_b
    try:
        result = handler(action, text, opts)
        if 'ok' not in result:
            result['ok'] = True
        return result
    except Exception as exc:  # noqa: BLE001 — surface tool errors to UI
        return {'ok': False, 'error': str(exc)}
