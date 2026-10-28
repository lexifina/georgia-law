"""When an amending act took effect, read from its own text on Matsne.

Georgian acts end with an in-force article, nearly always in one of these forms:
    ეს კანონი ამოქმედდეს გამოქვეყნებისთანავე.                    on publication
    ეს კანონი ამოქმედდეს გამოქვეყნებიდან მე-15 დღეს.              on the 15th day from publication
    ეს კანონი ამოქმედდეს 2021 წლის 1 მარტიდან.                    from a date
    1. ეს კანონი, გარდა ამ კანონის პირველი მუხლისა, ამოქმედდეს გამოქვეყნებისთანავე.
    2. ამ კანონის პირველი მუხლი ამოქმედდეს 2025 წლის 1 სექტემბრიდან.   a part, from another date
Quoted lines (the text an act inserts into another law) are skipped. The main clause ("ეს კანონი", this law) gives
the commit date; the other clauses are kept as `In-force-part:` trailers. A rule that is not a date (an event, such
as another law taking effect or an oath) falls back to the publication date, with the rule quoted in the commit.

"On the Nth day from publication" is taken as publication date + N days (a period in days starts the day after the
event).
"""
import re
from datetime import date, timedelta

MONTHS = [('იანვ', 1), ('თებერვ', 2), ('მარტ', 3), ('აპრილ', 4), ('მაის', 5), ('ივნის', 6), ('ივლის', 7),
          ('აგვისტ', 8), ('სექტემბ', 9), ('ოქტომბ', 10), ('ნოემბ', 11), ('დეკემბ', 12)]
VERB = re.compile(r'(ამოქმედდეს|ამოქმედდება|ძალაში\s+შევიდეს|ძალაში\s+შედის|შევიდეს\s+ძალაში)')
DATE = re.compile(r'(\d{4})\s+წლის\s+(\d{1,2})\s+([^\s,.;]+)')
NTH = re.compile(r'გამოქვეყნებიდან\s+(?:მე-)?(\d+)(?:-ე)?\s+დღე')


def month(word: str) -> int | None:
    for stem, n in MONTHS:
        if word.startswith(stem):
            return n
    return None


def when(rule: str, published: str) -> tuple[str | None, str]:
    """(ISO date or None, basis) for the words after the verb."""
    if re.search(r'გამოქვეყნები(სთანავე|სთანვე|ს\s+დღიდან|ს\s+დღეს)', rule) or \
            re.search(r'გამოქვეყნებისთანავე', rule):
        return published or None, 'on publication'
    m = NTH.search(rule)
    if m and published:
        d = date.fromisoformat(published) + timedelta(days=int(m.group(1)))
        return d.isoformat(), f'day {m.group(1)} from publication'
    for m in DATE.finditer(rule):
        mo = month(m.group(3))
        if mo:
            try:
                return date(int(m.group(1)), mo, int(m.group(2))).isoformat(), 'date in the act'
            except ValueError:
                pass
    return None, 'not a date'


def parse(lines: list[str], published: str) -> dict:
    clauses = []
    for l in lines:
        s = l.strip()
        if not s or s[0] in '"„“\'' or len(s) > 700:
            continue
        m = VERB.search(s)
        if not m:
            continue
        subj = s[:m.start()]
        rule = s[m.end():]
        main = bool(re.search(r'(^|[\s.])ეს\s+(კანონი|კოდექსი|ორგანული|კონსტიტუციური|დადგენილება|დეკრეტი|ბრძანებულება|რეგლამენტი)', subj)) \
            and 'ამ კანონის' not in subj.split('გარდა')[0]
        part = 'ამ ' in subj or 'მუხლ' in subj or 'პუნქტ' in subj or 'ნაწილ' in subj
        if not main and not part:
            continue
        d, basis = when(rule, published)
        clauses.append({'main': main, 'except': 'გარდა' in subj, 'date': d, 'basis': basis, 'words': s})
    mains = [c for c in clauses if c['main']]
    # The act's own in-force article comes last; if a main clause appears more than once take the last.
    main = mains[-1] if mains else None
    parts = [c for c in clauses if not c['main'] and c['date']]
    if main and main['date']:
        return {'date': main['date'], 'basis': main['basis'], 'words': main['words'], 'parts': parts}
    if main:
        return {'date': published or None, 'basis': 'published (in-force rule is not a date)',
                'words': main['words'], 'parts': parts}
    if parts and len({p['date'] for p in parts}) == 1:
        return {'date': parts[0]['date'], 'basis': parts[0]['basis'], 'words': parts[0]['words'], 'parts': []}
    return {'date': published or None, 'basis': 'published (no in-force article found)', 'words': '', 'parts': parts}
