from django.db import models

# Create your models here.
class Show(models.Model):
    shw_title       = models.CharField(max_length=100, blank=False, default='My Title')
    slug            = models.SlugField(max_length=200, unique=True)
    description     = models.TextField(max_length=2048, blank=True)
    shw_code        = models.CharField(max_length=8, unique=True, blank=True)
    shw_image       = models.ImageField(upload_to='photos/billboard', blank=True)
    is_in_billboard = models.BooleanField(default=True, blank=True)
    is_active       = models.BooleanField(default=True, blank=True)

    def __str__(self):
        return self.shw_title
    