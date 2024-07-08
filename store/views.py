from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
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
        shows = Show.objects.all().filter(is_in_billboard=True, is_active=True).order_by('id')
    billboard_list = []

    max_date_time = datetime.now()+relativedelta(hours=18)
    max_date_time = max_date_time.replace(tzinfo=pytz.utc)
    for show in shows:
        shw_events = Event.objects.all().filter(show=show.pk) 
        sell_allowed: bool = False 
        if shw_events.count():
            from_date = datetime.now()+relativedelta(months=36)
            from_date = from_date.replace(tzinfo=pytz.utc)
            for event in shw_events:
                if (event.date_time < from_date) and (event.date_time > max_date_time):
                    from_date = event.date_time
                    price_full = event.price_full
                    price_reduced = event.price_reduced
                    show_url = show.get_url
                    sell_allowed: bool = True

            if sell_allowed:

                billboard_list.append ({
                'title': show.shw_title,
                'slug': show.slug,
                'image': show.shw_image,
                'price_full': price_full,
                'price_reduced': price_reduced,
                'from_date': from_date,
                'show_url': show_url}
                )

    show_count = len(billboard_list)

    paginator = Paginator(billboard_list, 4)
    page = request.GET.get('page')
    paged_shows = paginator.get_page(page)

    context = {
        'billboard': paged_shows,
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
    max_date_time = datetime.now()+relativedelta(hours=18)
    max_date_time = max_date_time.replace(tzinfo=pytz.utc)  
    events = Event.objects.filter(show=show,date_time__gte=max_date_time)
    events_number = events.count()
    prices = ''
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


def search(request):
    if 'keyword' in request.GET :
        keyword = request.GET['keyword']
        print(f'{keyword}')
        if keyword:
            shows = Show.objects.filter(Q(description__icontains=keyword) | Q(shw_title__icontains=keyword))
            billboard_list = []
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

                        billboard_list.append ({
                        'title': show.shw_title,
                        'slug': show.slug,
                        'image': show.shw_image,
                        'price_full': price_full,
                        'price_reduced': price_reduced,
                        'from_date': from_date,
                        'show_url': show_url}
                        )

            show_count = len(billboard_list)

            paginator = Paginator(billboard_list, 4)
            page = request.GET.get('page')
            paged_shows = paginator.get_page(page)

            context = {
                'billboard': billboard_list,
                'show_count': show_count,
                'keyword': keyword,
            }
            return render(request, 'store/store.html', context)
        else:
            return HttpResponse('Non è stata fornita nessuna chiave di ricerca.')

