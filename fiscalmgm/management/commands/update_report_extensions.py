"""
Management command per aggiornare le estensioni dei file report da .xls a .xlsx
"""
from django.core.management.base import BaseCommand
from fiscalmgm.models import Report
import os


class Command(BaseCommand):
    help = 'Aggiorna le estensioni dei file report da .xls a .xlsx nel database'

    def handle(self, *args, **options):
        # Trova tutti i report con estensione .xls
        reports = Report.objects.filter(doc_path__endswith='.xls')
        updated_count = 0

        for report in reports:
            old_path = report.doc_path
            new_path = old_path.replace('.xls', '.xlsx')

            self.stdout.write(f'Aggiornamento: {old_path} -> {new_path}')

            # Aggiorna il path nel database
            report.doc_path = new_path
            report.save()

            # Se il file esiste, rinominalo
            full_old_path = os.path.join('media', 'siae_reports', old_path)
            full_new_path = os.path.join('media', 'siae_reports', new_path)

            if os.path.exists(full_old_path):
                os.rename(full_old_path, full_new_path)
                self.stdout.write(self.style.SUCCESS(f'  File rinominato: {old_path}'))

            updated_count += 1

        if updated_count > 0:
            self.stdout.write(self.style.SUCCESS(f'\nAggiornati {updated_count} record nel database'))
        else:
            self.stdout.write(self.style.WARNING('Nessun record da aggiornare'))
