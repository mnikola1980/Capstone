# CLAUDE.md

This file provides guidance for AI assistants (Claude Code and similar tools) working in this repository.

## Project Overview

**Capstone** is a location model project. Based on the initial README, the goal is to build a model related to location data — likely a machine learning, geospatial, or predictive modeling system. The project is in its earliest stages (only an initial commit exists).

## Repository State

- **Current state**: Bootstrapped — only a `README.md` exists.
- **No source code, dependencies, tests, or CI/CD** have been added yet.
- All substantive development is ahead; conventions below should be followed as the project grows.

## Repository Structure

```
Capstone/
├── README.md       # Project description (minimal)
└── CLAUDE.md       # This file
```

As the project matures, expected additions include:
- `src/` or a language-appropriate source directory
- `tests/` or `test/` for test suites
- `data/` for datasets or data loading utilities (add to `.gitignore` if large)
- `notebooks/` if exploratory data analysis is involved
- `requirements.txt` / `pyproject.toml` (Python) or `package.json` (Node.js)
- `Dockerfile` / `docker-compose.yml` for containerization
- `.github/workflows/` for CI/CD

## Git Workflow

### Branching

- **`main`**: Stable, production-ready code. Never push directly.
- **Feature branches**: Use descriptive names, e.g. `feature/location-model-training`, `fix/data-loader-bug`.
- **Claude branches**: Prefixed with `claude/` (e.g. `claude/add-claude-documentation-NOQyp`).

### Commits

- Write clear, imperative commit messages: `Add location parser module`, not `added stuff`.
- Keep commits focused; one logical change per commit.
- Commit messages should explain *why*, not just *what*, when the reason isn't obvious.

### Pushing

Always push with tracking:
```bash
git push -u origin <branch-name>
```

If push fails due to network errors, retry with exponential backoff: 2s, 4s, 8s, 16s.

## Development Conventions

### General

- Prefer editing existing files over creating new ones unless a new file is clearly required.
- Do not add speculative abstractions, unused helpers, or code for hypothetical future features.
- Only validate at system boundaries (user input, external APIs); trust internal invariants.
- Do not add error handling for impossible scenarios.

### Code Style

Conventions will be established once the primary language and framework are chosen. Until then:
- Follow the idiomatic style of whichever language is adopted.
- Add a linter/formatter config file (`.eslintrc`, `pyproject.toml [tool.ruff]`, etc.) early in development to enforce consistency.

### Security

- Never commit secrets, API keys, or credentials. Use environment variables.
- Add a `.env.example` file when environment variables are introduced.
- Add `.env` to `.gitignore` immediately when creating it.

### Testing

- Write tests alongside new features, not after.
- Tests live in a `tests/` directory mirroring the source structure.
- All tests must pass before merging to `main`.

## Common Commands

These will be populated as the tech stack is established. Placeholder structure:

```bash
# Install dependencies
# <install command>

# Run the application
# <run command>

# Run tests
# <test command>

# Lint / format
# <lint command>
```

## GitHub Repository

- **Owner/repo**: `mnikola1980/Capstone`
- **Remote**: `origin` (proxied via local Claude Code proxy)
- **Default branch**: `main`

## Notes for AI Assistants

- The project goal ("build location model") likely involves geospatial data, ML modeling, or both — ask the user for clarification before choosing a tech stack or architecture.
- Do not create a pull request unless the user explicitly asks for one.
- All development for Claude-initiated tasks should happen on the designated `claude/` branch and be pushed before the session ends.
- Update this `CLAUDE.md` whenever significant new conventions, commands, or structural decisions are made.
