from django.shortcuts import get_object_or_404
from .models import Section


def menu_links(request):
    links = Section.objects.all()
    return dict(links=links)
