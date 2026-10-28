# Georgian law, change by change

The laws of Georgia as a git repository: 948 acts from [Matsne](https://matsne.gov.ge), the Legislative Herald of Georgia, the official publisher of Georgian legislation. They are every document Matsne lists as a main (consolidated) document in its "law" group (კანონი), in force or not: 796 laws; 57 laws of the autonomous republics (Adjara, Abkhazia); 40 organic laws; 36 codes; 12 other acts in the law group (Soviet-era decrees and similar); 4 rules of procedure (reglament) of Parliament; 2 constitutions (1995, and the 1921 Constitution as Matsne publishes it); 1 constitutional laws. There is one folder per law and one file per article. Each change is a commit credited to the act that made it, dated the day that act took effect, at noon Tbilisi time. The text is the Georgian original, as Matsne publishes it.

The record runs from 1921-02-21 to 2026-10-26 in 11818 commits on `main`, built from 12954 consolidated publications. 58 further commits, for changes that have been published but take effect after 2026-10-28, are on the branch `future`, which is never merged.

Sub-legislative acts (decrees, resolutions, orders: about 50,000 more documents on Matsne) are not included yet.

## A lawyer's questions as git commands

Each law's folder is `<kind>/<Matsne id>/`, listed with its title in [`laws.csv`](laws.csv): for example `constitution/30346` (the Constitution), `code/1043717` (the Tax Code), `code/31702` (the Civil Code), `code/16426` (the Criminal Code).

| Question | Command |
| --- | --- |
| What did article 37 of the Constitution say on 1 January 2019? | `python tools/in_force_on.py 2019-01-01 constitution/30346 37` |
| The whole of a law on a date | `python tools/in_force_on.py 2019-01-01 constitution/30346` |
| The same, counting changes already published but not yet in force | `python tools/in_force_on.py --future 2027-01-01 code/1043717 1` |
| Which act last changed each line of an article? | `git blame code/31702/1.md` |
| Every change to an article, with the act behind it | `git log -p code/1043717/12-1.md` |
| The words that changed, not whole lines | `git log -p --word-diff code/1043717/12-1.md` |
| Everything one act changed | `git log --author='№6500-რს' --stat` |
| Every act that changed a law, in order | `git log --format='%(trailers:key=In-force,valueonly,separator=) %an' -- code/1043717` |
| Commits on or before a day, without time-zone surprises | `git log --before='2019-01-01T23:59:59+04:00' -1 -- constitution/30346` |
| What no act is credited with | `git log --grep='Kind: unexplained'` |
| The list of laws, and of amending acts with their in-force dates | [`laws.csv`](laws.csv), [`data/acts.csv`](data/acts.csv) |

In PowerShell, `git show $(...):path` splits into two arguments; use `$r = git rev-list -1 main -- code/31702; git show "$($r):code/31702/1.md"`.

Article files are named by number: `12-1.md` is article 12¹ (`მუხლი 12¹`). A second article with a number already used in the same law (an annex, a quoted text) gets `~2`. Each file starts with any book, part or chapter headings above the article as `##` lines, then the article heading as `# მუხლი 12¹. ...`, then one line per paragraph. Matsne prints, under amended text, a note naming the act that last changed it (`საქართველოს 2019 წლის 28 ივნისის კანონი №4906 - ვებგვერდი, 04.07.2019წ.`); these notes are kept where they appear, as `- ` lines. `title.md` holds the title and preamble, `signature.md` the signature block, and `changes-listed.md` the list of changes some older laws print at their end.

## The dates, and which one we use

Matsne publishes each law as a series of consolidated publications. Publication N is the text after the Nth change in the law's list of changes, and Matsne dates it by the day the amending act was **adopted**. That is neither the day it was published nor the day it took effect.

**Commits are dated by the day the change took effect.** That date is read from the amending act's own in-force article on Matsne:

- "ეს კანონი ამოქმედდეს გამოქვეყნებისთანავე" (on publication): the publication date. 6003 commits.
- "გამოქვეყნებიდან მე-15 დღეს" (on the Nth day from publication): the publication date plus N days, because a period in days runs from the day after the event. 1215 commits.
- A date in the act ("2021 წლის 1 მარტიდან"): that date. 2646 commits.
- An event rather than a date (another law taking effect, a President's oath), or no in-force article found: the publication date, labelled `In-force-basis: published (...)` with the act's words quoted. 1006 commits.

Every amendment commit carries `In-force:`, `In-force-basis:`, `In-force-rule:` (the act's words), `Adopted:` and `Published:`. Where parts of an act take effect on other dates ("1. ეს კანონი, გარდა ამ კანონის პირველი მუხლისა, ამოქმედდეს გამოქვეყნებისთანავე. 2. ამ კანონის პირველი მუხლი ამოქმედდეს 2025 წლის 1 სექტემბრიდან."), the commit is dated by the act's main clause and the other parts are listed as `In-force-part:` lines. **The text in such a commit includes those parts from the main date**, because Matsne's consolidated text does not separate them.

Acts take effect out of the order they were published (an act adopted in November may take effect on 1 January, after an act adopted in December that took effect at once). Changes are applied in the order they took effect. Where a later-published change touches lines that an earlier-published, not yet effective change also touches, it is re-applied to the text then in force by a three-way line merge. Where that is impossible, the change is held back until the earlier act takes effect and appears in its commit; both commits say so (`Held-back:` and `Includes-held-back:`, 1829 files in all).

An act that took effect before the law it amends (a law amended between adoption and entry into force) is dated by the day the law took effect, with the act's own date as `In-force-act:`.

The first commit of each law (`Kind: original`) is Matsne's publication 0: the law as adopted, dated by its own in-force article.

**Git cannot store dates before 1970.** Laws from before then (Soviet-era codes and decrees) are committed on 1970-01-01, one second apart and in order. The real date is in the `In-force:` trailer, which `tools/in_force_on.py` reads.

## What "author" means

The author of a commit is the act that made the change, as Matsne lists it, at an address that cannot exist: `საქართველოს კანონი №4906 (28.06.2019) <law-4906-20190628@matsne.invalid>`. The name is the act's type, number and adoption date; the address is its number (transliterated) and adoption date. So `git blame` names, for each line, the act that last wrote it. The first commit of a law is authored by the law itself.

A change is credited on Matsne's own word: publication N of a law is the text after change N in its list of changes, which links the amending act (`Evidence: matsne`). In 10769 commit parts the changed text also gains Matsne's printed note naming that act's number (`Evidence: matsne + note`); in 461 it does not (deletions leave no note, and older publications print fewer notes). A difference between two publications for which Matsne lists no act would be a commit by the publisher labelled `Kind: unexplained`; there are 0.

In total: 947 original texts, 10583 amendment commits and 287 repeals, by 10866 amending acts.

## What it does not show

- Sub-legislative acts (Presidential decrees, Government resolutions, ministerial orders), international treaties and court decisions, except where they appear as amending acts. The Constitutional Court's decisions that strike down provisions are credited as the act that changed the text.
- English translations. Matsne publishes unofficial English translations of many laws; only the Georgian text is authoritative and only it is used here.
- Which parts of an act took effect later than its main clause, beyond the `In-force-part:` lines (see above).
- Transitional and saving rules, which are in the amending acts at each commit's `Source:` link.
- Repeals that Matsne records without a change in the law's list. 441 laws are no longer in force on Matsne; their files are deleted on the day the repealing act took effect where Matsne lists that act as the law's last change, and are otherwise left as last published (see `status` in `laws.csv`).
- Footnotes, tables laid out as images, and formatting. Tables are kept as rows with cells separated by `|`.
- Publications that could not be read: 0, listed in [`data/issues.csv`](data/issues.csv).

This is a research aid. Only the texts published by the Legislative Herald of Georgia are official, and Matsne's consolidated versions, and so this repository, are not the official publication of the amending acts.

## How it is checked

- `tools/in_force_on.py` gives, for sampled articles and dates, the same text as Matsne's own consolidated publication for that date (see REPRODUCE.md).
- Replaying every change of a law gives its latest publication on Matsne, for all but 0 laws (listed in `data/issues.csv`).
- Every commit's trailers parse with `git interpret-trailers --parse`. `main` has no merges, and its dates never go backwards or past the build day.
- The build is deterministic: from the same pages it gives the same commit hashes. The sha256 of every page is in [`data/page-sha256.tsv`](data/page-sha256.tsv). See [`REPRODUCE.md`](REPRODUCE.md).

## How it is built

`fetch_catalogue.py` reads Matsne's search listing for every main document in the "law" group and each law's page, which lists its consolidated publications and its changes with links to the amending acts. `fetch_versions.py` downloads every publication and every amending act. `parse_doc.py` reads each publication into a title and articles. `inforce.py` reads each act's in-force article. `build.py` compares consecutive publications article by article, credits and dates each change as above, and writes the history with one streamed `git fast-import`. No AI model takes part in building or checking it.

## Licence

Source: LEPL Legislative Herald of Georgia (სსიპ "საქართველოს საკანონმდებლო მაცნე"), https://matsne.gov.ge. The texts were converted to one file per article and arranged as commits, and the wording was not changed. Under the Law of Georgia on Copyright and Related Rights (article 8), official documents such as laws and other normative acts are not objects of copyright; Matsne's site carries the notice "ყველა უფლება დაცულია" (all rights reserved) for the site itself. **Check Matsne's terms before this repository is made public.** Lexifina's own contributions (the tools, the arrangement and the commit messages) are CC0. See [`LICENSE`](LICENSE).
