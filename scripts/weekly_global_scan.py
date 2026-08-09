#!/usr/bin/env python3
"""Weekly global scan across domestic + international tool communities.

Schedule: Sunday 01:00 Asia/Shanghai == Saturday 17:00 UTC
  cron: '0 17 * * 6'

Steps:
1. Load curated CN/INT sources + seed tools
2. Live GitHub searches (CN keywords + international topics)
3. Fetch READMEs from key open-source toolboxes and extract tool lists
4. Categorize gaps vs StackBox registry
5. Write weekly report + weekly_candidates.json
6. Optionally open a GitHub issue
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stackbox.settings')

import django

django.setup()

from toolbox.discovery import lib as disco  # noqa: E402
from toolbox.registry import CATEGORIES, TOOLS  # noqa: E402


def collect_candidates(live: bool = True) -> tuple[list[dict], list[dict], dict]:
    sources_doc = disco.load_json(disco.SOURCES_PATH, {})
    catalog = disco.load_json(disco.CATALOG_PATH, {})
    have, blob = disco.existing_tool_index()

    pool: dict[str, dict] = {}

    def add(item: dict, region: str = 'intl', origin: str = ''):
        slug = disco.normalize(item.get('slug_hint') or item.get('name') or '')
        if not slug or slug.startswith('_'):
            return
        if disco.is_covered(slug, have, blob):
            return
        cat = item.get('category') or disco.guess_category(item.get('name', ''), item.get('tags'), slug)
        prev = pool.get(slug)
        merged = {
            'slug_hint': slug,
            'name': item.get('name') or slug,
            'description': item.get('description') or '',
            'tags': sorted(set((item.get('tags') or []) + ((prev or {}).get('tags') or []))),
            'priority': item.get('priority') or disco.prioritize(item),
            'category': cat,
            'region': item.get('region') or region,
            'sources': sorted(set(((prev or {}).get('sources') or []) + ([origin] if origin else []))),
            'source_url': item.get('source_url') or item.get('html_url') or (prev or {}).get('source_url') or '',
        }
        # keep higher priority if conflict
        rank = {'high': 0, 'medium': 1, 'low': 2}
        if prev and rank.get(prev.get('priority', 'medium'), 9) < rank.get(merged['priority'], 9):
            merged['priority'] = prev['priority']
        pool[slug] = merged

    # 1) seed extras from sources_global
    for item in sources_doc.get('seed_tools_extra', []):
        add(item, region=item.get('region') or 'intl', origin='sources_global.seed')

    # 2) community_catalog known tools
    for item in catalog.get('known_tools', []):
        add(item, region='intl', origin='community_catalog')

    # 3) README mining from github sources
    readme_hits = []
    for src in sources_doc.get('sources', []):
        readme_url = src.get('readme')
        if not readme_url:
            continue
        text = disco.http_get_text(readme_url)
        if not text:
            continue
        tools = disco.extract_tools_from_readme(text, src.get('id') or src.get('name'))
        readme_hits.append({'source': src.get('name'), 'count': len(tools), 'region': src.get('region')})
        for t in tools:
            add(t, region=src.get('region') or 'intl', origin=src.get('id') or src.get('name'))

    # 4) live GitHub searches — pulse only (do not treat whole repos as tools)
    repos = []
    if live:
        for q in sources_doc.get('github_queries', []):
            found = disco.github_search_repos(q['query'], per_page=12)
            for repo in found:
                repos.append({**repo, 'region': q.get('region') or 'intl', 'query': q['query']})
                # If README exists, mine concrete tool names from popular toolboxes
                name = (repo.get('full_name') or '').lower()
                desc = (repo.get('description') or '').lower()
                if any(k in name or k in desc for k in ('toolbox', 'devtools', 'dev-tool', 'utils', '工具', 'cyberchef', 'formatter')):
                    readme_url = f"https://raw.githubusercontent.com/{repo.get('full_name')}/HEAD/README.md"
                    text = disco.http_get_text(readme_url)
                    if text:
                        for t in disco.extract_tools_from_readme(text, repo.get('full_name')):
                            add(t, region=q.get('region') or 'intl', origin=repo.get('full_name'))

    gaps = list(pool.values())
    rank = {'high': 0, 'medium': 1, 'low': 2}
    gaps.sort(key=lambda g: (rank.get(g['priority'], 9), g['category'], g['slug_hint']))
    meta = {
        'readme_hits': readme_hits,
        'repos_sampled': len(repos),
        'sources': sources_doc.get('sources', []),
        'repos': repos[:40],
    }
    return gaps, repos, meta


def write_weekly_report(gaps: list[dict], meta: dict) -> Path:
    disco.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).astimezone()
    stamp = now.strftime('%Y%m%d')
    path = disco.REPORTS_DIR / f'weekly-global-scan-{stamp}.md'

    by_cat: dict[str, list] = defaultdict(list)
    by_region: dict[str, list] = defaultdict(list)
    for g in gaps:
        by_cat[g['category']].append(g)
        by_region[g.get('region') or 'intl'].append(g)

    cat_labels = dict(CATEGORIES)
    cat_labels.update({
        'frontend': '前端视觉',
        'security': '安全校验',
        'oss': '开源仓库',
    })

    lines = [
        f'# StackBox 每周全网扫描 — {now.isoformat(timespec="seconds")}',
        '',
        f'- 已集成工具：**{len(TOOLS)}**',
        f'- 发现缺口：**{len(gaps)}**（high={sum(1 for g in gaps if g["priority"]=="high")} / medium={sum(1 for g in gaps if g["priority"]=="medium")} / low={sum(1 for g in gaps if g["priority"]=="low")}）',
        f'- 国内候选：{len(by_region.get("cn", []))} · 国际候选：{len(by_region.get("intl", []))}',
        f'- 源站/仓库跟踪：{len(meta.get("sources", []))} · GitHub 仓库采样：{meta.get("repos_sampled", 0)}',
        '',
        '## 分门别类（待集成）',
        '',
    ]

    for cat, items in sorted(by_cat.items(), key=lambda x: (-len(x[1]), x[0])):
        label = cat_labels.get(cat, cat)
        lines.append(f'### {label}（{len(items)}）')
        lines.append('')
        for g in items[:40]:
            region = '国内' if g.get('region') == 'cn' else '国际'
            src = ', '.join(g.get('sources') or [])[:80]
            lines.append(
                f"- `{g['slug_hint']}` — **{g['name']}** · {g['priority']} · {region}"
                + (f' · {src}' if src else '')
            )
        if len(items) > 40:
            lines.append(f'- … 另有 {len(items) - 40} 项')
        lines.append('')

    lines += ['## README 挖掘', '']
    if not meta.get('readme_hits'):
        lines.append('_无_')
    for hit in meta.get('readme_hits', []):
        region = '国内' if hit.get('region') == 'cn' else '国际'
        lines.append(f"- {hit['source']}（{region}）：提取 {hit['count']} 条工具线索")

    lines += ['', '## GitHub 脉搏（摘录）', '']
    for repo in meta.get('repos', [])[:20]:
        region = '国内' if repo.get('region') == 'cn' else '国际'
        lines.append(
            f"- [{repo.get('full_name')}]({repo.get('html_url')}) ★{repo.get('stars')} · {region} — {repo.get('description', '')[:100]}"
        )

    lines += [
        '',
        '## 下一步',
        '',
        '1. 优先实现 `priority=high` 且无外部付费依赖的工具',
        '2. 保持 Django 无数据库、瞬时处理',
        '3. 运行 `python scripts/integrate_candidates.py --apply` 尝试模板化集成',
        '',
    ]
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return path


def maybe_issue(gaps: list[dict], report: Path) -> None:
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    if not token or not repo or not gaps:
        print('Skip issue creation')
        return
    high = [g for g in gaps if g['priority'] == 'high'][:25]
    body = [
        '每周全网扫描（国内 + 国外社区/开源仓库）。',
        '',
        f'Report: `{report.relative_to(ROOT)}`',
        f'Gaps: {len(gaps)} | Installed: {len(TOOLS)}',
        '',
        '### High priority',
        '',
    ]
    for g in high or gaps[:20]:
        region = 'CN' if g.get('region') == 'cn' else 'INTL'
        body.append(f"- `{g['slug_hint']}` — {g['name']} [{region}/{g['category']}]")
    body += ['', '_Generated by `scripts/weekly_global_scan.py`_']

    import json
    import urllib.request

    payload = json.dumps(
        {
            'title': f'Weekly global tool scan: {len(gaps)} candidates ({datetime.now().date().isoformat()})',
            'body': '\n'.join(body),
            'labels': ['tool-scan', 'weekly', 'enhancement'],
        }
    ).encode('utf-8')
    req = urllib.request.Request(
        f'https://api.github.com/repos/{repo}/issues',
        data=payload,
        method='POST',
        headers={
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {token}',
            'User-Agent': 'StackBox-WeeklyScan',
            'Content-Type': 'application/json',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print('Issue:', data.get('html_url'))
    except Exception as exc:  # noqa: BLE001
        print('Issue failed:', exc)


def main() -> int:
    parser = argparse.ArgumentParser(description='Weekly CN+INTL tool discovery scan')
    parser.add_argument('--no-live', action='store_true', help='Skip live GitHub/README network calls')
    parser.add_argument('--create-issue', action='store_true')
    args = parser.parse_args()

    gaps, _repos, meta = collect_candidates(live=not args.no_live)
    report = write_weekly_report(gaps, meta)
    now = datetime.now(timezone.utc).astimezone()
    payload = {
        'scanned_at': now.isoformat(timespec='seconds'),
        'scan_type': 'weekly_global',
        'installed_count': len(TOOLS),
        'gap_count': len(gaps),
        'gaps': gaps,
        'by_category': {
            cat: [g['slug_hint'] for g in gaps if g['category'] == cat]
            for cat in sorted({g['category'] for g in gaps})
        },
        'by_region': {
            'cn': [g['slug_hint'] for g in gaps if g.get('region') == 'cn'],
            'intl': [g['slug_hint'] for g in gaps if g.get('region') != 'cn'],
        },
        'report': str(report.relative_to(ROOT)),
        'readme_hits': meta.get('readme_hits'),
    }
    disco.save_json(disco.WEEKLY_PATH, payload)
    # also refresh generic candidates pointer for nightly consumers
    disco.save_json(
        disco.CANDIDATES_PATH,
        {
            'scanned_at': payload['scanned_at'],
            'installed_count': len(TOOLS),
            'gaps': [g for g in gaps if g['priority'] in {'high', 'medium'}][:80],
            'github_pulse': meta.get('repos', [])[:20],
            'report': payload['report'],
            'scan_type': 'weekly_global',
        },
    )
    print(f'Weekly scan done: installed={len(TOOLS)} gaps={len(gaps)} report={report}')
    if args.create_issue:
        maybe_issue(gaps, report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
