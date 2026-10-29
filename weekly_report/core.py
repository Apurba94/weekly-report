"""Collect commits (with line statistics) via `git log`, plus notes edited during the period."""
import datetime as dt
import os
import re
import subprocess

SEP = "\x1e"
FMT = SEP + "%H%x1f%an%x1f%ae%x1f%ad%x1f%s"


def week_range(today=None, weeks_back=0):
    """Monday..Sunday of the current (or a previous) ISO week."""
    today = today or dt.date.today()
    monday = today - dt.timedelta(days=today.weekday()) - dt.timedelta(weeks=weeks_back)
    return monday, monday + dt.timedelta(days=6)


def git_log(repo, since, until, author=None):
    cmd = ["git", "-C", repo, "log", "--no-merges", "--date=short", "--pretty=format:" + FMT, "--numstat",
           "--since=%s 00:00" % since.isoformat(), "--until=%s 23:59:59" % until.isoformat()]
    if author:
        cmd.append("--author=" + author)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError("git log failed in %s: %s" % (repo, r.stderr.strip()))
    return r.stdout


def parse_log(text):
    """Parse output of git log with FMT and --numstat into commit dicts."""
    commits = []
    for block in text.split(SEP):
        block = block.strip("\n")
        if not block:
            continue
        head, *stats = block.split("\n")
        h, name, email, date, subject = head.split("\x1f", 4)
        added = deleted = files = 0
        for line in stats:
            m = re.match(r"^(\d+|-)\t(\d+|-)\t(.+)$", line)
            if m:
                files += 1
                added += int(m.group(1)) if m.group(1) != "-" else 0
                deleted += int(m.group(2)) if m.group(2) != "-" else 0
        commits.append({"hash": h[:8], "author": name, "email": email, "date": date, "subject": subject,
                        "files": files, "added": added, "deleted": deleted})
    return commits


def notes_in_range(folder, since, until, exts=(".md", ".txt", ".tex")):
    """Notes/manuscript files modified in the period, newest first, with their first heading."""
    out = []
    lo = dt.datetime.combine(since, dt.time.min).timestamp()
    hi = dt.datetime.combine(until, dt.time.max).timestamp()
    for dp, dns, fns in os.walk(folder):
        dns[:] = [d for d in dns if not d.startswith(".")]
        for fn in fns:
            if not fn.lower().endswith(exts):
                continue
            p = os.path.join(dp, fn)
            mt = os.path.getmtime(p)
            if lo <= mt <= hi:
                title = fn
                with open(p, encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        m = re.match(r"^#\s+(.+)|\\title\{([^}]*)\}", line)
                        if m:
                            title = (m.group(1) or m.group(2)).strip()
                            break
                out.append({"path": os.path.relpath(p, folder), "title": title, "modified": dt.datetime.fromtimestamp(mt)})
    return sorted(out, key=lambda x: x["modified"], reverse=True)


_TYPES = [("fix", r"^(fix|bug|hotfix)"), ("feature", r"^(feat|add|implement|new)"), ("docs", r"^(docs?|readme)"),
          ("analysis", r"(analy|figure|plot|result|model|stat)"), ("writing", r"(draft|manuscript|paper|section|revis)")]


def classify(subject):
    s = subject.lower()
    for name, rx in _TYPES:
        if re.search(rx, s):
            return name
    return "other"


def render(repos, notes, since, until, author=None, plans=None):
    total = sum(len(c) for c in repos.values())
    lines = ["# Weekly report: %s to %s" % (since.isoformat(), until.isoformat()), ""]
    if author:
        lines += ["**Author:** %s" % author, ""]
    added = sum(c["added"] for cs in repos.values() for c in cs)
    deleted = sum(c["deleted"] for cs in repos.values() for c in cs)
    days = len({c["date"] for cs in repos.values() for c in cs})
    lines += ["**Summary:** %d commit(s) in %d repositor%s on %d day(s), +%d / -%d lines; %d note(s) updated." % (
        total, len([r for r in repos.values() if r]), "y" if len([r for r in repos.values() if r]) == 1 else "ies", days,
        added, deleted, len(notes)), ""]
    for name, commits in repos.items():
        if not commits:
            continue
        kinds = {}
        for c in commits:
            kinds[classify(c["subject"])] = kinds.get(classify(c["subject"]), 0) + 1
        lines += ["## %s (%d commits: %s)" % (name, len(commits), ", ".join("%s %d" % kv for kv in sorted(kinds.items()))), ""]
        for c in sorted(commits, key=lambda c: c["date"]):
            lines.append("- %s %s (`%s`, +%d/-%d)" % (c["date"], c["subject"], c["hash"], c["added"], c["deleted"]))
        lines.append("")
    if notes:
        lines += ["## Notes and documents", ""]
        lines += ["- %s: %s" % (n["modified"].strftime("%a %d %b"), n["title"]) for n in notes]
        lines.append("")
    lines += ["## Next week", ""] + (["- " + p for p in plans] if plans else ["- "]) + [""]
    lines += ["## Blockers / help needed", "", "- ", ""]
    return "\n".join(lines)
