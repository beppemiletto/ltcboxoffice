from django.http import HttpResponse
from django.shortcuts import render
from billboard.models import Show
from store.models import Event
from datetime import datetime, timedelta
from dateutil.relativedelta import *
import pytz

def home(request):
    shows = Show.objects.all().filter(is_in_billboard=True, is_active=True)

    if shows.count():
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
    else:
        now = datetime.now()
        year = now.year
        month = now.month
        if month==1 or month==2:
            season = 'Inverno'
            message = "La stagione {}/{} dovrebbe essere in corso. Se non ci sono spettacoli prenotabili è per via di qualche disguido. Ci scusiamo con il pubblico.".format(year-1,year)

        elif month==3 or month==4 or month==5:
            season = 'Primavera'
            message = "La stagione {}/{} dovrebbe essere in corso. Se non ci sono spettacoli prenotabili è per via di qualche disguido. Ci scusiamo con il pubblico.".format(year-1,year)
        elif month==6 or month==7 or month==8:
            season = 'Estate'
            message = "La stagione {}/{} è terminata e il Teatro Comunale è chiuso. Stiamo preparando la stagione {}/{}.".format(year-1,year,year,year+1)
        elif month==9 or month==10 or month==11  or month==12:
            season = 'Autunno'
            message = "La stagione {}/{} dovrebbe essere in corso. Se non ci sono spettacoli prenotabili è per via di qualche disguido. Ci scusiamo con il pubblico.".format(year,year+1)

        context = {
            'season' : season,
            'message' : message,
            'now': now,
            'year': year,
        }

        return render(request, 'home_noshow.html', context)
