
# Quick Start Guide for Developers

This guide will help you get the LTC Box Office project up and running on your local machine.

## Prerequisites

- Python 3.8 or higher
- MySQL 5.7+ or MariaDB 10.3+
- Redis (for Celery)
- Git
- Node.js and npm (for frontend dependencies)

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/beppemiletto/ltcboxoffice.git
cd ltcboxoffice
```

### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install Node.js packages
npm install
```

### 4. Set Up Environment Variables

```bash
# Windows
copy .env.example .env

# Linux/macOS
cp .env.example .env
```

Edit `.env` and configure:
- Database credentials
- Email settings (or use console backend for development)
- Secret key (generate a new one)

### 5. Create Database

```sql
CREATE DATABASE ltcboxoffice CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'djangodbuser'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON ltcboxoffice.* TO 'djangodbuser'@'localhost';
FLUSH PRIVILEGES;
```

### 6. Run Migrations

```bash
python manage.py migrate
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

### 8. Load Initial Data (Optional)

```bash
python manage.py loaddata ltcboxoffice_start_data_fixture.json
```

### 9. Start Development Server

```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000

### 10. Start Celery (in separate terminals)

**Terminal 2 - Worker:**
```bash
celery -A ltcboxoffice worker --loglevel=info
```

**Terminal 3 - Beat:**
```bash
celery -A ltcboxoffice beat --loglevel=info
```

## Using Make Commands (Recommended)

If you have `make` installed, use these shortcuts:

```bash
make dev-install      # Install all dependencies
make migrate          # Run migrations
make run              # Start development server
make celery-worker    # Start Celery worker
make celery-beat      # Start Celery beat
make test             # Run tests
make lint             # Run linters
make format           # Format code
```

View all commands: `make help`

## Development Workflow

### Before Starting Work

1. Pull latest changes: `git pull`
2. Activate virtual environment
3. Install any new dependencies: `pip install -r requirements.txt`
4. Run migrations: `python manage.py migrate`

### Making Changes

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Format code: `make format` or `black . && isort .`
4. Run tests: `make test` or `pytest`
5. Check for linting issues: `make lint`

### Committing Changes

1. Stage changes: `git add .`
2. Commit: `git commit -m "feat: your feature description"`
3. Push: `git push origin feature/your-feature`
4. Create Pull Request on GitHub

## Project Structure Overview

```
ltcboxoffice/
├── accounts/          # User authentication
├── billboard/         # Event listings
├── booking/           # Reservations
├── boxoffice/         # Point-of-sale
├── carts/            # Shopping cart
├── fiscalmgm/        # Fiscal documents
├── hall/             # Venue management
├── orders/           # Order processing
├── store/            # Product catalog
├── tickets/          # Ticket generation
├── ltcboxoffice/     # Project configuration
│   └── settings/     # Environment settings
└── templates/        # HTML templates
```

## Common Tasks

### Create a New App

```bash
python manage.py startapp myapp
```

Then add to `INSTALLED_APPS` in `settings/base.py`

### Make Model Changes

```bash
python manage.py makemigrations
python manage.py migrate
```

### Access Django Shell

```bash
python manage.py shell
```

### Collect Static Files

```bash
python manage.py collectstatic
```

### Run Specific Tests

```bash
pytest accounts/tests.py
pytest -k test_user_creation
```

## Troubleshooting

### Database Connection Error

- Check MySQL is running
- Verify credentials in `.env`
- Ensure database exists

### ImportError or Module Not Found

- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

### Celery Not Working

- Check Redis is running: `redis-cli ping` (should return PONG)
- Verify `CELERY_BROKER_URL` in `.env`

### Static Files Not Loading

- Run `python manage.py collectstatic`
- Check `STATIC_ROOT` and `STATICFILES_DIRS` settings

## Useful Development Tools

### Django Debug Toolbar (Optional)

```bash
pip install django-debug-toolbar
```

Add to `settings/development.py`:
```python
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

### iPython Shell

```bash
pip install ipython django-extensions
python manage.py shell_plus
```

## Next Steps

- Read the [README.md](README.md) for full documentation
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- Review [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- See [CHANGELOG.md](CHANGELOG.md) for project history

## Getting Help

- Check existing issues on GitHub
- Read Django documentation: https://docs.djangoproject.com
- Review project documentation in `/docs` (if available)

Happy coding! 🎭
