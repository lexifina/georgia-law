"""Read one Matsne document page (a consolidated publication) into units: a title page and one unit per article.

The text is the page's `maindoc` block. Each block element (paragraph, div, table row, list item) is one line.
An article starts at a line `მუხლი N. heading` (also `მუხლი N¹`, `მუხლი 12⁴`). Lines `თავი ...` (chapter), `კარი ...`
(part), `წიგნი ...` (book), `ნაწილი ...`, `განყოფილება ...` and the centred titles after them are headings, kept as
`##` lines in the next article. The italic notes Matsne prints under amended text (`საქართველოს 2017 წლის 13
ოქტომბრის კანონი №1324 - ვებგვერდი, 19.10.2017წ.`) are kept as `- ` lines where they appear.
"""
import html
import re

ART = re.compile(r'^მუხლი\s+(\d+(?:[\s\-–]*[¹²³⁴⁵⁶⁷⁸⁹⁰]+|\s+\d+(?=\s*\.))?)\s*(?:[\.\s]\s*(.*))?$')
HEAD = re.compile(r'^(თავი|კარი|წიგნი|ნაწილი|განყოფილება|ქვეთავი|ქვეკარი|ქვეგანყოფილება)\b')
SUP = str.maketrans('¹²³⁴⁵⁶⁷⁸⁹⁰', '1234567890')
NOTE = re.compile(r'(\d{2,4}\s?\d{0,2}\s+წლის\s+\d{1,2}\s+\S+\s+(?:\S+\s+){0,6}?(?:კანონი|კანონით|დადგენილება|დეკრეტი|ბრძანებულება|'
                  r'რეგლამენტი|გადაწყვეტილება)\S*\s*(?:№|N)\s*\S+.*(?:ვებგვერდი|სსმ|უწყებები|გაზეთი|მაცნე)'
                  r'.*\d{2}\.\d{2}\.\d{4})')
SIGN = re.compile(r'^(საქართველოს\s+(პრეზიდენტი|სახელმწიფოს\s+მეთაური|პარლამენტის\s+თავმჯდომარე)|.*(უზენაესი\s+საბჭოს|პარლამენტის)\s+თავმჯდომარე)')
BLOCK = re.compile(r'</?(?:p|div|tr|li|h[1-6]|table|tbody|thead|ul|ol|br|blockquote|center)\b[^>]*>', re.I)


def lines_of(page: str) -> list[str]:
    i = page.find('id="maindoc"')
    i = page.find('>', i) + 1
    j = page.find('document-changes-bottom', i)
    j = page.rfind('<', i, j) if j > 0 else len(page)
    body = re.sub(r'[\r\n\t]+', ' ', page[i:j])
    body = re.sub(r'<(style|script)\b.*?</\1>', ' ', body, flags=re.S | re.I)
    body = re.sub(r'<!--.*?-->', ' ', body, flags=re.S)
    # Footnote and annotation markers ('#' links to treaties) are not text.
    body = re.sub(r'<a[^>]*class="urlWithAnnotation"[^>]*>.*?</a>', ' ', body, flags=re.S)
    body = re.sub(r'</t[dh]>', ' | ', body, flags=re.I)
    body = BLOCK.sub('\n', body)
    body = re.sub(r'<sup>\s*(\d+)\s*</sup>', lambda m: m.group(1).translate(str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹')),
                  body, flags=re.I)
    body = re.sub(r'<[^>]+>', '', body)
    body = html.unescape(body)
    out = []
    for l in body.split('\n'):
        l = norm(l)
        l = re.sub(r'^(\|\s*)+|(\s*\|)+$', '', l).strip()
        if l and l != '|':
            out.append(l)
    return out


def norm(s: str) -> str:
    s = s.replace('\xa0', ' ').replace('​', '').replace('­', '').replace('﻿', '')
    s = s.replace('“', '"').replace('”', '"').replace('„', '"').replace('’', "'").replace('‘', "'")
    s = s.replace('–', '-').replace('—', '-')
    return re.sub(r'\s+', ' ', s).strip()


def art_id(raw: str) -> str:
    """'12¹' -> '12-1', '12' -> '12'."""
    raw = raw.strip()
    m = re.match(r'(\d+)[\s\-]*([¹²³⁴⁵⁶⁷⁸⁹⁰]+)$', raw)
    if m:
        return f'{m.group(1)}-{m.group(2).translate(SUP)}'
    m = re.match(r'(\d+)\s+(\d+)$', raw)
    if m:
        return f'{m.group(1)}-{m.group(2)}'
    return re.sub(r'\D', '', raw) or raw


def is_note(l: str) -> bool:
    return bool(NOTE.search(l)) and len(l) < 400


def parse(page: str) -> dict:
    lines = lines_of(page)
    title: list[str] = []
    units: list[dict] = []
    pending: list[str] = []   # headings waiting for the next article
    cur = None
    seen: dict[str, int] = {}
    for l in lines:
        m = ART.match(l)
        if m and (len(l) < 600):
            uid = art_id(m.group(1))
            if uid in seen:            # a second article with the same number (an annex, a quoted law)
                seen[uid] += 1
                uid = f'{uid}~{seen[uid]}'
            else:
                seen[uid] = 1
            cur = {'id': uid, 'heading': list(pending), 'lines': [l]}
            units.append(cur)
            pending = []
            continue
        if HEAD.match(l) and len(l) < 300:
            pending.append(l)
            continue
        if pending and cur is not None and len(l) < 300 and not is_note(l) and not re.match(r'^\d', l) \
                and len(pending) < 4 and not l.endswith(('.', ';', ':')):
            pending.append(l)      # the centred title under a chapter/part heading
            continue
        if cur is None:
            title.extend(pending)
            pending = []
            title.append(l)
        else:
            if pending:            # headings with no article after them (e.g. an annex): keep them in place
                cur['lines'].extend(pending)
                pending = []
            cur['lines'].append(l)
    if pending:
        (cur['lines'] if cur else title).extend(pending)
    listed: list[str] = []
    holder = units[-1]['lines'] if units else title
    for k, l in enumerate(holder):
        if l.startswith('შეტანილი ცვლილებები') or l.startswith('შეტანილი ცვლილება'):
            listed = holder[k:]
            del holder[k:]
            break
    sign: list[str] = []
    if units:
        last = units[-1]['lines']
        for k in range(max(1, len(last) - 12), len(last)):
            if SIGN.match(last[k]):
                sign = last[k:]
                del last[k:]
                break
    return {'title': title, 'units': units, 'signature': sign, 'listed': listed}


def unit_text(u: dict) -> str:
    out = [f'## {h}' for h in u['heading']]
    first, *rest = u['lines']
    out.append(f'# {first}')
    for l in rest:
        out.append(f'- {l}' if is_note(l) else l)
    return '\n'.join(out) + '\n'


def title_text(lines: list[str]) -> str:
    return '\n'.join(f'- {l}' if is_note(l) else l for l in lines) + '\n'
