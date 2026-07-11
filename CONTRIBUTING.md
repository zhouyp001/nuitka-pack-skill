# Contributing to nuitka-pack

Thanks for your interest in contributing!

## Getting started

1. Fork the repository and clone it locally.
2. Create a branch for your change: `git checkout -b fix-something` or `git checkout -b feature-something`.

## What to work on

- **Bug fixes** — check the open issues or report a new one first.
- **New Nuitka gotchas** — if you've hit a Nuitka compilation issue that the skill doesn't cover yet, adding it to the troubleshooting table in `SKILL.md` is a great contribution.
- **Documentation** — corrections, clarifications, or translations for `README.md` / `README_CN.md`.
- **Scripts** — improvements to `scripts/monitor_cpu.py` or new helper scripts.

## Before submitting

- Run the CI checks locally to verify nothing is broken:

  ```bash
  # Validate SKILL.md frontmatter
  pip install pyyaml
  python -c "import yaml; meta = yaml.safe_load(open('SKILL.md').read().split('---', 2)[1]); print(meta['name'], meta['description'])"

  # Check monitor_cpu.py
  python -m py_compile scripts/monitor_cpu.py
  python scripts/monitor_cpu.py --help
  ```

- Follow the existing style — the skill uses concise, actionable language.

## Pull request process

1. Push your branch and open a PR against `main`.
2. Fill out the PR template.
3. CI will run automatically — make sure it passes.
4. A maintainer will review your PR. Keep it focused — one change per PR is best.

## Skill development notes

- `SKILL.md` uses YAML frontmatter (`---` delimited). The `name` and `description` fields are required by Claude Code.
- The skill is designed to be practical and experience-driven. Before adding new sections, make sure they come from real compilation experience rather than theoretical completeness.
- When adding new Nuitka flags or troubleshooting items, include the **symptom** (what the user sees), the **cause** (why it happens), and the **fix** (exact flag or code change).
