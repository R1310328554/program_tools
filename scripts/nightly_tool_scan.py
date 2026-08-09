#!/usr/bin/env python3
"""Nightly community scan for developer tools missing from StackBox.

Designed to run at 01:00 Asia/Shanghai via GitHub Actions (cron 0 17 * * *)
or manually / via Cursor Automation.

It:
1. Loads curated community catalog + optional live GitHub topic search
2. Diffs against toolbox.registry.TOOLS
3. Writes reports/tool-scan-<date>.md and toolbox/discovery/candidates.json
4. Optionally creates/updates a GitHub issue when --create-issue is set
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stackbox.settings')

import django

django.setup()

from toolbox.registry import TOOLS  # noqa: E402

CATALOG_PATH = ROOT / 'toolbox' / 'discovery' / 'community_catalog.json'
CANDIDATES_PATH = ROOT / 'toolbox' / 'discovery' / 'candidates.json'
REPORTS_DIR = ROOT / 'reports'


def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding='utf-8'))


def existing_slugs() -> set[str]:
    return {t.slug for t in TOOLS}


def existing_blob() -> str:
    parts = []
    for t in TOOLS:
        parts.append(' '.join([t.slug, t.name, *t.tags]))
    return ' '.join(parts).lower()


def normalize(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def gap_from_catalog(catalog: dict) -> list[dict]:
    have = existing_slugs()
    blob = existing_blob()
    gaps = []
    for item in catalog.get('known_tools', []):
        hint = item.get('slug_hint') or normalize(item.get('name', ''))
        tags = item.get('tags') or []
        covered = hint in have or any(normalize(tag) in blob and hint.replace('-', '') in blob.replace('-', '') for tag in tags[:1])
        # stricter: only slug match or close name in blob
        covered = hint in have
        if not covered:
            # fuzzy: if all significant tokens appear in existing names
            tokens = [x for x in re.split(r'[^a-z0-9]+', hint) if len(x) > 2]
            if tokens and all(tok in blob for tok in tokens):
                covered = True
        if covered:
            continue
        gaps.append(
            {
                'slug_hint': hint,
                'name': item.get('name') or hint,
                'tags': tags,
                'priority': item.get('priority') or 'medium',
                'reason': 'listed in community_catalog but missing from registry',
            }
        )
    priority_rank = {'high': 0, 'medium': 1, 'low': 2}
    gaps.sort(key=lambda g: (priority_rank.get(g['priority'], 9), g['slug_hint']))
    return gaps


def github_topic_hints(limit: int = 20) -> list[dict]:
    """Best-effort live scan of GitHub topic developer-tools (optional)."""
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    url = (
        'https://api.github.com/search/repositories'
        '?q=topic:developer-tools+online+tools&sort=updated&order=desc&per_page=10'
    )
    headers = {
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'StackBox-NightlyScan',
    }
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return [{'slug_hint': '_github_scan_error', 'name': 'GitHub scan skipped', 'tags': [], 'priority': 'low', 'reason': str(exc)}]

    hints = []
    for repo in data.get('items', [])[:limit]:
        hints.append(
            {
                'slug_hint': normalize(repo.get('name') or 'repo'),
                'name': repo.get('full_name'),
                'tags': repo.get('topics') or [],
                'priority': 'low',
                'reason': f"recent repo: {repo.get('html_url')}",
                'source_url': repo.get('html_url'),
                'description': repo.get('description') or '',
            }
        )
    return hints


def write_outputs(gaps: list[dict], live: list[dict], catalog: dict) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).astimezone()
    stamp = now.strftime('%Y%m%d')
    report_path = REPORTS_DIR / f'tool-scan-{stamp}.md'

    high = [g for g in gaps if g['priority'] == 'high']
    medium = [g for g in gaps if g['priority'] == 'medium']
    low = [g for g in gaps if g['priority'] == 'low']

    lines = [
        f'# StackBox Tool Scan — {now.isoformat(timespec="seconds")}',
        '',
        f'- Installed tools: **{len(TOOLS)}**',
        f'- Catalog gaps: **{len(gaps)}** (high={len(high)}, medium={len(medium)}, low={len(low)})',
        f'- Sources tracked: {len(catalog.get("sources", []))}',
        '',
        '## High priority missing',
        '',
    ]
    if not high:
        lines.append('_None_')
    for g in high:
        lines.append(f"- `{g['slug_hint']}` — {g['name']} ({', '.join(g.get('tags') or [])})")

    lines += ['', '## Medium priority missing', '']
    if not medium:
        lines.append('_None_')
    for g in medium:
        lines.append(f"- `{g['slug_hint']}` — {g['name']}")

    lines += ['', '## Live GitHub topic pulse', '']
    for item in live[:15]:
        url = item.get('source_url') or ''
        lines.append(f"- {item.get('name')} {url}".rstrip())

    lines += [
        '',
        '## Next actions',
        '',
        '1. Implement high-priority gaps in `toolbox/registry.py` + processors',
        '2. Refresh `toolbox/discovery/community_catalog.json` when new communities appear',
        '3. Keep tools Python/Django-stateless (no database)',
        '',
    ]
    report_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    payload = {
        'scanned_at': now.isoformat(timespec='seconds'),
        'installed_count': len(TOOLS),
        'gaps': gaps,
        'github_pulse': [x for x in live if not str(x.get('slug_hint', '')).startswith('_')],
        'report': str(report_path.relative_to(ROOT)),
    }
    CANDIDATES_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report_path


def maybe_create_issue(gaps: list[dict], report_path: Path) -> None:
    if not gaps:
        print('No gaps; skip issue')
        return
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    if not token or not repo:
        print('GITHUB_TOKEN/GITHUB_REPOSITORY missing; skip issue creation')
        return

    high = [g for g in gaps if g['priority'] == 'high'][:20]
    body_lines = [
        'Automated nightly scan (01:00 Asia/Shanghai).',
        '',
        f'Report: `{report_path.relative_to(ROOT)}`',
        '',
        '### High priority candidates',
        '',
    ]
    for g in high or gaps[:15]:
        body_lines.append(f"- `{g['slug_hint']}` — {g['name']}")
    body_lines += ['', '_Generated by `scripts/nightly_tool_scan.py`_']
    body = '\n'.join(body_lines)

    api = f'https://api.github.com/repos/{repo}/issues'
    payload = json.dumps(
        {
            'title': f'Nightly tool scan: {len(gaps)} candidates ({datetime.now().date().isoformat()})',
            'body': body,
            'labels': ['tool-scan', 'enhancement'],
        }
    ).encode('utf-8')
    req = urllib.request.Request(
        api,
        data=payload,
        method='POST',
        headers={
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {token}',
            'User-Agent': 'StackBox-NightlyScan',
            'Content-Type': 'application/json',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print('Issue created:', data.get('html_url'))
    except urllib.error.HTTPError as exc:
        print('Issue creation failed:', exc.read().decode('utf-8', errors='replace'))


def main() -> int:
    parser = argparse.ArgumentParser(description='Nightly StackBox tool discovery scan')
    parser.add_argument('--live-github', action='store_true', help='Query GitHub search API')
    parser.add_argument('--create-issue', action='store_true', help='Open GitHub issue with gaps')
    args = parser.parse_args()

    catalog = load_catalog()
    gaps = gap_from_catalog(catalog)
    live = github_topic_hints() if args.live_github else []
    report = write_outputs(gaps, live, catalog)
    print(f'Installed: {len(TOOLS)} | Gaps: {len(gaps)} | Report: {report}')
    if args.create_issue:
        maybe_create_issue(gaps, report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
