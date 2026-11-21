"""CLI: python -m tidynames FOLDER [--slugify] [--prefix X] [--date-prefix] [--number] [--replace A B] [--apply] [--undo]"""
import argparse
import sys

from .core import apply_plan, build_plan, find_collisions, undo


def main(argv=None):
    parser = argparse.ArgumentParser(prog="tidynames", description="Batch rename files, preview first.")
    parser.add_argument("folder", help="Folder whose files get renamed")
    parser.add_argument("--slugify", action="store_true", help="Lowercase, spaces to dashes, strip unsafe characters")
    parser.add_argument("--prefix", default="", help="Text to put in front of every name")
    parser.add_argument("--date-prefix", action="store_true", help="Prefix with the file date as YYYYMMDD-")
    parser.add_argument("--number", action="store_true", help="Prefix with a sequence number 001-, 002-, ...")
    parser.add_argument("--start", type=int, default=1, help="First sequence number")
    parser.add_argument("--replace", nargs=2, metavar=("FROM", "TO"), help="Replace text in the name")
    parser.add_argument("--apply", action="store_true", help="Actually rename (default is a dry run preview)")
    parser.add_argument("--undo", action="store_true", help="Undo the last applied rename batch in this folder")
    args = parser.parse_args(argv)

    if args.undo:
        restored = undo(args.folder)
        if not restored:
            print("Nothing to undo (no tidynames-undo.json found).")
            return 0
        for entry in restored:
            print(f"{entry['new']} -> {entry['old']}")
        print(f"undone: {len(restored)} files")
        return 0

    plan = build_plan(args.folder, slug=args.slugify, prefix=args.prefix,
                      date_prefix=args.date_prefix, number=args.number,
                      start=args.start, replace=args.replace)
    collisions = find_collisions(args.folder, plan)
    blocked = {id(entry) for entry in collisions}
    safe = [entry for entry in plan if id(entry) not in blocked]
    for entry in safe:
        print(f"{entry['old']} -> {entry['new']}")
    for entry in collisions:
        print(f"SKIP (name clash): {entry['old']} -> {entry['new']}", file=sys.stderr)
    if not args.apply:
        print(f"preview only: {len(safe)} renames, {len(collisions)} skipped. Rerun with --apply to do it.")
        return 0
    done = apply_plan(args.folder, safe)
    print(f"renamed: {len(done)} files. Undo any time with: python -m tidynames {args.folder} --undo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
