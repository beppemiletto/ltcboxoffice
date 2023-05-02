from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from billboard.models import Show, Section
from .models import Event
from datetime import datetime
from dateutil.relativedelta import *
import pytz


# Create your views here.
def store(request, section_slug=None):
    sections = None
    shows = None
    if section_slug != None:
        sections = get_object_or_404(Section, slug=section_slug)
        shows = Show.objects.filter(section=sections,  is_in_billboard=True, is_active=True)
    else:
        shows = Show.objects.all().filter(is_in_billboard=True, is_active=True)
    billboard = {}
    for show in shows:
        shw_events = Event.objects.all().filter(show=show.pk) 
        sell_allowed: bool = False 
        if shw_events.count():
            from_date = datetime.now()+relativedelta(month=12)
            from_date = from_date.replace(tzinfo=pytz.utc)
            max_date_time = datetime.now()+relativedelta(hours=24)
            max_date_time = max_date_time.replace(tzinfo=pytz.utc)
            for event in shw_events:
                if event.date_time < from_date:
                    from_date = event.date_time
                    price_full = event.price_full
                    price_reduced = event.price_reduced
                    show_url = show.get_url
                    sell_allowed: bool = (event.date_time > max_date_time)

            if sell_allowed:

                billboard[show.pk]= {
                'title': show.shw_title,
                'slug': show.slug,
                'image': show.shw_image,
                'price_full': price_full,
                'price_reduced': price_reduced,
                'from_date': from_date,
                'show_url': show_url
                }

    show_count = len(billboard)

    context = {
        'billboard': billboard,
        'show_count': show_count,
    }
    return render(request, 'store/store.html', context)

def show_detail(request, section_slug, show_slug):
    try:
        show = Show.objects.get(section__slug=section_slug, slug=show_slug)
    except Exception as e:
        raise e


    # section = get_object_or_404(Section, slug=section_slug)
    # show = get_object_or_404(Show, slug=show_slug)
    events = Event.objects.filter(show=show)
    events_number = events.count()
    if events_number > 0:
        for event in events:
            try: 
                price_full = round(float(event.price_full),2)
                price_reduced = round(float(event.price_reduced),2)
                prices = 'Intero: € {} - Ridotto € {}'.format(price_full, price_reduced)
            except TypeError:
                prices = '{}'.format(event.price_full)

    

    context = {
        'events': events,
        'show': show,
        'prices': prices,

    }
    return render(request, 'store/show_detail.html', context)

def select_seats(request, section_slug, show_slug, event_slug):
    section = get_object_or_404(Section, slug=section_slug)
    show = get_object_or_404(Show, slug=show_slug)
    event = get_object_or_404(Event, event_slug=event_slug)
    return redirect('/hall/{}/'.format(event.event_slug))