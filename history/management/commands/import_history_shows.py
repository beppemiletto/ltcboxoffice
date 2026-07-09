"""
Importa gli spettacoli dal vecchio sito nella history del nuovo sito.
Usa SSH per eseguire la query MySQL sul vecchio sito.

Uso:
  python manage.py import_history_shows [--dry-run]
"""
from datetime import date, datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from history.models import HistoryShow, Season
from billboard.models import Section, SiaeType, Venue

SEASON_MAP = [
    (date(2024, 9, 1), date(2025, 7, 31), '2024-2025'),
    (date(2025, 9, 1), date(2026, 7, 31), '2025-2026'),
]


def _season_for_date(d):
    for start, end, label in SEASON_MAP:
        if start <= d <= end:
            return label
    return None


def _fetch_old_shows():
    import paramiko, json

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.1.12', username='ltc', password='ltc', timeout=10)

    query = (
        "SELECT b.shw_title, b.shw_author, b.shw_director, b.shw_theater_company,"
        " b.slug, b.shw_image, b.section_id, b.siaetype_id,"
        " MIN(e.date_time) as prima_data, COALESCE(e.venue_id, 1) as venue_id"
        " FROM billboard_show b"
        " JOIN store_event e ON e.show_id = b.id"
        " GROUP BY b.id ORDER BY prima_data"
    )
    cmd = f"mysql -u djangodbuser -p'aSdF!234' ltcboxoffice -N -e \"{query}\" 2>/dev/null"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    output = stdout.read().decode('utf-8')
    ssh.close()

    rows = []
    for line in output.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) < 10:
            continue
        rows.append(parts)
    return rows


class Command(BaseCommand):
    help = 'Importa spettacoli stagioni recenti dal vecchio sito nella history'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        try:
            rows = _fetch_old_shows()
        except Exception as e:
            raise CommandError(f'Errore connessione vecchio sito: {e}')

        self.stdout.write(f'Trovati {len(rows)} show distinti sul vecchio sito')

        seasons  = {s.season_label: s for s in Season.objects.all()}
        sections = {s.id: s for s in Section.objects.all()}
        siatypes = {s.id: s for s in SiaeType.objects.all()}
        venues   = {v.id: v for v in Venue.objects.all()}
        default_section = sections.get(1) or Section.objects.first()
        default_siatype = siatypes.get(1) or SiaeType.objects.first()
        default_venue   = venues.get(1) or Venue.objects.first()

        created = updated = skipped = 0

        for parts in rows:
            title, author, director, company, slug, image = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
            section_id = int(parts[6]) if parts[6].isdigit() else 1
            siatype_id = int(parts[7]) if parts[7].isdigit() else 1
            prima_data_str = parts[8]
            venue_id = int(parts[9]) if parts[9].isdigit() else 1

            try:
                show_date = datetime.strptime(prima_data_str[:10], '%Y-%m-%d').date()
            except ValueError:
                skipped += 1
                continue

            season_label = _season_for_date(show_date)
            if not season_label:
                self.stdout.write(f'  skip (fuori stagioni mappate): {title} ({show_date})')
                skipped += 1
                continue

            season = seasons.get(season_label)
            if not season:
                self.stdout.write(f'  skip (stagione {season_label} mancante): {title}')
                skipped += 1
                continue

            section = sections.get(section_id, default_section)
            siatype = siatypes.get(siatype_id, default_siatype)
            venue   = venues.get(venue_id, default_venue)
            unique_slug = slug or slugify(title)

            exists = HistoryShow.objects.filter(shw_slug=unique_slug).exists()

            if dry_run:
                action = 'aggiorna' if exists else 'crea'
                self.stdout.write(f'  [{action}] {title} ({show_date}) → {season_label}')
                updated += 1 if exists else 0
                created += 0 if exists else 1
                continue

            _, is_new = HistoryShow.objects.update_or_create(
                shw_slug=unique_slug,
                defaults=dict(
                    shw_title=title,
                    shw_author=author or '',
                    shw_director=director or '',
                    shw_theater_company=company or '',
                    shw_date=show_date,
                    shw_season=season,
                    shw_section=section,
                    shw_siaetype=siatype,
                    shw_venue=venue,
                    shw_image=image or 'photos/history/poster_globe_theatre.jpg',
                )
            )
            if is_new:
                created += 1
                self.stdout.write(f'  creato: {title} ({show_date}) → {season_label}')
            else:
                updated += 1
                self.stdout.write(f'  aggiornato: {title} ({show_date}) → {season_label}')

        prefix = '[DRY-RUN] ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'{prefix}Completato: {created} creati, {updated} aggiornati, {skipped} saltati'
        ))
