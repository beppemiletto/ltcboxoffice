"""
Comando management per liberare i posti abbandonati nei carrelli.

Uso:
    python manage.py cleanup_abandoned_carts
    python manage.py cleanup_abandoned_carts --minutes 20  # Custom timeout
    python manage.py cleanup_abandoned_carts --dry-run     # Solo mostra cosa verrebbe eliminato
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from boxoffice.models import SellingSeats
from store.models import Event
import json
import os


class Command(BaseCommand):
    help = 'Libera i posti nei carrelli abbandonati dopo un timeout specificato'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes',
            type=int,
            default=15,
            help='Timeout in minuti per considerare un carrello abbandonato (default: 15)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra cosa verrebbe fatto senza effettuare modifiche',
        )
        parser.add_argument(
            '--event-id',
            type=int,
            help='Limita il cleanup a un evento specifico',
        )

    def handle(self, *args, **options):
        timeout_minutes = options['minutes']
        dry_run = options['dry_run']
        event_id = options.get('event_id')

        # Calcola il timestamp di cutoff
        cutoff_time = timezone.now() - timedelta(minutes=timeout_minutes)

        self.stdout.write(
            self.style.WARNING(
                f'Cercando carrelli abbandonati da più di {timeout_minutes} minuti...'
            )
        )

        # Query per posti non finalizzati (senza OrderEvent)
        abandoned_query = SellingSeats.objects.filter(
            orderevent__isnull=True,
            created_at__lt=cutoff_time
        ).select_related('event')

        if event_id:
            abandoned_query = abandoned_query.filter(event_id=event_id)

        abandoned_seats = list(abandoned_query)

        if not abandoned_seats:
            self.stdout.write(self.style.SUCCESS('✓ Nessun carrello abbandonato trovato.'))
            return

        # Raggruppa per evento
        events_dict = {}
        for seat in abandoned_seats:
            event_id = seat.event.id
            if event_id not in events_dict:
                events_dict[event_id] = {
                    'event': seat.event,
                    'seats': []
                }
            events_dict[event_id]['seats'].append(seat)

        # Mostra riepilogo
        self.stdout.write(
            self.style.WARNING(
                f'\n⚠ Trovati {len(abandoned_seats)} posti in {len(events_dict)} eventi:'
            )
        )

        for event_id, data in events_dict.items():
            event = data['event']
            seats = data['seats']
            self.stdout.write(
                f"\n  Evento: {event.show.shw_title} ({event.date_time.strftime('%d/%m/%Y %H:%M')})"
            )
            self.stdout.write(f"  Posti da liberare: {len(seats)}")
            
            # Mostra dettagli posti
            seats_list = [s.seat for s in seats]
            sessions = set(s.session_id[:8] for s in seats if s.session_id)
            
            self.stdout.write(f"    Posti: {', '.join(sorted(seats_list))}")
            self.stdout.write(f"    Sessioni: {len(sessions)} diverse")
            
            # Età più vecchia
            oldest = min(seats, key=lambda s: s.created_at)
            age_minutes = int((timezone.now() - oldest.created_at).total_seconds() / 60)
            self.stdout.write(f"    Più vecchio: {age_minutes} minuti fa")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\n🔍 DRY RUN - Nessuna modifica effettuata (rimuovi --dry-run per applicare)'
                )
            )
            return

        # Conferma dall'utente
        if not options.get('verbosity', 1) == 0:  # Skip prompt in quiet mode
            confirm = input(f'\nConfermi di voler liberare {len(abandoned_seats)} posti? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.ERROR('✗ Operazione annullata'))
                return

        # Procedi con cleanup
        self.stdout.write(self.style.WARNING('\n🔄 Esecuzione cleanup...'))
        
        freed_count = 0
        updated_events = set()

        for event_id, data in events_dict.items():
            event = data['event']
            seats = data['seats']
            
            # Aggiorna JSON dell'evento
            json_file_path = os.path.abspath(event.get_json_path())
            
            try:
                with open(json_file_path, 'r') as jfp:
                    hall_status = json.load(jfp)
                
                # Libera i posti nel JSON
                for seat in seats:
                    if seat.seat in hall_status:
                        old_status = hall_status[seat.seat]['status']
                        if old_status == 4:  # In carrello
                            hall_status[seat.seat]['status'] = 0  # Libero
                            hall_status[seat.seat]['order'] = ''
                            freed_count += 1
                
                # Salva JSON aggiornato
                with open(json_file_path, 'w') as jfp:
                    json.dump(hall_status, jfp, indent=2)
                
                updated_events.add(event_id)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Evento {event_id}: liberati {len(seats)} posti nel JSON'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Errore aggiornamento JSON evento {event_id}: {e}'
                    )
                )

        # Elimina record SellingSeats dal database
        deleted_count, _ = abandoned_query.delete()

        # Riepilogo finale
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Cleanup completato:'
            )
        )
        self.stdout.write(f'  - {deleted_count} record SellingSeats eliminati dal database')
        self.stdout.write(f'  - {freed_count} posti liberati nei file JSON')
        self.stdout.write(f'  - {len(updated_events)} eventi aggiornati')
        
        # Suggerimento per automazione
        if timeout_minutes == 15:
            self.stdout.write(
                self.style.WARNING(
                    '\n💡 Suggerimento: Aggiungi questo comando a crontab per esecuzione automatica:'
                )
            )
            self.stdout.write('   */15 * * * * cd /path/to/project && python manage.py cleanup_abandoned_carts')
