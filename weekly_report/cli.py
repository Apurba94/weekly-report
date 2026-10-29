"""Command-line interface for weekly-report."""
import argparse
import datetime as dt
import os
import sys

from .core import git_log, notes_in_range, parse_log, render, week_range


def main(argv=None, today=None):
    ap = argparse.ArgumentParser(prog="weekly-report", description="Weekly progress report from git and notes.")
    ap.add_argument("repos", nargs="*", default=["."], help="git repositories")
    ap.add_argument("--author", help="only commits whose author matches (name or e-mail)")
    ap.add_argument("--weeks-back", type=int, default=0, help="0 = this week, 1 = last week ...")
    ap.add_argument("--since", help="YYYY-MM-DD (overrides the week)")
    ap.add_argument("--until", help="YYYY-MM-DD")
    ap.add_argument("--notes", action="append", default=[], help="folder of notes/manuscripts to include")
    ap.add_argument("--plan", action="append", default=[], help="item for the 'Next week' section")
    ap.add_argument("-o", "--output")
    args = ap.parse_args(argv)
    since, until = week_range(today, args.weeks_back)
    if args.since:
        since = dt.date.fromisoformat(args.since)
    if args.until:
        until = dt.date.fromisoformat(args.until)
    repos = {}
    for r in args.repos:
        try:
            repos[os.path.basename(os.path.abspath(r))] = parse_log(git_log(r, since, until, args.author))
        except RuntimeError as exc:
            print("warning: %s" % exc, file=sys.stderr)
    notes = [n for folder in args.notes for n in notes_in_range(folder, since, until)]
    text = render(repos, notes, since, until, args.author, args.plan)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    return 0
