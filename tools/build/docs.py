"""README, REPRODUCE.md, LICENSE, corpus.json, laws.csv, data/ and tools for the Georgia law repository (called by
build.py)."""
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
REPO_FILES = HERE / 'repo'
CACHE = HERE / '.cache'
SCRIPTS = ('build.py', 'parse_doc.py', 'inforce.py', 'matsne.py', 'fetch_catalogue.py', 'fetch_versions.py', 'docs.py')

KIND_NAMES = {'constitution': 'constitutions (1995, and the 1921 Constitution as Matsne publishes it)', 'constitutional-law': 'constitutional laws',
              'organic-law': 'organic laws', 'code': 'codes', 'law': 'laws',
              'rules-of-procedure': 'rules of procedure (reglament) of Parliament',
              'autonomous-republic': 'laws of the autonomous republics (Adjara, Abkhazia)',
              'other': 'other acts in the law group (Soviet-era decrees and similar)'}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def render(laws: list[dict], commits: list[dict], issues: list[dict], acts: dict, today: str) -> dict[str, bytes]:
    main = [c for c in commits if c['date'] <= today]
    future = [c for c in commits if c['date'] > today]
    kinds = Counter(c['kind'] for c in main)
    authors = {c['act']['id'] for c in main if c['kind'] in ('amendment', 'repeal')}
    basis = Counter(c['act']['inforce']['basis'] for c in main if c['kind'] in ('amendment', 'repeal'))
    held = sum(len(p.get('held_back', ())) for c in commits for p in c['parts'])
    ev = Counter(p['evidence'] for c in main if c['kind'] == 'amendment' for p in c['parts'])
    by_kind = Counter(l['kind'] for l in laws if l['versions'])
    built = [l for l in laws if l['versions']]
    versions = sum(len(l['versions']) for l in built)
    first = min(c['date'] for c in main) if main else ''
    last = max(c['date'] for c in main) if main else ''
    unread = [i for i in issues if i['issue'] not in ('replayed text differs from the last publication',)]
    replay = [i for i in issues if i['issue'] == 'replayed text differs from the last publication']

    out = io.StringIO()
    w = csv.writer(out, lineterminator='\n')
    w.writerow(['id', 'kind', 'title', 'type', 'number', 'adopted', 'published', 'status', 'publications',
                'changes', 'path', 'source'])
    for l in built:
        w.writerow([l['id'], l['kind'], l['title'], l.get('type') or '', l.get('number') or '', l.get('adopted') or '',
                    l.get('published') or '', l['status'], len(l['versions']), len(l['changes']),
                    f"{l['kind']}/{l['id']}/", f"https://matsne.gov.ge/ka/document/view/{l['id']}"])
    laws_csv = out.getvalue()

    a = io.StringIO()
    w = csv.writer(a, lineterminator='\n')
    w.writerow(['act', 'number', 'type', 'adopted', 'published', 'in_force', 'basis', 'rule', 'source'])
    for k in sorted(acts):
        x = acts[k]
        w.writerow([x['id'], x['number'], x['type'], x['adopted'], x['published'], x['inforce']['date'],
                    x['inforce']['basis'], x['inforce'].get('words', ''), f"https://matsne.gov.ge/ka/document/view/{x['id']}"])

    iss = io.StringIO()
    w = csv.writer(iss, lineterminator='\n')
    w.writerow(['law', 'publication', 'issue'])
    for i in issues:
        w.writerow([i['law'], i['publication'], i['issue']])

    stats = {
        'today': today, 'laws': len(built), 'versions': versions,
        'commits': len(main) + 1, 'future': len(future), 'original': kinds['original'],
        'amendment': kinds['amendment'], 'repeal': kinds['repeal'], 'unexplained': kinds['unexplained'],
        'amending_acts': len(authors), 'first': first, 'last': last, 'unreadable': len(unread),
        'replay_mismatch': len(replay), 'held_back': held,
        'evidence_note': ev['matsne + note'], 'evidence_list': ev['matsne'],
        'basis': dict(basis), 'by_kind': dict(by_kind),
        'active': sum(1 for l in built if l['status'] == 'active'),
        'expired': sum(1 for l in built if l['status'] != 'active'),
    }
    stats['basis_publication'] = basis.get('on publication', 0)
    stats['basis_day'] = sum(v for k, v in basis.items() if k.startswith('day '))
    stats['basis_date'] = basis.get('date in the act', 0)
    stats['basis_fallback'] = sum(v for k, v in basis.items() if k.startswith(('published', 'adopted')))
    kinds_line = '; '.join(f'{v} {KIND_NAMES.get(k, k)}' for k, v in sorted(by_kind.items(), key=lambda x: -x[1]))
    stats['kinds_line'] = kinds_line

    readme = (REPO_FILES / 'README.md').read_text('utf-8')
    reproduce = (REPO_FILES / 'REPRODUCE.md').read_text('utf-8')
    for k, v in stats.items():
        if isinstance(v, (dict, list)):
            continue
        readme = readme.replace('{{' + k.upper() + '}}', str(v))
        reproduce = reproduce.replace('{{' + k.upper() + '}}', str(v))
    for name in SCRIPTS:
        reproduce = reproduce.replace('{{SHA_' + name.upper().replace('.', '_') + '}}', _sha(HERE / name))
    sums = (CACHE / 'sha256.tsv').read_text('utf-8') if (CACHE / 'sha256.tsv').exists() else ''
    reproduce = reproduce.replace('{{PAGES}}', str(sums.count('\n')))
    reproduce = reproduce.replace('{{SUMS_SHA}}', hashlib.sha256(sums.encode()).hexdigest())

    corpus = {
        'corpus': 'ge/national/acts',
        'name': 'Legislation of Georgia (laws, from Matsne)',
        'label': 'Georgia: laws',
        'record_to': last,
        'record_note': 'every main document in Matsne\'s "law" group (Constitution, constitutional and organic laws, '
                       'codes, laws, autonomous-republic laws), in force or expired; sub-legislative acts not included; '
                       'changes published but in force after the build day are on the future branch',
        'in_force_trailer': 'In-force',
        'baseline_trailer': 'In-force',
        'has_future_branch': True,
        'future_branch': 'future',
        'laws': dict(by_kind),
        'history_from': first,
        'built': today,
        'language': 'ka',
        'dates': {'commit': 'in-force (from the amending act\'s own in-force article)',
                  'other_trailers': ['Adopted', 'Published', 'In-force-part'],
                  'time': '12:00 Asia/Tbilisi (+04:00)', 'before_1970': 'clamped to 1970-01-01',
                  'future': 'branch future, never merged'},
        'author': {'amendment': 'the amending act', 'original': 'the law itself',
                   'unexplained': 'Legislative Herald of Georgia (matsne.gov.ge)', 'evidence_trailer': 'Evidence'},
        'scope': {
            'trailer': 'Applies',
            'groups': 'any one line',
            'conditions': 'all of a line',
            'when_absent': 'no scope note extracted for Georgia; transitional provisions are in the amending act at the Source link',
            'default_reach': {
                'rule': 'no retroactive effect unless the act says so',
                'meaning': 'a normative act has no retroactive force unless it expressly provides so; a law that '
                           'establishes or aggravates liability never has retroactive force',
                'authority': 'Constitution of Georgia, art. 31(5) (2017 text); Law of Georgia on Normative Acts, art. 24',
                'decided_here': False,
            },
        },
        'citation': {
            'file': r'^([a-z-]+/\d+)/(\d+)\.md$',
            'cites': r'(?<![\d¹²³⁴⁵⁶⁷⁸⁹⁰])(?:მუხლი\s+{n}(?![\d¹²³⁴⁵⁶⁷⁸⁹⁰])|(?:მე-)?{n}(?![\d¹²³⁴⁵⁶⁷⁸⁹⁰])(?:-ე)?\s+მუხლ)',
            'note': 'forms "მუხლი N", "მე-N მუხლი", "N-ე მუხლი"; articles with a superscript number (file 12-1.md = '
                    'article 12¹) are not matched by the file rule; the first article is written "პირველი მუხლი" '
                    'and lists ("120-ე და 121-ე მუხლები") match only their last number; citations are within the same law',
        },
        'tool': 'tools/in_force_on.py',
    }

    files = {
        'corpus.json': (json.dumps(corpus, indent=2, ensure_ascii=False) + '\n').encode('utf-8'),
        'README.md': readme.encode('utf-8'),
        'REPRODUCE.md': reproduce.encode('utf-8'),
        'LICENSE': (REPO_FILES / 'LICENSE').read_bytes(),
        'laws.csv': laws_csv.encode('utf-8'),
        'data/acts.csv': a.getvalue().encode('utf-8'),
        'data/issues.csv': iss.getvalue().encode('utf-8'),
        'data/stats.json': (json.dumps(stats, indent=1, sort_keys=True, ensure_ascii=False) + '\n').encode('utf-8'),
        'data/page-sha256.tsv': sums.encode('utf-8'),
        'tools/in_force_on.py': (REPO_FILES / 'tools' / 'in_force_on.py').read_bytes(),
    }
    for name in SCRIPTS:
        files[f'tools/build/{name}'] = (HERE / name).read_bytes()
    for name in ('README.md', 'REPRODUCE.md', 'LICENSE'):
        files[f'tools/build/repo/{name}'] = (REPO_FILES / name).read_bytes()
    return files
