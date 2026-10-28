"""Print a Georgian law, or one article of it, as it stood on a date.

    python tools/in_force_on.py 2019-01-01 constitution/30346          # every file of the Constitution on that day
    python tools/in_force_on.py 2019-01-01 constitution/30346 37       # article 37
    python tools/in_force_on.py 2016-01-01 code/1043717 12-1           # article 12¹ of the Tax Code
    python tools/in_force_on.py --future 2027-01-01 code/1043717 1     # include changes not yet in force

The folder of each law is in laws.csv. Reads the `In-force:` trailer (the real date; commit dates before 1970 are
clamped), so it is right for any day. Standard library only.
"""
import subprocess
import sys


def git(*args: str) -> str:
    return subprocess.run(['git', *args], capture_output=True, text=True, encoding='utf-8', check=True).stdout


def commit_on(day: str, path: str, ref: str) -> str | None:
    """The last commit on or before `day` that touched `path`."""
    fmt = '%H%x1f%(trailers:key=In-force,valueonly,separator=)'
    for line in git('log', '--first-parent', f'--format={fmt}', ref, '--', path).splitlines():
        h, d = (line.split('\x1f') + [''])[:2]
        d = d.strip()[:10]
        if d and d <= day:
            return h
    return None


def main() -> None:
    args = sys.argv[1:]
    ref = 'main'
    if args and args[0] == '--future':
        ref, args = 'future', args[1:]
    if len(args) < 2:
        sys.exit(__doc__)
    day, law = args[0], args[1].strip('/')
    unit = args[2] if len(args) > 2 else None
    path = f'{law}/{unit}.md' if unit else law
    h = commit_on(day, path, ref)
    if not h:
        sys.exit(f'{path}: no text on or before {day} (not yet adopted, not in this record, or no such article)')
    names = git('ls-tree', '--name-only', h, f'{path}' if unit else f'{law}/').split()
    if not names:
        sys.exit(f'{path}: not in force on {day} (repealed or removed by then)')
    if unit:
        sys.stdout.write(git('show', f'{h}:{path}'))
        return

    def order(n: str):
        stem = n.rsplit('/', 1)[-1][:-3]
        head = stem.split('-')[0].split('~')[0]
        rank = 0 if stem == 'title' else (2 if not head.isdigit() else 1)
        nums = [int(x) if x.isdigit() else 0 for x in stem.replace('~', '-').split('-')]
        return (rank, nums, stem)
    for n in sorted(names, key=order):
        sys.stdout.write(git('show', f'{h}:{n}') + '\n')


if __name__ == '__main__':
    main()
