# weekly-report

**Write your weekly progress report in seconds: commits from all your project repositories
(with lines changed and a rough activity type), notes and manuscripts you edited, and sections for
next week's plans and blockers.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

PhD students, postdocs and project members are often asked for weekly or monthly updates, and the
evidence of what was done is scattered across repositories and note folders. Reconstructing it on Friday
afternoon is tedious and incomplete. Generating a draft from the actual record makes reporting fast and
honest, and the Markdown output pastes into e-mail, wikis or supervisor meeting notes.

## Features

- Commits from any number of git repositories for this week, previous weeks (`--weeks-back`) or a date range
- Author filter, merge commits skipped, `+added/-deleted` line counts per commit (binary files ignored)
- Rough classification of commit subjects: fix, feature, docs, analysis, writing, other
- Notes/manuscript files (`.md`, `.txt`, `.tex`) modified in the period, with their title
- "Next week" and "Blockers" sections, pre-filled with `--plan`

## Usage

```bash
pip install .
weekly-report ~/code/thesis ~/code/paper-2 --author "Ana" --notes ~/notes -o week.md
weekly-report . --weeks-back 1 --plan "finish revision" --plan "run sensitivity analysis"
```

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
