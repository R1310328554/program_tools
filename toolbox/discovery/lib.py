"""Shared helpers for nightly/weekly tool discovery."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / 'toolbox' / 'discovery' / 'community_catalog.json'
SOURCES_PATH = ROOT / 'toolbox' / 'discovery' / 'sources_global.json'
CANDIDATES_PATH = ROOT / 'toolbox' / 'discovery' / 'candidates.json'
WEEKLY_PATH = ROOT / 'toolbox' / 'discovery' / 'weekly_candidates.json'
REPORTS_DIR = ROOT / 'reports'

CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ('json', ('json', 'yaml', 'xml', 'csv', 'toml', 'schema', 'jsonpath', 'properties', 'ini', 'graphql')),
    ('encode', ('base64', 'base32', 'base58', 'hash', 'md5', 'sha', 'aes', 'rsa', 'jwt', 'hmac', 'bcrypt', 'gzip', 'morse', 'rot', 'hex', 'unicode', 'crc', 'htpasswd', 'encrypt', 'decrypt', 'pem')),
    ('convert', ('timestamp', 'color', 'cron', 'chmod', 'docker', 'curl', 'roman', 'unit', 'bytes', 'case', 'contrast', 'palette', 'chinese', 'number')),
    ('text', ('regex', 'sql', 'markdown', 'html', 'css', 'javascript', 'js', 'diff', 'escape', 'slug', 'env', 'beautify', 'minify', 'lorem', 'graphql')),
    ('generate', ('uuid', 'ulid', 'nanoid', 'password', 'qr', 'fake', 'totp', 'otp', 'ssh', 'random', 'barcode', 'lorem')),
    ('network', ('ip', 'cidr', 'dns', 'url', 'ua', 'user-agent', 'whois', 'ssl', 'cert', 'header', 'websocket', 'subnet', 'port')),
    ('reference', ('http', 'mime', 'status', 'cheat', 'cheatsheet', 'ascii', 'ports')),
    ('frontend', ('css', 'color', 'contrast', 'gradient', 'shadow', 'favicon', 'svg', 'meta')),
    ('security', ('password', 'hash', 'xss', 'jwt', 'totp', 'bcrypt', 'htpasswd', 'luhn', 'iban')),
]


def normalize(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', (s or '').lower()).strip('-')


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def guess_category(name: str, tags: list[str] | None = None, slug: str = '') -> str:
    blob = ' '.join([name or '', slug or '', *(tags or [])]).lower()
    scores: dict[str, int] = {}
    for cat, keys in CATEGORY_RULES:
        score = sum(1 for k in keys if k in blob)
        if score:
            scores[cat] = score
    if not scores:
        return 'text'
    return max(scores.items(), key=lambda x: x[1])[0]


def existing_tool_index() -> tuple[set[str], str]:
    # Lazy import to avoid Django requirement for pure catalog ops when possible
    try:
        from toolbox.registry import TOOLS

        slugs = {t.slug for t in TOOLS}
        blob = ' '.join(' '.join([t.slug, t.name, *t.tags]) for t in TOOLS).lower()
        return slugs, blob
    except Exception:
        return set(), ''


def is_covered(hint: str, have: set[str], blob: str) -> bool:
    hint = normalize(hint)
    if hint in have:
        return True
    tokens = [x for x in hint.split('-') if len(x) > 2]
    if tokens and all(tok in blob for tok in tokens):
        return True
    compact = hint.replace('-', '')
    if compact and compact in blob.replace('-', '').replace(' ', ''):
        return True
    return False


def http_get_json(url: str, timeout: int = 30) -> dict[str, Any] | None:
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    headers = {
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'StackBox-DiscoveryBot/1.0',
    }
    if token and 'api.github.com' in url:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def http_get_text(url: str, timeout: int = 25) -> str | None:
    headers = {'User-Agent': 'StackBox-DiscoveryBot/1.0'}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            for enc in ('utf-8', 'gb18030', 'latin-1'):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw.decode('utf-8', errors='ignore')
    except (urllib.error.URLError, TimeoutError):
        return None


def github_search_repos(query: str, per_page: int = 15) -> list[dict[str, Any]]:
    q = urllib.parse.quote(query)
    url = f'https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page={per_page}'
    data = http_get_json(url)
    if not data:
        return []
    out = []
    for repo in data.get('items', []):
        out.append(
            {
                'full_name': repo.get('full_name'),
                'html_url': repo.get('html_url'),
                'description': repo.get('description') or '',
                'stars': repo.get('stargazers_count') or 0,
                'topics': repo.get('topics') or [],
                'language': repo.get('language'),
            }
        )
    return out


def extract_tools_from_readme(text: str, source: str) -> list[dict[str, Any]]:
    """Heuristic extraction of tool names from README markdown tables/lists."""
    found: dict[str, dict[str, Any]] = {}
    # Table rows: | Name | desc |
    for m in re.finditer(r'^\|\s*\[?([^|\]]+?)\]?[^|]*\|\s*([^|]+)\|', text, re.M):
        name = m.group(1).strip()
        desc = m.group(2).strip()
        if len(name) < 2 or len(name) > 60:
            continue
        if name.lower() in {'tool', 'name', '---', ':---', ':---:'}:
            continue
        if re.fullmatch(r'[:\-\s]+', name):
            continue
        slug = normalize(name)
        if not slug or slug in found:
            continue
        found[slug] = {
            'slug_hint': slug,
            'name': re.sub(r'[*`]+', '', name),
            'description': re.sub(r'[*`]+', '', desc)[:180],
            'tags': [],
            'source': source,
            'priority': 'medium',
        }
    # Bullet lines mentioning Formatter/Encoder/Generator/转换/格式化
    for m in re.finditer(
        r'^[\-\*]\s+(?:\*\*|__)?\[?([^\n\]]{2,50})\]?(?:\*\*|__)?\s*[\-—:：]\s*([^\n]+)',
        text,
        re.M,
    ):
        name = m.group(1).strip()
        desc = m.group(2).strip()
        if not re.search(r'format|encode|decode|convert|generat|hash|regex|json|yaml|uuid|cron|密码|格式化|编码|转换|生成|校验', (name + ' ' + desc), re.I):
            continue
        slug = normalize(name)
        if slug and slug not in found:
            found[slug] = {
                'slug_hint': slug,
                'name': name,
                'description': desc[:180],
                'tags': [],
                'source': source,
                'priority': 'low',
            }
    return list(found.values())


def prioritize(item: dict[str, Any]) -> str:
    if item.get('priority') in {'high', 'medium', 'low'}:
        return item['priority']
    blob = ' '.join([item.get('slug_hint', ''), item.get('name', ''), ' '.join(item.get('tags') or [])]).lower()
    high_keys = ('json', 'base64', 'jwt', 'regex', 'uuid', 'hash', 'timestamp', 'aes', 'rsa', 'yaml', 'sql')
    if any(k in blob for k in high_keys):
        return 'high'
    return 'medium'
