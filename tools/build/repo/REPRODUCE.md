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
  - `docs.py` {{SHA_DOCS_PY}}

## Steps


```sh
cd tools/build
# the retrieved pages (sha256 in data/page-sha256.tsv), where build.py reads them
python build.py ../../../georgia-law-rebuilt --today {{TODAY}}
```

`--today` dates the documentation commit and splits `main` from `future`; it is required, so a rebuild never depends on the day it is run. The builder refuses to write into a non-empty folder that is not an earlier build, and keeps `origin` when it rebuilds one.

Matsne adds publications as laws change, so a later retrieval gives a longer history. To rebuild this exact history, use pages whose sha256 match `data/page-sha256.tsv`.

## Sources

- Listing: `https://matsne.gov.ge/ka/document/search?type=main&group=1000003&sort=signingDate_asc&limit=100&page=N`
- Law page: `https://matsne.gov.ge/ka/document/view/<id>` (latest publication, its list of publications and its list of changes)
- Publication: `https://matsne.gov.ge/ka/document/view/<id>?publication=<n>`
- Amending act: `https://matsne.gov.ge/ka/document/view/<act id>`

## Bulk data

- Matsne offers no bulk download or API for its texts.

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
