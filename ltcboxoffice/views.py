from django.http import HttpResponse
from django.shortcuts import render
from billboard.models import Show
from store.models import Event
from datetime import datetime, timedelta
from dateutil.relativedelta import *
import pytz

def home(request):
    shows = Show.objects.all().filter(is_in_billboard=True, is_active=True)
    billboard = {}
    zero_timedelta = timedelta(days=0,seconds=1,microseconds=0,milliseconds=0,minutes=0,hours=0,weeks=0)
    evidence_timedelta = timedelta(days=365)
    evidence_show_found: bool = False
    evidence_show = shows.last()
    for show in shows:
        shw_events = Event.objects.filter(show=show.pk) 
        if shw_events.count():
            from_date = datetime.now()+relativedelta(hours=3) 
            from_date = from_date.replace(tzinfo=pytz.utc)
            for event in shw_events:
                time_gap = event.date_time - from_date
                if time_gap > zero_timedelta and time_gap < evidence_timedelta:
                    evidence_timedelta = time_gap
                    evidence_show = show
                    evidence_show_url = show.get_url
                    date_start = event.date_time
                    evidence_show_found = True

    if not evidence_show_found:
        shw_events = Event.objects.filter(show=show.pk)
        for event in shw_events:
            time_gap = event.date_time - from_date
            if time_gap < evidence_timedelta:
                evidence_timedelta = time_gap
                evidence_show = show
                evidence_show_url = show.get_url
                date_start = event.date_time
              
    billboard[evidence_show.pk]= {
    'title': evidence_show.shw_title,
    'slug': evidence_show.slug,
    'image': evidence_show.shw_image,
    'from_date': date_start,
    'show_url': evidence_show_url,
    }


    context = {
        'billboard': billboard,
    }
    # return HttpResponse("<H1>My Home page</H1>")
    return render(request, 'home.html', context)
