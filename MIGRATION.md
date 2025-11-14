# Migration Guide: Upgrading to Professional Structure

This guide helps you migrate from the old project structure to the new professional setup.

## ⚠️ Important Notes

- **Backup everything** before starting
- **Test in development** before production
- The old `settings.py` still works (with deprecation warning)
- You can migrate gradually

## 🔄 Step-by-Step Migration

### Phase 1: Preparation (5 minutes)

1. **Backup your current setup:**
   ```powershell
   # Create backup
   cd ..
   Copy-Item ltcboxoffice ltcboxoffice_backup -Recurse
   cd ltcboxoffice
   ```

2. **Check Git status:**
   ```powershell
   git status
   git add .
   git commit -m "chore: backup before migration"
   ```

### Phase 2: Environment Setup (10 minutes)

1. **Create `.env` file:**
   ```powershell
   copy .env.example .env
   ```

2. **Configure `.env` with your current values:**
   ```ini
   # Your current database settings
   DB_NAME=ltcboxoffice
   DB_USER=djangodbuser
   DB_PASSWORD=aSdF!234
   DB_HOST=127.0.0.1
   DB_PORT=3306

   # Your current email settings
   EMAIL_HOST=smtp.teatrocambiano.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=ltcboxoffice@teatrocambiano.com
   EMAIL_HOST_PASSWORD=2024Boxlabo?
   EMAIL_USE_TLS=False

   # Generate a new secret key for production!
   SECRET_KEY=django-insecure-410%jpm^odm^!zj7*3u5^v@ae=p!-4#p0&#cw)k%eu5fj9$te0

   # Set environment
   DJANGO_ENV=development
   ```

3. **Install python-dotenv (if needed):**
   ```powershell
   pip install python-dotenv
   ```

### Phase 3: Update Dependencies (5 minutes)

1. **Install new/updated packages:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Install development tools (optional but recommended):**
   ```powershell
   pip install -r requirements-dev.txt
   ```

### Phase 4: Test the New Setup (10 minutes)

1. **Verify settings load correctly:**
   ```powershell
   python manage.py check
   ```

2. **Test database connection:**
   ```powershell
   python manage.py migrate --plan
   ```

3. **Run migrations (if any new ones):**
   ```powershell
   python manage.py migrate
   ```

4. **Start development server:**
   ```powershell
   python manage.py runserver
   ```

5. **Visit `http://127.0.0.1:8000` and verify it works**

### Phase 5: Update Your Workflow (Optional)

1. **Install pre-commit hooks:**
   ```powershell
   pre-commit install
   ```

2. **Format existing code (optional):**
   ```powershell
   black .
   isort .
   ```

3. **Run linting to see code quality:**
   ```powershell
   flake8 .
   ```

## 🔍 Verification Checklist

After migration, verify:

- [ ] Application starts: `python manage.py runserver`
- [ ] Admin works: `http://127.0.0.1:8000/admin`
- [ ] Database queries work
- [ ] Static files load
- [ ] Media files accessible
- [ ] Email sends (test)
- [ ] Celery tasks run
- [ ] No deprecation warnings (except the old settings.py one)

## 🎯 Environment Switcher

The new setup uses `DJANGO_ENV` to switch environments:

### Development (Default)
```powershell
$env:DJANGO_ENV="development"
python manage.py runserver
```

### Staging
```powershell
$env:DJANGO_ENV="staging"
python manage.py runserver
```

### Production
```powershell
$env:DJANGO_ENV="production"
# Use Gunicorn in production
gunicorn ltcboxoffice.wsgi:application
```

## 🔧 Common Issues & Solutions

### Issue: "Cannot import settings"

**Solution:**
```powershell
# Make sure settings/__init__.py exists
dir ltcboxoffice\settings\__init__.py
```

### Issue: Environment variables not loaded

**Solution:**
```powershell
# Install python-dotenv
pip install python-dotenv

# Or set manually
$env:DB_NAME="ltcboxoffice"
$env:SECRET_KEY="your-secret-key"
```

### Issue: Old imports fail

**Solution:**
The old `ltcboxoffice.settings` still works with a deprecation warning. You can:
- Ignore the warning (it still works)
- Update to `ltcboxoffice.settings.development` if needed

### Issue: Celery can't find settings

**Solution:**
```powershell
$env:DJANGO_SETTINGS_MODULE="ltcboxoffice.settings"
celery -A ltcboxoffice worker --loglevel=info
```

### Issue: Static files not loading

**Solution:**
```powershell
python manage.py collectstatic --noinput
```

## 📋 Update Checklist for Production

Before deploying to production:

- [ ] Generate new `SECRET_KEY` (never use dev key!)
- [ ] Set `DEBUG=False` in `.env`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set `DJANGO_ENV=production`
- [ ] Use strong database password
- [ ] Configure email with real SMTP
- [ ] Set up HTTPS/SSL certificates
- [ ] Review security settings in `settings/production.py`
- [ ] Test with `python manage.py check --deploy`
- [ ] Set up backups
- [ ] Configure logging
- [ ] Set up monitoring

## 🔐 Generate New Secret Key

**Never use the default key in production!**

Generate a new one:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output to your `.env` file:
```ini
SECRET_KEY=your-newly-generated-secret-key-here
```

## 🐳 Docker Migration (Optional)

To migrate to Docker:

1. **Ensure `.env` is configured**
2. **Build images:**
   ```powershell
   docker-compose build
   ```

3. **Start services:**
   ```powershell
   docker-compose up -d
   ```

4. **Run migrations:**
   ```powershell
   docker-compose exec web python manage.py migrate
   ```

5. **Create superuser:**
   ```powershell
   docker-compose exec web python manage.py createsuperuser
   ```

## 📊 Rollback Plan

If something goes wrong:

1. **Stop the application**
2. **Restore backup:**
   ```powershell
   cd ..
   Remove-Item ltcboxoffice -Recurse -Force
   Copy-Item ltcboxoffice_backup ltcboxoffice -Recurse
   cd ltcboxoffice
   ```

3. **Reinstall old dependencies:**
   ```powershell
   pip install -r requirements_20250911.txt
   ```

4. **Start old version:**
   ```powershell
   python manage.py runserver
   ```

## 💡 Tips

- **Gradual migration:** You can keep using old settings.py while testing new structure
- **Test locally first:** Never test directly in production
- **Keep backups:** Database and media files especially
- **Document changes:** Keep notes of what you modified
- **Ask for help:** Open GitHub issue if stuck

## 📞 Support

If you encounter issues:

1. Check this migration guide
2. Review error messages carefully
3. Check logs: `logs/django.log`
4. Search GitHub issues
5. Create new issue with details

## ✅ Post-Migration Tasks

After successful migration:

1. Update documentation if you made custom changes
2. Inform team members about new structure
3. Update deployment scripts
4. Set up CI/CD if using GitHub Actions
5. Configure monitoring/logging services
6. Test all functionality thoroughly
7. Monitor for any issues in first few days

---

**Migration Status Tracking:**

- [ ] Phase 1: Preparation
- [ ] Phase 2: Environment Setup  
- [ ] Phase 3: Update Dependencies
- [ ] Phase 4: Test New Setup
- [ ] Phase 5: Update Workflow
- [ ] Verification Complete
- [ ] Production Deployment (if applicable)

Good luck! 🚀
