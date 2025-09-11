from django.db import models
from billboard.models import Section, SiaeType, Venue
from django.conf import settings
from django.urls import reverse
import os

class Season(models.Model):
    season_label        = models.CharField(max_length=50, blank=True, unique=True)
    season_start_date   = models.DateField()
    season_end_date     = models.DateField()
    season_description  = models.TextField(max_length=2048, blank=True)

    def __str__(self):
        return self.season_label

class HistoryShow(models.Model):
    shw_title           = models.CharField(max_length=100, blank=False, default='My Title')
    shw_theater_company = models.CharField(max_length=100, blank=False, default='Laboratorio Teatrale di Cambiano')
    shw_author          = models.CharField(max_length=100, blank=False, default='My Author')
    shw_director        = models.CharField(max_length=100, blank=False, default='My Director')
    shw_slug            = models.SlugField(max_length=200, unique=True)
    shw_season          = models.ForeignKey(Season, on_delete=models.DO_NOTHING , default=1, blank = True)
    shw_date            = models.DateField()
    shw_description     = models.TextField(max_length=2048, blank=True)
    shw_spectators      = models.IntegerField(default=0, blank=True)
    shw_section         = models.ForeignKey(Section, on_delete= models.CASCADE, default=1, blank=True )
    shw_image           = models.ImageField(upload_to='photos/history', blank=True,default='photos/history/poster_globe_theatre.jpg')
    shw_siaetype        = models.ForeignKey(SiaeType, on_delete=models.CASCADE, default=1, blank=True)
    shw_venue           = models.ForeignKey(Venue, on_delete=models.DO_NOTHING, default=1, blank=True )

    def __str__(self):
        return self.shw_slug

    def get_url(self):
        return reverse('show_detail', args=[self.shw_section.slug, self.shw_slug])


    
