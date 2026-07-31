from django.shortcuts import render, get_object_or_404
from django.utils.text import slugify
from django.db.models import Sum, Count
from collections import Counter, defaultdict
from .models import Season, HistoryShow
from accounts.decorators import socio_required


def _director_slug(name):
    return slugify(name)


def _split_directors(director_str):
    return [n.strip() for n in director_str.replace(' e ', '|').split('|') if n.strip()]


@socio_required
def history_home(request):
    seasons = Season.objects.order_by('season_start_date').annotate(
        show_count=Count('historyshow'),
        total_spectators=Sum('historyshow__shw_spectators'),
    )
    all_shows = HistoryShow.objects.all()
    total_shows = all_shows.count()
    total_spectators = all_shows.aggregate(t=Sum('shw_spectators'))['t'] or 0

    directors_counter = Counter()
    for d in all_shows.values_list('shw_director', flat=True):
        for name in _split_directors(d):
            directors_counter[name] += 1

    top_directors = [
        {'name': name, 'slug': _director_slug(name), 'count': count}
        for name, count in directors_counter.most_common(10)
    ]

    context = {
        'seasons': seasons,
        'total_shows': total_shows,
        'total_spectators': total_spectators,
        'total_seasons': seasons.count(),
        'top_directors': top_directors,
    }
    return render(request, 'history/history_home.html', context)


@socio_required
def season_detail(request, season_label):
    season = get_object_or_404(Season, season_label=season_label)
    shows = HistoryShow.objects.filter(shw_season=season).order_by('shw_date')
    total_spectators = shows.aggregate(t=Sum('shw_spectators'))['t'] or 0

    directors = Counter()
    for d in shows.values_list('shw_director', flat=True):
        for name in _split_directors(d):
            directors[name] += 1

    context = {
        'season': season,
        'shows': shows,
        'total_spectators': total_spectators,
        'directors': [{'name': n, 'slug': _director_slug(n), 'count': c}
                      for n, c in directors.most_common()],
    }
    return render(request, 'history/season_detail.html', context)


@socio_required
def directors_list(request):
    all_shows = HistoryShow.objects.select_related('shw_season').all()

    directors = defaultdict(lambda: {'count': 0, 'spectators': 0, 'seasons': set()})
    for show in all_shows:
        for name in _split_directors(show.shw_director):
            directors[name]['count'] += 1
            directors[name]['spectators'] += show.shw_spectators or 0
            if show.shw_season:
                directors[name]['seasons'].add(show.shw_season.season_label)

    directors_data = sorted(
        [{'name': name, 'slug': _director_slug(name),
          'count': data['count'], 'spectators': data['spectators'],
          'seasons_count': len(data['seasons']), 'seasons': sorted(data['seasons'])}
         for name, data in directors.items()],
        key=lambda x: x['count'], reverse=True
    )

    context = {'directors': directors_data}
    return render(request, 'history/directors_list.html', context)


@socio_required
def director_detail(request, slug):
    all_shows = HistoryShow.objects.select_related('shw_season').order_by('shw_date')

    director_name = None
    shows = []
    for show in all_shows:
        for name in _split_directors(show.shw_director):
            if _director_slug(name) == slug:
                director_name = name
                shows.append(show)
                break

    if director_name is None:
        from django.http import Http404
        raise Http404

    total_spectators = sum(s.shw_spectators or 0 for s in shows)
    seasons = sorted(set(s.shw_season.season_label for s in shows if s.shw_season))

    context = {
        'director_name': director_name,
        'shows': shows,
        'total_spectators': total_spectators,
        'seasons': seasons,
    }
    return render(request, 'history/director_detail.html', context)


@socio_required
def show_detail(request, slug):
    show = get_object_or_404(HistoryShow, shw_slug=slug)
    director_links = [
        {'name': n, 'slug': _director_slug(n)}
        for n in _split_directors(show.shw_director)
    ]
    context = {
        'show': show,
        'director_links': director_links,
    }
    return render(request, 'history/show_detail.html', context)
