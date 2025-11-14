# LTC Box Office

A professional Django-based box office management system for Teatro Cambiano, handling ticket sales, reservations, events, and customer management.

## 🎭 Features

- **Event Management**: Create and manage theater shows, performances, and events
- **Ticket Sales**: Complete ticketing system with seat selection and booking
- **Box Office**: Point-of-sale interface for ticket sales
- **Customer Accounts**: User registration, profiles, and order history
- **Shopping Cart**: Multi-item cart with session management
- **Payment Processing**: Integrated payment handling
- **Fiscal Management**: Receipt and fiscal document generation
- **Barcode/QR Integration**: Ticket printing with barcodes
- **Hall Management**: Seat mapping and venue configuration
- **Cookie Consent**: GDPR-compliant cookie management

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- MySQL 5.7+ or MariaDB 10.3+
- Redis (for Celery tasks)
- Node.js (for frontend assets)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/beppemiletto/ltcboxoffice.git
   cd ltcboxoffice
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Node.js dependencies**
   ```bash
   npm install
   ```

5. **Set up environment variables**
   ```bash
   copy .env.example .env
   # Edit .env with your configuration
   ```

6. **Configure the database**
   - Create a MySQL database named `ltcboxoffice`
   - Update database credentials in `.env`

7. **Run migrations**
   ```bash
   python manage.py migrate
   ```

8. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

9. **Collect static files**
   ```bash
   python manage.py collectstatic --noinput
   ```

10. **Run the development server**
    ```bash
    python manage.py runserver
    ```

Visit `http://127.0.0.1:8000` to see the application.

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example` for complete list):

- `DJANGO_ENV`: Environment (development/staging/production)
- `SECRET_KEY`: Django secret key (generate a new one for production!)
- `DEBUG`: Debug mode (True/False)
- `DB_*`: Database configuration
- `EMAIL_*`: Email server configuration
- `CELERY_*`: Celery/Redis configuration

### Settings Structure

The project uses environment-based settings:

- `settings/base.py`: Common settings for all environments
- `settings/development.py`: Development-specific settings
- `settings/staging.py`: Staging environment settings
- `settings/production.py`: Production-specific settings

Set `DJANGO_ENV` environment variable to switch between environments.

## 📦 Project Structure

```
ltcboxoffice/
├── accounts/          # User authentication and profiles
├── billboard/         # Event listings and display
├── booking/           # Reservation system
├── boxoffice/         # Point-of-sale interface
├── carts/            # Shopping cart functionality
├── fiscalmgm/        # Fiscal document management
├── hall/             # Venue and seat management
├── history/          # Activity logging
├── orders/           # Order processing
├── store/            # Product catalog
├── tickets/          # Ticket generation and management
├── templates/        # Django templates
├── static/           # Static files (CSS, JS, images)
├── media/            # User-uploaded files
└── ltcboxoffice/     # Project configuration
    ├── settings/     # Environment-based settings
    ├── static/       # Project-level static files
    └── urls.py       # URL configuration
```

## 🛠️ Development

### Running with Celery

Start Celery worker for background tasks:

```bash
celery -A ltcboxoffice worker --loglevel=info
```

Start Celery beat for scheduled tasks:

```bash
celery -A ltcboxoffice beat --loglevel=info
```

### Code Quality

Run linting and formatting:

```bash
# Format code with Black
black .

# Check code with Flake8
flake8 .

# Run pylint
pylint */**.py
```

### Running Tests

```bash
python manage.py test
```

## 🐳 Docker Deployment

Build and run with Docker Compose:

```bash
docker-compose up -d
```

## 📝 Common Tasks

### Create new app

```bash
python manage.py startapp appname
```

### Make migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Load fixture data

```bash
python manage.py loaddata ltcboxoffice_start_data_fixture.json
```

### Create superuser

```bash
python manage.py createsuperuser
```

## 🔐 Security

- Never commit `.env` file or expose secret keys
- Use strong, unique `SECRET_KEY` in production
- Keep dependencies updated: `pip list --outdated`
- Enable HTTPS in production (settings configured for this)
- Review and update `ALLOWED_HOSTS` for your domain
- Use environment variables for all sensitive data

## 📄 License

Proprietary - Teatro Cambiano

## 🤝 Contributing

1. Create a feature branch (`git checkout -b feature/amazing-feature`)
2. Commit your changes (`git commit -m 'Add amazing feature'`)
3. Push to the branch (`git push origin feature/amazing-feature`)
4. Open a Pull Request

## 📧 Contact

Project Link: [https://github.com/beppemiletto/ltcboxoffice](https://github.com/beppemiletto/ltcboxoffice)

## 🙏 Acknowledgments

- Django Framework
- Bootstrap
- jQuery
- ReportLab
- python-escpos
