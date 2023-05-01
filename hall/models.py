from django.db import models

# Create your models here.
class Seat(models.Model):
    name        = models.CharField(max_length=3,unique=True, blank=False)
    row         = models.CharField(max_length=1, blank=False)
    num_in_row  = models.CharField(max_length=2, blank=False)
    number      = models.IntegerField()
    active      = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class Row(models.Model):
    name            = models.CharField(max_length=1,unique=True)
    offset_start    = models.IntegerField()
    offset_end      = models.IntegerField()
    is_active       = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name