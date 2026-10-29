"""Resolve every `code:` link in the system pages to exact GitHub line ranges.

Usage:
    python3 scripts/gen-code-refs.py <path-to-game-repo-checked-out-at-the-tag>

Reads src/content/systems/*.md for links like (code:AChrisGameMode::DetermineRoundWinner),
finds where each symbol starts and ends in the game's Source folder, and writes
src/data/code-refs.json. Run it again whenever CODE.ref in src/config.ts changes.

Symbol forms:
    Class::Function   a function definition in a .cpp file
    Name              a class or struct declaration in a header
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / 'src' / 'content' / 'systems'
OUT = ROOT / 'src' / 'data' / 'code-refs.json'
LINK = re.compile(r'\]\(code:([^)]+)\)')


def find_function(files, cls, fn):
    pattern = re.compile(rf'^[\w:<>\*&\s,]*\b{re.escape(cls)}::{re.escape(fn)}\s*\(')
    for path in files:
        if path.suffix != '.cpp':
            continue
        lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
        for i, line in enumerate(lines):
            if pattern.match(line):
                for j in range(i, len(lines)):
                    if lines[j].rstrip() == '}':
                        return path, i + 1, j + 1
    return None


def find_type(files, kind, name):
    pattern = re.compile(rf'^\s*{kind}\s+(?:\w+_API\s+)?{re.escape(name)}\b(?!;)')
    for path in files:
        if path.suffix != '.h':
            continue
        lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
        for i, line in enumerate(lines):
            if pattern.match(line):
                start = i - 1 if i > 0 and lines[i - 1].strip().startswith(('USTRUCT', 'UCLASS')) else i
                for j in range(i, len(lines)):
                    if lines[j].rstrip() == '};':
                        return path, start + 1, j + 1
    return None


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    repo = pathlib.Path(sys.argv[1]).resolve()
    files = sorted((repo / 'Source').rglob('*.[ch]*'))
    symbols = sorted({m.group(1).strip() for md in CONTENT.glob('*.md') for m in LINK.finditer(md.read_text())})

    refs, missing = {}, []
    for sym in symbols:
        if '::' not in sym:
            hit = find_type(files, 'class', sym) or find_type(files, 'struct', sym)
        else:
            cls, fn = sym.split('::', 1)
            hit = find_function(files, cls, fn)
        if not hit:
            missing.append(sym)
            continue
        path, start, end = hit
        refs[sym] = {'path': path.relative_to(repo).as_posix(), 'start': start, 'end': end}

    # The tag the game repo is checked out at becomes the ref every link points to
    tag = subprocess.run(['git', '-C', str(repo), 'describe', '--tags', '--exact-match'],
                         capture_output=True, text=True).stdout.strip()
    if not tag:
        sys.exit('Check the game repo out at a tag first (e.g. git checkout v0.9.0).')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'ref': tag, 'symbols': refs}, indent=2) + '\n')
    print(f'Resolved {len(refs)} symbols at {tag} -> {OUT.relative_to(ROOT)}')
    if missing:
        sys.exit('Not found: ' + ', '.join(missing))


if __name__ == '__main__':
    main()
