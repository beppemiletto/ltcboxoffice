from django.http import HttpResponse
from django.shortcuts import render
from billboard.models import Show
from store.models import Event
from datetime import datetime, timedelta
from dateutil.relativedelta import *
import pytz


def _history_context():
    from history.models import Season, HistoryShow
    return {
        'history_seasons': Season.objects.count(),
        'history_shows': HistoryShow.objects.count(),
    }

def home(request):
    shows = Show.objects.all().filter(is_in_billboard=True, is_active=True)

    if shows.count():
        billboard = {}
        zero_timedelta = timedelta(days=0,seconds=1,microseconds=0,milliseconds=0,minutes=0,hours=0,weeks=0)
        evidence_timedelta = timedelta(days=365)
        evidence_show_found: bool = False
        evidence_show = shows.last()
        date_start = None
        evidence_show_url = None

        for show in shows:
            shw_events = Event.objects.filter(show=show.pk).order_by('date_time')
            if shw_events.count():
                now = datetime.now(pytz.utc)
                for event in shw_events:
                    # Usa il metodo is_bookable() per controllare la deadline dinamica
                    if event.is_bookable():
                        time_gap = event.date_time - now
                        if time_gap > zero_timedelta and time_gap < evidence_timedelta:
                            evidence_timedelta = time_gap
                            evidence_show = show
                            evidence_show_url = show.get_url()
                            date_start = event.date_time
                            evidence_show_found = True
                            break  # Prendi il primo evento prenotabile per questo show

        if not evidence_show_found:
            # Fallback: prende l'ultimo show comunque
            shw_events = Event.objects.filter(show=evidence_show.pk).order_by('date_time')
            now = datetime.now(pytz.utc)
            for event in shw_events:
                if event.is_bookable():
                    evidence_show_url = evidence_show.get_url()
                    date_start = event.date_time
                    evidence_show_found = True
                    break

        # If still no bookable event found, show the no bookable events page
        if not evidence_show_found:
            context = {
                'message': 'Al Teatro Comunale di Cambiano non ci sono spettacoli prenotabili. Il Laboratorio Teatrale di Cambiano APS sta preparando il nuovo programma e presto sarà prenotabile.',
                **_history_context(),
            }
            return render(request, 'no_bookable_events.html', context)

        # Only add to billboard if we have at least a show URL
        if evidence_show_url is None:
            evidence_show_url = evidence_show.get_url()

        billboard[evidence_show.pk]= {
        'title': evidence_show.shw_title,
        'slug': evidence_show.slug,
        'image': evidence_show.shw_image,
        'from_date': date_start,
        'show_url': evidence_show_url,
        }


        context = {
            'billboard': billboard,
            **_history_context(),
        }
        return render(request, 'home.html', context)
    else:
        now = datetime.now()
        year = now.year
        month = now.month
        # month =1 # for test only to be removed
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
