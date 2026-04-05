# Contributing to PyAgent

Thank you for your interest in contributing to PyAgent! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your changes
4. Make your changes
5. Push to your fork and submit a pull request

## Development Setup

### Prerequisites

- Python 3.10 or higher
- uv package manager (recommended) or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/pyagent.git
cd pyagent

# Install uv (if not already installed)
pip install uv

# Install dependencies
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_todo.py -v
```

### Code Quality

```bash
# Run ruff check
uv run ruff check src/ tests/

# Run ruff format
uv run ruff format src/ tests/

# Run mypy
uv run mypy src/
```

## Coding Standards

### Python Style

- Follow PEP 8 style guide
- Use Ruff for formatting and linting
- Maximum line length: 88 characters
- Use type hints for all public functions

### Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Modules | snake_case | `chat_agent.py` |
| Classes | PascalCase | `ChatAgent` |
| Functions | snake_case | `send_message()` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| Private | _leading_underscore | `_internal_func()` |

### Documentation

- Use Google-style docstrings
- Document all public functions and classes
- Keep docstrings up to date

```python
def example_function(param1: str, param2: int) -> bool:
    """Short description of function.

    Longer description if needed.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: If param1 is empty.
    """
    pass
```

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Code style (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding/updating tests
- **chore**: Build process, dependencies, etc.

### Examples

```
feat(browser): add DOM parsing support

Add intelligent DOM parsing for better element detection.

Closes #123
```

```
fix(memory): fix memory leak in chat history

The chat history was not properly cleaning up old entries.
```

## Pull Request Process

1. **Create a branch**: Create a feature branch from `main`
2. **Make changes**: Implement your changes following coding standards
3. **Add tests**: Add tests for new functionality
4. **Update docs**: Update documentation if needed
5. **Run checks**: Ensure all tests pass and code is formatted
6. **Submit PR**: Create a pull request with a clear description

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Commit messages follow guidelines

## Questions?

If you have questions, feel free to:

- Open an issue for discussion
- Check existing documentation in `docs/`
- Review the AGENTS.md file for project structure
