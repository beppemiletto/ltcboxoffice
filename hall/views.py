from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from store.models import Event
from .models import Row
from subscriptions.utils import get_subscription_price_options
import json, os, datetime

# Create your views here.
def hall(request):
    events = Event.objects.all()
    context = {
        'events': events,
    }
    return render(request, 'hall/hall.html', context)

def hall_detail(request, event_slug=None):
    event = get_object_or_404(Event, event_slug=event_slug)
    json_file_path= os.path.abspath(event.get_json_path())
    with open(json_file_path,'r') as jfp:
        event_data = json.load(jfp)

    # Handle both old format (dict of seats) and new format (dict with 'seats', 'aisles', 'rows_metadata')
    if 'seats' in event_data:
        # New format (v2.0+) with aisles and rows_metadata
        hall_status = event_data['seats']
        aisles = event_data.get('aisles', {'horizontal': [], 'vertical': []})
        rows_metadata = event_data.get('rows_metadata', {})
    else:
        # Old format (v1.0) - backward compatibility
        hall_status = event_data
        aisles = {'horizontal': [], 'vertical': []}
        rows_metadata = {}

    # If seats are empty (JSON not yet initialized), reload from venue config and persist
    if not hall_status:
        hall_status, aisles, rows_metadata = event._load_seats_from_venue_config()
        event_data = {'seats': hall_status, 'aisles': aisles, 'rows_metadata': rows_metadata}
        with open(json_file_path, 'w') as jfp:
            json.dump(event_data, jfp, indent=4, separators=(',', ': '))
    else:
        # Load aisles from venue configuration (overrides event JSON if present)
        venue = event.venue
        if venue and venue.configuration_file:
            config_path = venue.get_config_file_path()
            if config_path and os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        venue_config = json.load(f)
                        venue_data = venue_config.get('venue', {})
                        venue_aisles = venue_data.get('aisles', {})
                        if venue_aisles:
                            aisles = venue_aisles
                except Exception as e:
                    print(f"Error loading venue configuration: {e}")

    if request.method == 'POST':
        selected_seats = request.POST['selected_seats'].split(',')
        try:
            for seat in selected_seats:
                hall_status[seat]['status'] = 3
            # Save back in the same format
            if 'seats' in event_data:
                event_data['seats'] = hall_status
                with open(json_file_path,'w') as jfp:
                    json.dump(event_data,jfp, indent=2)
            else:
                with open(json_file_path,'w') as jfp:
                    json.dump(hall_status,jfp, indent=2)
        except:
            print('Something wrong!')
        return HttpResponse('Il metodo usato era POST e i posti selezionati sono {}'.format(request.POST['selected_seats']))
    else:
        print("Got the GET Method")
        # preparing rows (from JSON metadata instead of DB)
        rows={}
        row ={}
        row_label = ''
        for k, seat in hall_status.items():
            if  row_label != seat['row']:
                if row_label != '':
                    rows[row_label]=row
                row = {}
                row_label = seat['row']

                # Get row metadata from JSON (or fallback to DB for old events)
                row['data'] = {}  # Initialize with empty dict
                if row_label in rows_metadata and rows_metadata[row_label]:
                    try:
                        r_data = rows_metadata[row_label]
                        row['data']= {
                            'name': r_data.get('name', row_label),
                            'off_start': r_data.get('offset_start', 0),
                            'off_end': r_data.get('offset_end', 0),
                            'is_act': r_data.get('is_active', True)
                        }
                    except (KeyError, TypeError) as e:
                        print(f"Error processing rows_metadata for {row_label}: {e}")
                
                # Use DB fallback if metadata wasn't set from JSON
                if not row['data']:
                    try:
                        r_data = Row.objects.get(name = row_label)
                        row['data']= {'name': r_data.name, 'off_start': r_data.offset_start, 'off_end': r_data.offset_end, 'is_act':r_data.is_active}
                    except Row.DoesNotExist:
                        # If row doesn't exist in DB either, use defaults
                        row['data']= {'name': row_label, 'off_start': 0, 'off_end': 0, 'is_act': True}

            row[seat['num_in_row']]= {'status':seat['status'], 'order':seat['order'], 'name':seat['name']}
        if row_label:
            rows[row_label]=row  # last row closure

        # Check user's active subscriptions
        subscription_options = []
        if request.user.is_authenticated:
            subscription_options = get_subscription_price_options(request.user)

        context = {
            'hall_status': hall_status,
            'rows': rows,
            'aisles': aisles,  # Pass aisles to template
            'json_file' : json_file_path,
            'event': event,
            'subscription_options': subscription_options,
        }

        return render(request, 'hall/hall_detail.html', context)






