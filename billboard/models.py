from django.db import models
from django.urls import reverse





# Create your models here.
class Section(models.Model):
    name                    = models.CharField(max_length=50, unique=True)
    slug                    = models.SlugField(max_length=100, unique=True)
    default_price_full      = models.CharField(max_length=50)
    default_price_reduced   = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.name
    
    def get_url(self):
        return reverse('shows_by_section', args=[self.slug])
    
class Show(models.Model):
    shw_title           = models.CharField(max_length=100, blank=False, default='My Title')
    slug                = models.SlugField(max_length=200, unique=True)
    description         = models.TextField(max_length=2048, blank=True)
    shw_code            = models.CharField(max_length=8, unique=True, blank=True)
    section             = models.ForeignKey(Section, on_delete= models.CASCADE, default=1, blank=True )
    responsible_mail    = models.EmailField(max_length=100, blank=True, default='')
    shw_image           = models.ImageField(upload_to='photos/billboard', blank=True)
    is_in_billboard     = models.BooleanField(default=True, blank=True)
    is_active           = models.BooleanField(default=True, blank=True)

    def __str__(self):
        return self.slug

    def get_url(self):
        return reverse('show_detail', args=[self.section.slug, self.slug])
    