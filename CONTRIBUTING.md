# Contributing to LTC Box Office

Thank you for your interest in contributing to this project!

## Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/ltcboxoffice.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate it and install dependencies: `pip install -r requirements.txt -r requirements-dev.txt`
5. Set up your `.env` file from `.env.example`
6. Run migrations: `python manage.py migrate`

## Code Style

- We use **Black** for code formatting (100 char line length)
- We use **isort** for import sorting
- We use **Flake8** for linting
- We use **Pylint** with Django plugin

Run formatters before committing:
```bash
make format
```

## Pre-commit Hooks

Install pre-commit hooks to automatically check your code:
```bash
pre-commit install
```

## Testing

Write tests for new features and bug fixes:
```bash
make test
```

For coverage report:
```bash
make test-cov
```

## Commit Messages

Follow conventional commits format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Test additions or changes
- `chore:` Build process or auxiliary tool changes

Example: `feat: add seat reservation timeout`

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Ensure all tests pass
3. Make sure code follows the style guidelines
4. Update documentation as needed
5. Request review from maintainers

## Questions?

Open an issue for discussion before starting major changes.
