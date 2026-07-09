"""
Importa gli utenti dal vecchio sito nel nuovo.
Supporta due modalità:
  1. File SQL (mysqldump): --sql-file /path/to/dump.sql
  2. Connessione diretta via SSH tunnel: --host ... --user ... --password ...

Gli utenti importati vengono creati con is_active=False e migrated_from_old_site=True.
Non sovrascrive utenti già esistenti (match per email).

Uso:
  python manage.py import_migrated_users --sql-file /tmp/vecchio_sito.sql [--dry-run]
  python manage.py import_migrated_users --host 127.0.0.1 --port 3308 --db ltcboxoffice \
      --user USERNAME --password PASSWORD [--dry-run]
"""

import re
from django.core.management.base import BaseCommand, CommandError
from accounts.models import Account, UserProfile


def _parse_sql_dump(path):
    """
    Legge un mysqldump e restituisce (users, profiles).
    users: lista di dict con i campi di accounts_account
    profiles: dict {old_user_id: dict} con i campi di accounts_userprofile
    """
    with open(path, encoding='utf-8') as f:
        content = f.read()

    # Estrae il blocco VALUES di accounts_account
    account_match = re.search(
        r"INSERT INTO `accounts_account` VALUES\s*(.*?);",
        content, re.DOTALL
    )
    profile_match = re.search(
        r"INSERT INTO `accounts_userprofile` VALUES\s*(.*?);",
        content, re.DOTALL
    )

    users = []
    profiles = {}

    if account_match:
        for row in _parse_values(account_match.group(1)):
            # Colonne nell'ordine del dump:
            # id, password, first_name, last_name, username, email, phone_number,
            # date_joined, last_login, is_admin, is_staff, is_active, is_superadmin
            if len(row) < 13:
                continue
            users.append({
                'old_id':       int(row[0]),
                'password':     row[1],
                'first_name':   row[2],
                'last_name':    row[3],
                'username':     row[4],
                'email':        row[5],
                'phone_number': row[6],
                'date_joined':  row[7],
                'last_login':   row[8],
                'is_admin':     bool(int(row[9])),
                'is_staff':     bool(int(row[10])),
                'is_superadmin': bool(int(row[12])),
            })

    if profile_match:
        for row in _parse_values(profile_match.group(1)):
            # id, address_line1, address_line2, profile_picture, city, province, post_code, user_id
            if len(row) < 8:
                continue
            profiles[int(row[7])] = {
                'address_line1': row[1],
                'address_line2': row[2],
                'city':          row[4],
                'province':      row[5],
                'post_code':     row[6],
            }

    return users, profiles


def _parse_values(values_str):
    """
    Parsea le tuple VALUES di un INSERT mysqldump.
    Restituisce lista di liste di stringhe (un elemento per colonna).
    Gestisce stringhe con escape, NULL, e numeri.
    """
    rows = []
    i = 0
    s = values_str.strip()
    while i < len(s):
        if s[i] == '(':
            row, i = _parse_tuple(s, i)
            rows.append(row)
        else:
            i += 1
    return rows


def _parse_tuple(s, start):
    """Parsea una singola tupla a partire da '('."""
    assert s[start] == '('
    i = start + 1
    fields = []
    current = []

    while i < len(s):
        c = s[i]

        if c == "'":
            # stringa SQL con escape
            i += 1
            buf = []
            while i < len(s):
                ch = s[i]
                if ch == '\\':
                    i += 1
                    esc = s[i] if i < len(s) else ''
                    buf.append({'n': '\n', 't': '\t', 'r': '\r', "'": "'",
                                '\\': '\\'}.get(esc, esc))
                elif ch == "'":
                    break
                else:
                    buf.append(ch)
                i += 1
            fields.append(''.join(buf))

        elif s[i:i+4].upper() == 'NULL':
            fields.append(None)
            i += 3

        elif c == ',':
            pass  # separatore tra campi (già gestito)

        elif c == ')':
            i += 1
            break

        elif c in '-0123456789':
            # numero
            j = i
            while i < len(s) and s[i] not in (',', ')'):
                i += 1
            fields.append(s[j:i].strip())
            continue

        i += 1

    return fields, i


class Command(BaseCommand):
    help = 'Importa utenti dal vecchio sito come inattivi/migrati'

    def add_arguments(self, parser):
        parser.add_argument('--sql-file', help='Path al dump SQL (mysqldump)')
        parser.add_argument('--host', help='Host MySQL diretto')
        parser.add_argument('--port', type=int, default=3306)
        parser.add_argument('--db', help='Nome database')
        parser.add_argument('--user', help='Utente MySQL')
        parser.add_argument('--password', help='Password MySQL')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if options.get('sql_file'):
            try:
                old_users, old_profiles = _parse_sql_dump(options['sql_file'])
            except Exception as e:
                raise CommandError(f'Errore lettura SQL file: {e}')
            self.stdout.write(f'Letti {len(old_users)} utenti e {len(old_profiles)} profili dal file SQL')

        elif options.get('host'):
            try:
                import MySQLdb
                conn = MySQLdb.connect(
                    host=options['host'], port=options['port'],
                    db=options['db'], user=options['user'],
                    passwd=options['password'], charset='utf8mb4',
                )
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, password, first_name, last_name, username, email, phone_number,
                           date_joined, last_login, is_admin, is_staff, is_active, is_superadmin
                    FROM accounts_account ORDER BY id
                """)
                rows = cursor.fetchall()
                old_users = [{
                    'old_id': r[0], 'password': r[1], 'first_name': r[2], 'last_name': r[3],
                    'username': r[4], 'email': r[5], 'phone_number': r[6],
                    'date_joined': r[7], 'last_login': r[8],
                    'is_admin': bool(r[9]), 'is_staff': bool(r[10]), 'is_superadmin': bool(r[12]),
                } for r in rows]
                cursor.execute("""
                    SELECT user_id, address_line1, address_line2, city, province, post_code
                    FROM accounts_userprofile
                """)
                old_profiles = {r[0]: {
                    'address_line1': r[1], 'address_line2': r[2],
                    'city': r[3], 'province': r[4], 'post_code': r[5],
                } for r in cursor.fetchall()}
                cursor.close()
                conn.close()
            except Exception as e:
                raise CommandError(f'Connessione DB fallita: {e}')
        else:
            raise CommandError('Specificare --sql-file oppure --host/--db/--user/--password')

        existing_emails = set(Account.objects.values_list('email', flat=True))
        imported = skipped = 0

        for u in old_users:
            email = u.get('email', '')
            if not email:
                skipped += 1
                continue

            if email in existing_emails:
                self.stdout.write(f'  skip (già esiste): {email}')
                skipped += 1
                continue

            # Assicura username univoco
            base = u.get('username') or email.split('@')[0]
            unique_username = base
            suffix = 1
            while Account.objects.filter(username=unique_username).exists():
                unique_username = f'{base}_{suffix}'
                suffix += 1

            if dry_run:
                self.stdout.write(f'  [dry-run] importerebbe: {email}')
                imported += 1
                continue

            user = Account(
                first_name=u.get('first_name') or '',
                last_name=u.get('last_name') or '',
                username=unique_username,
                email=email,
                phone_number=u.get('phone_number') or '',
                is_admin=u.get('is_admin', False),
                is_staff=u.get('is_staff', False),
                is_superadmin=u.get('is_superadmin', False),
                is_active=False,
                migrated_from_old_site=True,
            )
            user.password = u['password']
            user.save()
            existing_emails.add(email)

            prof = old_profiles.get(u['old_id'], {})
            UserProfile.objects.create(
                user=user,
                address_line1=prof.get('address_line1') or '',
                address_line2=prof.get('address_line2') or '',
                city=prof.get('city') or '',
                province=prof.get('province') or '',
                post_code=prof.get('post_code') or '',
                profile_picture='default/default-user.png',
            )

            imported += 1

        prefix = '[DRY-RUN] ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'{prefix}Completato: {imported} importati, {skipped} saltati'
        ))
