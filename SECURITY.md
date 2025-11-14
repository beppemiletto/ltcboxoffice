# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please send an email to security@teatrocambiano.com with:

1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if any)

You should receive a response within 48 hours. If the issue is confirmed, we will:

1. Work on a fix
2. Release a security patch
3. Credit you for the discovery (unless you prefer to remain anonymous)

## Security Best Practices

When deploying this application:

- Always use HTTPS in production
- Keep `SECRET_KEY` secure and unique
- Use environment variables for sensitive data
- Keep dependencies updated
- Enable all security middleware
- Configure ALLOWED_HOSTS properly
- Use strong database passwords
- Enable database backups
- Monitor logs for suspicious activity
