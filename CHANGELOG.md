# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Environment-based settings configuration (development/staging/production)
- Comprehensive README with setup instructions
- Docker and Docker Compose support
- Pre-commit hooks for code quality
- CI/CD pipeline with GitHub Actions
- Code formatting with Black, isort
- Linting with Flake8, Pylint
- Makefile for common development tasks
- Proper logging configuration
- Security best practices
- Contributing guidelines
- .env.example for configuration

### Changed
- Reorganized settings into environment-specific modules
- Updated requirements.txt with organized sections
- Improved .gitignore with more comprehensive exclusions

### Security
- Moved all secrets to environment variables
- Added HTTPS enforcement in production settings
- Enabled security headers
- Added security scanning in CI/CD

## [1.0.0] - 2024-XX-XX

### Added
- Initial release
- User authentication and profiles
- Event management
- Ticket booking and sales
- Shopping cart functionality
- Payment processing
- Box office interface
- Fiscal document management
- Barcode/QR ticket printing
- Hall and seat management
- Email notifications
- Celery background tasks
- Redis caching support
