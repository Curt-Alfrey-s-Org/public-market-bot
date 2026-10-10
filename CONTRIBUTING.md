# Contributing to market-pie5-bot

Thank you for your interest in contributing to market-pie5-bot! This document provides guidelines and instructions for contributing.

## Development Workflow

**Build on Windows, run on Linux Mint:** The project is often developed on a Windows PC (e.g. Cursor) and run on a Linux Mint server with `python3` in a venv. Push to GitHub, pull on the server, then run tests and the bot there. See **[DEV_DEPLOY_WORKFLOW.md](DEV_DEPLOY_WORKFLOW.md)** for the full workflow, line endings (`.gitattributes`), and run/test commands.

### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/market-pie5-bot.git
   cd market-pie5-bot
   ```
3. **Set up development environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your test configuration
   ```
5. **Install pre-commit hook** (recommended):
   ```bash
   # This catches code quality issues before committing
   cp pre-commit-hook.sh .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit
   ```
   See [PRE_COMMIT_HOOK_GUIDE.md](PRE_COMMIT_HOOK_GUIDE.md) for details.

### Making Changes

1. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bugfix-name
   ```

2. **Make your changes** following our coding standards (see below)

3. **Run tests** to ensure nothing is broken. On **Linux Mint** (or your run environment), use the project venv:
   ```bash
   source venv/bin/activate
   python3 -m unittest discover -s . -p "test_*.py" -v
   # or: python3 -m pytest test_*.py -v
   ```
   If you develop on Windows, run tests on the Linux server (or in WSL) before pushing; see [DEV_DEPLOY_WORKFLOW.md](DEV_DEPLOY_WORKFLOW.md).

4. **Commit your changes** with clear, descriptive messages:
   ```bash
   git add .
   git commit -m "Add feature: your feature description"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** on GitHub

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 127 characters
- Use meaningful variable and function names

### Code Quality Tools

We use automated tools to maintain code quality:

- **flake8**: Linting and style checking
- **black**: Code formatting
- **isort**: Import sorting
- **pylint**: Static code analysis

Run these tools before submitting:

```bash
# Check code style
flake8 . --max-line-length=127 --exclude=venv,node_modules,.git

# Format code
black . --exclude="venv|node_modules|\.git"

# Sort imports
isort . --skip venv --skip node_modules

# Run pylint
pylint *.py --max-line-length=127 --ignore=venv,node_modules,.git,test_*.py
```

### Documentation

- Add docstrings to all functions, classes, and modules
- Use clear, concise comments for complex logic
- Update README.md if adding new features
- Update CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/) format

### Testing

- Write unit tests for all new features
- Maintain or improve test coverage
- Test files should be named `test_*.py`
- Use Python's `unittest` framework
- Mock external APIs in tests

Example test structure:

```python
import unittest

class TestYourFeature(unittest.TestCase):
    def setUp(self):
        # Set up test fixtures
        pass
    
    def test_feature_behavior(self):
        # Test your feature
        self.assertEqual(expected, actual)
    
    def tearDown(self):
        # Clean up after tests
        pass
```

### Running Tests

To run the full test suite locally, use the following commands. These match the commands used in our CI pipeline:

```bash
# Set required environment variables for testing
export ENABLE_PDT_RULES='false'
export PAPER_TRADING_MODE='true'
export SCHWAB_SANDBOX_MODE='true'
export BOT_ENABLE_AI='false'
export BOT_ENABLE_ML='false'
export ENABLE_STOCK_SCREENER='false'
export ENABLE_EMAIL_ALERTS='false'

# Run all tests with pytest (recommended - matches CI)
pytest test_*.py -v --tb=short --maxfail=10

# Or run with unittest
python3 -m unittest discover -s . -p "test_*.py" -v

# Save test output to test_results.txt (useful for CI/troubleshooting)
pytest test_*.py -v --tb=short --maxfail=10 > test_results.txt 2>&1

# Or with unittest
python3 -m unittest discover -s . -p "test_*.py" -v > test_results.txt 2>&1
```

**Pushing Test Results:**

When reporting test failures or requesting help:
1. Run tests and save output to `test_results.txt` using the commands above
2. Review the output to identify failing tests
3. Include relevant portions of `test_results.txt` in your issue or PR
4. For CI failures, test results are automatically uploaded as artifacts

**Note:** You may commit `test_results.txt` to document test runs, or reference it locally when troubleshooting issues.

## Pull Request Guidelines

### Before Submitting

- [ ] Code follows PEP 8 style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated (README, CHANGELOG, docstrings)
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up-to-date with main

### Pull Request Template

When creating a PR, include:

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
Describe how you tested your changes

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

## CI/CD Pipeline

Our GitHub Actions workflows automatically run on every push and PR:

1. **Tests**: Run unit tests on Python 3.8-3.12
2. **Linting**: Check code style and quality
3. **Security**: Scan for vulnerabilities and security issues
4. **Release**: Automatically create releases when version tags are pushed

All checks must pass before a PR can be merged.

**Note:** GitHub Copilot PRs are protected by the Copilot Sentinel workflow, which prevents premature merging while Copilot is still working. See [BRANCH_PROTECTION_GUIDE.md](BRANCH_PROTECTION_GUIDE.md) for details.

### Copilot PR Label Gate

- **Requirement:** Copilot PRs (branches starting with `copilot/`) must include the `copilot-completed` label to merge.
- **Auto-label:** An automation adds this label when all required checks (tests, lint, security, e2e) have completed successfully.
- **Gate & re-check:** The gate re-evaluates on the `labeled` event; merging is allowed when the label is present.
- **Manual fallback:** If automation hasn’t labeled the PR, add it via the PR sidebar (Labels → `copilot-completed`). CLI option:
   - `winget install GitHub.cli`
   - `gh auth login`
   - `gh pr edit <number> --add-label copilot-completed`


## Feature Maturity Levels

When adding new features, indicate their maturity level:

- **Production-Ready** ✅: Fully tested, documented, and ready for production use
- **Beta**: Functional but under active development, may have minor issues
- **Alpha**: Early development, expect significant changes
- **Experimental**: Proof of concept, not recommended for production

Update documentation to reflect feature status.

## Security

### Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** create a public GitHub issue
2. Email the maintainers privately (see README for contact info)
3. Provide detailed information about the vulnerability
4. Allow time for the issue to be fixed before public disclosure

### Security Best Practices

- Never commit API keys, tokens, or passwords
- Use environment variables for sensitive configuration
- Validate and sanitize all user inputs
- Follow secure coding practices

## Release Process

Releases are managed by maintainers:

1. Update version in CHANGELOG.md
2. Commit: `git commit -am "Prepare release v1.x.x"`
3. Tag: `git tag -a v1.x.x -m "Release v1.x.x"`
4. Push: `git push origin v1.x.x`
5. GitHub Actions creates the release automatically

## Getting Help

- **Documentation**: Check [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for all guides
- **Known Issues**: Review [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for known problems
- **Issues**: Search existing [GitHub issues](https://github.com/operator/market-pie5-bot/issues)
- **Issue Templates**: Use templates in `.github/ISSUE_TEMPLATE/` when creating issues
- **Discussions**: Use GitHub Discussions for questions
- **Roadmap**: Check [ROADMAP.md](ROADMAP.md) for planned features

## Commit Message Guidelines

Follow these standards to maintain clean commit history and prevent fragmentation:

### Format
```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring without feature changes
- **test**: Adding or updating tests
- **chore**: Maintenance tasks (dependencies, build config, etc.)
- **perf**: Performance improvements

### Examples
```bash
# Good commit messages
feat: Add email alert system for critical events
fix: Resolve unused variable warnings in main.py
docs: Update DOCUMENTATION_INDEX with new guides
refactor: Clean up imports in trading strategies
test: Add unit tests for risk management module

# Bad commit messages (avoid these)
fix stuff
updated files
changes
WIP
```

### Best Practices
- Use present tense ("Add feature" not "Added feature")
- Keep subject line under 72 characters
- Reference issue numbers when applicable (#123)
- Group related changes in a single commit
- Run linting before committing to avoid alert fixes

### Pre-commit Checks
Run these commands before committing to catch issues early:

```bash
# Check Python syntax errors
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Check code formatting
black --check .

# Check import sorting
isort --check-only .

# Run relevant tests
python -m unittest discover -s . -p "test_*.py" -v
```

## Documentation Standards

### When to Update Documentation
- New features added → Update feature guides
- Feature behavior changed → Update affected guides
- Bug fixes → Update KNOWN_ISSUES.md if relevant
- Configuration changes → Update README.md and relevant guides
- Breaking changes → Update CHANGELOG.md and migration guide

### Documentation Quality Standards
- **Accuracy**: Keep documentation in sync with code
- **Clarity**: Write for the intended audience (users vs developers)
- **Completeness**: Cover all important aspects
- **Examples**: Include code examples and screenshots where helpful
- **Navigation**: Update DOCUMENTATION_INDEX.md for new documents

### Creating New Documentation
1. Choose appropriate location:
   - User guides → Root directory
   - Historical notes → `docs/archive/`
   - Implementation details → Near relevant code or `docs/`
2. Follow existing documentation structure and style
3. Add entry to [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)
4. Link from relevant existing documents
5. Include "Last Updated" date at top

### Archiving Old Documentation
When documentation becomes outdated or superseded:
1. Move to `docs/archive/` directory
2. Add entry to [docs/ARCHIVE.md](docs/ARCHIVE.md)
3. Update links in other documents
4. Consider consolidation if many similar docs exist

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help create a welcoming environment for all contributors

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

Thank you for contributing to market-pie5-bot! 🚀
