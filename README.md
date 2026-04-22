# textbook_finder

This repository includes baseline CI/CD workflows and shared configuration files.

## Included automation

- **CI** (`.github/workflows/ci.yml`)
  - checks for required baseline config files
  - validates YAML syntax/style
  - lints Markdown files

- **CD** (`.github/workflows/cd.yml`)
  - triggers on semantic-version tags (for example: `v1.0.0`)
  - builds a source archive
  - publishes a GitHub release with generated notes

## Optional local hooks

Install and run pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```
