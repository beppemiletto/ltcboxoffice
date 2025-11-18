"""
Task Celery per cleanup automatico carrelli abbandonati
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from boxoffice.models import SellingSeats
import json
import os


@shared_task(name='boxoffice.cleanup_abandoned_carts')
def cleanup_abandoned_carts_task(timeout_minutes=15):
    """
    Task Celery per liberare automaticamente i posti abbandonati nei carrelli.
    
    Args:
        timeout_minutes: Timeout in minuti per considerare un carrello abbandonato (default: 15)
    
    Returns:
        dict: Riepilogo operazione con statistiche
    """
    cutoff_time = timezone.now() - timedelta(minutes=timeout_minutes)
    
    # Query posti abbandonati
    abandoned_seats = SellingSeats.objects.filter(
        orderevent__isnull=True,
        created_at__lt=cutoff_time
    ).select_related('event')
    
    if not abandoned_seats.exists():
        return {
            'status': 'success',
            'message': 'Nessun carrello abbandonato trovato',
            'freed_seats': 0,
            'deleted_records': 0,
            'updated_events': 0
        }
    
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
    
    freed_count = 0
    updated_events = set()
    errors = []
    
    # Aggiorna JSON eventi
    for event_id, data in events_dict.items():
        event = data['event']
        seats = data['seats']
        
        try:
            json_file_path = os.path.abspath(event.get_json_path())
            
            with open(json_file_path, 'r') as jfp:
                hall_status = json.load(jfp)
            
            # Libera posti
            for seat in seats:
                if seat.seat in hall_status and hall_status[seat.seat]['status'] == 4:
                    hall_status[seat.seat]['status'] = 0
                    hall_status[seat.seat]['order'] = ''
                    freed_count += 1
            
            # Salva JSON
            with open(json_file_path, 'w') as jfp:
                json.dump(hall_status, jfp, indent=2)
            
            updated_events.add(event_id)
            
        except Exception as e:
            errors.append(f"Evento {event_id}: {str(e)}")
    
    # Elimina record database
    deleted_count = abandoned_seats.count()
    abandoned_seats.delete()
    
    result = {
        'status': 'success' if not errors else 'partial',
        'freed_seats': freed_count,
        'deleted_records': deleted_count,
        'updated_events': len(updated_events),
        'timeout_minutes': timeout_minutes,
        'timestamp': timezone.now().isoformat()
    }
    
    if errors:
        result['errors'] = errors
    
    return result
