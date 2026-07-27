"""
Invia le email di migrazione a tutti gli utenti con migrated_from_old_site=True
e is_active=False che non hanno ancora confermato.

Uso:
  python manage.py send_migration_emails [--dry-run] [--batch 50]
"""

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from accounts.models import Account


class Command(BaseCommand):
    help = 'Invia email di conferma migrazione agli utenti importati dal vecchio sito'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Simula senza inviare')
        parser.add_argument('--batch', type=int, default=0,
                            help='Invia solo i primi N (0 = tutti)')
        parser.add_argument('--staff-only', action='store_true',
                            help='Invia solo agli utenti staff/admin')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch = options['batch']
        staff_only = options['staff_only']

        users = Account.objects.filter(migrated_from_old_site=True, is_active=False)
        if staff_only:
            from django.db.models import Q
            users = users.filter(Q(is_staff=True) | Q(is_admin=True))
        if batch:
            users = users[:batch]

        from django.conf import settings as djsettings
        domain = getattr(djsettings, 'SITE_DOMAIN', 'prenota.teatrocambiano.com')
        sent = 0
        errors = 0

        for user in users:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            body = render_to_string('accounts/migration_email.html', {
                'user': user,
                'domain': domain,
                'uid': uid,
                'token': token,
            })

            if dry_run:
                self.stdout.write(f'  [dry-run] manderebbe a: {user.email}')
                sent += 1
                continue

            try:
                mail = EmailMessage(
                    subject=f'[Teatro Cambiano] Conferma il tuo account sul nuovo sito',
                    body=body,
                    to=[user.email],
                )
                mail.send()
                sent += 1
                self.stdout.write(f'  inviata: {user.email}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  errore {user.email}: {e}'))
                errors += 1

        prefix = '[DRY-RUN] ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'{prefix}Completato: {sent} email inviate, {errors} errori'
        ))
