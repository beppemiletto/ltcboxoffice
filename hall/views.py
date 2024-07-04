from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from store.models import Event
from .models import Row
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
        hall_status = json.load(jfp)
    if request.method == 'POST':
        selected_seats = request.POST['selected_seats'].split(',')
        try:
            for seat in selected_seats:
                hall_status[seat]['status'] = 3 
            with open(json_file_path,'w') as jfp:
                json.dump(hall_status,jfp, indent=2)
        except:
            print('Something wrong!')
        return HttpResponse('Il metodo usato era POST e i posti selezionati sono {}'.format(request.POST['selected_seats']))
    else:
        print("Got the GET Method")
        # preparing rows
        row_hall = Row.objects.all()
        rows={}
        row ={}
        row_label = ''
        for k, seat in hall_status.items():
            if  row_label != seat['row']:
                if row_label != '':
                    rows[row_label]=row
                row = {}
                row_label = seat['row']
                r_data = Row.objects.get(name = row_label)
                row['data']= {'name': r_data.name, 'off_start': r_data.offset_start, 'off_end': r_data.offset_end, 'is_act':r_data.is_active}
            row[seat['num_in_row']]= {'status':seat['status'], 'order':seat['order'], 'name':seat['name']}
        rows[row_label]=row  # last row closure



        context = {
            'hall_status': hall_status,
            'rows': rows,
            'json_file' : json_file_path,
            'event': event,
        }

        return render(request, 'hall/hall_detail.html', context)






