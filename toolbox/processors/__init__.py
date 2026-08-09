"""Tool processors — map slug + action to handler functions."""

from __future__ import annotations

from typing import Any, Callable

from . import convert, crypto_extra, encode, extras, generate, json_data, network, ops, reference, text

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
    'json-sql': json_data.json_sql,
    'xml-format': json_data.xml_format,
    'json-path': json_data.json_path,
    'json-schema': json_data.json_schema_gen,
    'yaml-format': json_data.yaml_format,
    'properties-json': json_data.properties_json,
    'base64': encode.base64_tool,
    'url-codec': encode.url_codec,
    'html-entities': encode.html_entities,
    'unicode': encode.unicode_tool,
    'hex': encode.hex_tool,
    'hash': encode.hash_tool,
    'jwt': encode.jwt_tool,
    'password-hash': encode.password_hash,
    'unicode-normalize': encode.unicode_normalize,
    'hmac': crypto_extra.hmac_tool,
    'aes': crypto_extra.aes_tool,
    'jwt-sign': crypto_extra.jwt_sign,
    'base32': crypto_extra.base32_tool,
    'morse': crypto_extra.morse_tool,
    'rot13': crypto_extra.rot13_tool,
    'crc32': crypto_extra.crc32_tool,
    'binary-text': crypto_extra.binary_text,
    'gzip': crypto_extra.gzip_tool,
    'base58': crypto_extra.base58_tool,
    'rsa': crypto_extra.rsa_tool,
    'jwt-verify': crypto_extra.jwt_verify,
    'timestamp': convert.timestamp_tool,
    'number-base': convert.number_base,
    'color': convert.color_tool,
    'case': convert.case_tool,
    'bytes-size': convert.bytes_size,
    'cron': convert.cron_tool,
    'roman': convert.roman_tool,
    'regex': text.regex_tool,
    'sql-format': text.sql_format,
    'markdown': text.markdown_tool,
    'text-stats': text.text_stats,
    'escape': text.escape_tool,
    'line-tools': text.line_tools,
    'css-js-minify': text.css_js_minify,
    'slugify': text.slugify_tool,
    'html-format': text.html_format,
    'markdown-html': text.markdown_html,
    'uuid': generate.uuid_tool,
    'password': generate.password_tool,
    'lorem': generate.lorem_tool,
    'qrcode': generate.qrcode_tool,
    'random': generate.random_tool,
    'hashids-like': generate.hashids_like,
    'nanoid': generate.nanoid_tool,
    'fake-data': generate.fake_data,
    'uuid-v5': generate.uuid_v5_tool,
    'password-strength': generate.password_strength,
    'ulid': generate.ulid_tool,
    'ip-cidr': network.ip_cidr,
    'user-agent': network.user_agent,
    'jwt-claims-time': network.jwt_claims_time,
    'url-parser': ops.url_parser,
    'chmod': ops.chmod_calc,
    'docker-compose': ops.docker_run_compose,
    'basic-auth': ops.basic_auth,
    'env-format': ops.env_format,
    'pem-decode': ops.pem_decode,
    'totp': ops.totp_tool,
    'curl-python': ops.curl_to_python,
    'ssh-keygen': ops.ssh_keygen,
    'http-status': reference.http_status,
    'mime-types': reference.mime_types,
    'content-headers': reference.content_headers,
    'regex-cheat': reference.regex_cheat,
    'bcrypt': extras.bcrypt_tool,
    'htpasswd': extras.htpasswd_tool,
    'css-beautify': extras.css_beautify,
    'js-beautify': extras.js_beautify,
    'dns-lookup': extras.dns_lookup,
    'contrast-check': extras.contrast_check,
    'csv-viewer': extras.csv_viewer,
    'graphql-format': extras.graphql_format,
    'image-base64': extras.image_base64,
    'ini-json': extras.ini_json,
    'sql-to-json': extras.sql_to_json,
    'number-chinese': extras.number_chinese,
    'luhn': extras.luhn_check,
    'ascii-table': extras.ascii_table,
    'port-ref': extras.port_ref,
    'punycode': extras.punycode_tool,
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
