# Contributing to Good To Go

Thank you for your interest in contributing to Good To Go! This guide covers everything you need to set up a development environment.

## Development vs Usage

**If you just want to USE Good To Go**, see the [README](README.md) - you only need:
```bash
pip install goodtogo
```

**This guide is for DEVELOPING Good To Go itself** - contributing code, fixing bugs, adding features.

## Development Setup

### Prerequisites

- Python 3.9+
- Git
- A GitHub account

### Clone the Repository

```bash
git clone https://github.com/dsifry/goodtogo.git
cd goodtogo
```

### Install Development Dependencies

```bash
# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

This installs:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `black` - Code formatter
- `ruff` - Linter
- `mypy` - Type checker

### Verify Installation

```bash
# Run tests
pytest

# Check linting
ruff check .

# Check formatting
black --check .

# Check types
mypy src/
```

## Code Quality Requirements

All contributions must pass these checks:

```bash
# Run all checks
pytest && ruff check . && black --check . && mypy src/
```

### Test Coverage

Good To Go requires **100% branch coverage**. Tests will fail if coverage drops below 100%.

```bash
pytest --cov=goodtogo --cov-report=term-missing
```

### Code Style

- **Formatter**: Black (line length 100)
- **Linter**: Ruff
- **Type hints**: Required for all public functions

```bash
# Auto-format code
black .

# Auto-fix lint issues
ruff check . --fix
```

## Project Architecture

Good To Go uses **hexagonal architecture** (ports and adapters):

```
src/goodtogo/
├── core/                 # Business logic (no external dependencies)
│   ├── models.py        # Pydantic data models
│   ├── interfaces.py    # Abstract interfaces (ports)
│   ├── analyzer.py      # Main PR analysis logic
│   ├── validation.py    # Input validation
│   └── errors.py        # Error handling with redaction
├── adapters/            # External integrations (implements ports)
│   ├── github.py        # GitHub API adapter
│   ├── cache_sqlite.py  # SQLite cache adapter
│   └── cache_memory.py  # In-memory cache (for testing)
├── parsers/             # Comment parsers (strategy pattern)
│   ├── coderabbit.py    # CodeRabbit parser
│   ├── greptile.py      # Greptile parser
│   ├── claude.py        # Claude Code parser
│   ├── cursor.py        # Cursor/Bugbot parser
│   └── generic.py       # Fallback parser
├── container.py         # Dependency injection
├── cli.py               # Click CLI
└── __init__.py          # Public exports
```

### Key Principles

1. **Core has no dependencies** - Business logic is pure Python + Pydantic
2. **Adapters implement interfaces** - Easy to swap implementations
3. **Parsers are pluggable** - Add new reviewers without changing core
4. **Dependency injection** - Container wires everything together
5. **Security by design** - Tokens never logged, errors redacted

## Adding a New Reviewer Parser

To support a new automated reviewer:

1. Create `src/goodtogo/parsers/newreviewer.py`:

```python
from goodtogo.core.interfaces import ReviewerParser
from goodtogo.core.models import CommentClassification, Priority, ReviewerType

class NewReviewerParser(ReviewerParser):
    @property
    def reviewer_type(self) -> ReviewerType:
        return ReviewerType.UNKNOWN  # Or add new enum value

    def can_parse(self, author: str, body: str) -> bool:
        return author == "newreviewer[bot]"

    def parse(self, comment: dict) -> tuple[CommentClassification, Priority, bool]:
        body = comment.get("body", "")
        # Classification logic here
        return (CommentClassification.AMBIGUOUS, Priority.UNKNOWN, True)
```

2. Register in `container.py`:

```python
from goodtogo.parsers.newreviewer import NewReviewerParser

# In create_default():
parsers = [
    CodeRabbitParser(),
    GreptileParser(),
    ClaudeCodeParser(),
    CursorParser(),
    NewReviewerParser(),  # Add here
    GenericParser(),  # Keep generic last
]
```

3. Add tests in `tests/unit/parsers/test_newreviewer.py`

## Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/parsers/test_coderabbit.py

# With coverage report
pytest --cov=goodtogo --cov-report=html
open htmlcov/index.html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Submitting Changes

### Branch Naming

- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring
- `test/` - Test improvements

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Be concise but descriptive
- Reference issues if applicable

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all checks pass:
   ```bash
   pytest && ruff check . && black --check . && mypy src/
   ```
5. Push and create a PR

### PR Checklist

- [ ] Tests pass with 100% coverage
- [ ] Code formatted with Black
- [ ] No Ruff warnings
- [ ] Mypy type checks pass
- [ ] Documentation updated if needed

## Optional: Claude Code Workflow Tools

If you use [Claude Code](https://claude.ai/code), Good To Go includes workflow tools in the `.claude/` directory:

### Install Beads (Task Management)

```bash
npm install -g @coderabbitai/beads
bd init --prefix goodtogo
```

### Available Commands

- `/project:pr-shepherd` - Monitor PR to merge
- `/project:handle-pr-comments` - Address review feedback
- `/project:create-pr` - Create comprehensive PR

These are optional developer tools - they're not required for contributing, but they can help streamline your workflow if you use Claude Code.

## Security Considerations

When contributing, keep these security principles in mind:

1. **Never log tokens** - Use `<redacted>` in `__repr__`
2. **Validate inputs** - Use `validation.py` functions
3. **Redact errors** - Use `errors.py` for user-facing errors
4. **Secure file permissions** - Cache uses 0600/0700

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/dsifry/goodtogo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dsifry/goodtogo/discussions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
