# Reproducing this repository

Everything in this history comes from matsne.gov.ge and can be rebuilt from it. The same pages give the same commit hashes.

## What this build used

- Retrieved and built on {{TODAY}}: {{LAWS}} laws, {{VERSIONS}} consolidated publications, and the pages of the amending acts; {{PAGES}} pages in all, each with its sha256 in `data/page-sha256.tsv` (sha256 of that file: {{SUMS_SHA}}).
- {{COMMITS}} commits on `main`: {{ORIGINAL}} original, {{AMENDMENT}} amendment, {{REPEAL}} repeal, {{UNEXPLAINED}} unexplained, and this documentation commit. {{FUTURE}} commits on `future`.
- Issues ({{UNREADABLE}} unreadable publications, {{REPLAY_MISMATCH}} replay mismatches) are in `data/issues.csv`.
- Build scripts (sha256), copied to `tools/build/`:
  - `build.py` {{SHA_BUILD_PY}}
  - `parse_doc.py` {{SHA_PARSE_DOC_PY}}
  - `inforce.py` {{SHA_INFORCE_PY}}
  - `matsne.py` {{SHA_MATSNE_PY}}
  - `fetch_catalogue.py` {{SHA_FETCH_CATALOGUE_PY}}
  - `fetch_versions.py` {{SHA_FETCH_VERSIONS_PY}}
  - `docs.py` {{SHA_DOCS_PY}}

## Steps


```sh
cd tools/build
python fetch_catalogue.py               # search listing (group 1000003, "law"; 11 pages) + each law's page -> .cache/
python fetch_versions.py                # every ?publication=N page and every amending act's page -> .cache/
python fetch_versions.py --sums          # .cache/sha256.tsv
python build.py ../../../georgia-law-rebuilt --today {{TODAY}}
```

`--today` dates the documentation commit and splits `main` from `future`; it is required, so a rebuild never depends on the day it is run. The builder refuses to write into a non-empty folder that is not an earlier build, and keeps `origin` when it rebuilds one.

Matsne adds publications as laws change, so a later fetch gives a longer history. To rebuild this exact history, use pages whose sha256 match `data/page-sha256.tsv`.

## Sources

- Listing: `https://matsne.gov.ge/ka/document/search?type=main&group=1000003&sort=signingDate_asc&limit=100&page=N`
- Law page: `https://matsne.gov.ge/ka/document/view/<id>` (latest publication, its list of publications and its list of changes)
- Publication: `https://matsne.gov.ge/ka/document/view/<id>?publication=<n>`
- Amending act: `https://matsne.gov.ge/ka/document/view/<act id>`

## robots.txt and bulk data

- `https://matsne.gov.ge/robots.txt` (checked 28 October 2026) has one group, `User-agent: *`, with `Crawl-delay: 10` and `Disallow` lines for Drupal system paths (`/admin/`, `/user/...`, `/search/`, `/node/add/` and the like). It names no AI crawler (ClaudeBot, Claude-Web, anthropic-ai, GPTBot or others), and nothing in it disallows `/ka/document/view/` or `/ka/document/search`, the only paths this build fetches.
- Matsne offers no bulk download or API for its texts (also recorded in the World Law Sources register), so the pages were read one by one.

## Fetch rate

Matsne's robots.txt sets `Crawl-delay: 10`. **This build's one full fetch did not obey it**: it ran on 28 October 2026 with 8 to 10 requests in parallel (about 8 pages a second; about 25,000 pages, gzip-compressed transfer), before the rule to obey crawl delays was adopted across these repositories. Matsne's firewall refused about 1 request in 250 with an "Access Denied" page, which was detected and retried. The scripts as shipped now pace every request to one per 10 seconds across all threads (`CRAWL_DELAY` in `matsne.py`; `--workers` defaults to 1). At that rate a full fetch from nothing takes about 70 hours; a rebuild from the cache makes no requests.

## Decisions

- **Which documents:** Matsne's search with "only main (consolidated)" documents and document type "law" (კანონი), in force and expired. This is the Constitution, constitutional and organic laws, codes, laws, Parliament's rules of procedure, laws of the autonomous republics, and a few Soviet-era acts Matsne files in that group.
- **Which text:** the Georgian publication pages. English translations are not used.
- **Units:** a line `მუხლი N. ...` starts an article; lines starting `თავი`, `კარი`, `წიგნი`, `ნაწილი`, `განყოფილება` (and the short title lines under them) are headings of the next article. Each block element of the page is one line. Text before the first article is `title.md`; the signature block after the last article is `signature.md`; a printed list of changes (`შეტანილი ცვლილებები`) is `changes-listed.md`.
- **Normalised away:** whitespace (including non-breaking spaces), curly quotes, dashes, soft hyphens and zero-width characters; a file whose text differs from the previous publication only in whitespace keeps the earlier text.
- **Crediting:** publication N is change N in Matsne's list (the numbers and adoption dates match for every law in this build), credited to the act Matsne links.
- **Dates:** the act's in-force article (see README), noon Tbilisi time (+04:00). Before 1970, 1970-01-01 plus one second per commit, in order. Commits after `--today` are on `future`.
- **Order:** by in-force date; on one date, original texts first, then amendments by publication date and act id, then unexplained changes.
- **Out-of-order changes:** re-applied by a three-way line merge; otherwise held back to the earlier-published act's commit, and labelled.
- **Repeals:** an expired law whose last listed change is titled as a repeal (ძალადაკარგულად), or whose last publication newly says ძალადაკარგულია, has its files deleted in that change's commit.

## What the AI did

Claude Code with Claude Opus 5.5 (`claude-opus-5-5`) wrote the scripts, chose the rules above and ran the build and the checks. No AI model writes or changes legal text, and no model runs at fetch, parse or git-build time: the commit messages are built by code from Matsne's metadata.
