import datetime as dt
import io
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout

from weekly_report.cli import main
from weekly_report.core import FMT, SEP, classify, notes_in_range, parse_log, render, week_range

LOG = (SEP + "abcdef1234\x1fAna\x1fana@x.org\x1f2026-03-03\x1fAdd bootstrap analysis\n5\t2\tsrc/a.py\n-\t-\tfig.png\n"
       + SEP + "1234567890\x1fAna\x1fana@x.org\x1f2026-03-05\x1fFix typo in README\n1\t1\tREADME.md\n")


class ParseTests(unittest.TestCase):
    def test_parse_log(self):
        c = parse_log(LOG)
        self.assertEqual(len(c), 2)
        self.assertEqual((c[0]["hash"], c[0]["files"], c[0]["added"], c[0]["deleted"]), ("abcdef12", 2, 5, 2))
        self.assertEqual(c[1]["subject"], "Fix typo in README")

    def test_week_range_and_classify(self):
        self.assertEqual(week_range(dt.date(2026, 3, 5)), (dt.date(2026, 3, 2), dt.date(2026, 3, 8)))
        self.assertEqual(week_range(dt.date(2026, 3, 5), 1)[0], dt.date(2026, 2, 23))
        self.assertEqual(classify("Fix typo"), "fix")
        self.assertEqual(classify("Draft discussion section"), "writing")
        self.assertEqual(classify("Update figure 3 colours"), "analysis")

    def test_render(self):
        text = render({"thesis": parse_log(LOG), "empty": []}, [], dt.date(2026, 3, 2), dt.date(2026, 3, 8),
                      plans=["submit chapter 2"])
        self.assertIn("2 commit(s) in 1 repository on 2 day(s), +6 / -3 lines", text)
        self.assertIn("## thesis (2 commits: feature 1, fix 1)", text)
        self.assertNotIn("## empty", text)
        self.assertIn("- submit chapter 2", text)

    def test_notes_in_range(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "meeting.md")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("# Supervision meeting\nstuff\n")
            ts = dt.datetime(2026, 3, 4, 10).timestamp()
            os.utime(p, (ts, ts))
            notes = notes_in_range(d, dt.date(2026, 3, 2), dt.date(2026, 3, 8))
            self.assertEqual([n["title"] for n in notes], ["Supervision meeting"])
            self.assertEqual(notes_in_range(d, dt.date(2026, 3, 9), dt.date(2026, 3, 15)), [])


@unittest.skipUnless(shutil.which("git"), "git not installed")
class GitTests(unittest.TestCase):
    def test_real_repository(self):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, GIT_AUTHOR_DATE="2026-03-03T10:00:00", GIT_COMMITTER_DATE="2026-03-03T10:00:00")
            run = lambda *a: subprocess.run(["git", "-C", d, "-c", "user.name=Ana", "-c", "user.email=ana@x.org"] + list(a),
                                            capture_output=True, env=env, check=True)
            run("init", "-q")
            with open(os.path.join(d, "a.txt"), "w") as fh:
                fh.write("one\ntwo\n")
            run("add", "a.txt")
            run("commit", "-q", "-m", "Add first draft")
            with redirect_stdout(io.StringIO()) as buf:
                main([d, "--since", "2026-03-02", "--until", "2026-03-08"])
            self.assertIn("Add first draft", buf.getvalue())
            self.assertIn("+2/-0", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
