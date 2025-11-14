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

class SiaeType(models.Model):
    code = models.CharField(max_length=2, unique=True, editable=True )
    description = models.CharField(max_length=120, editable=True)
    iva = models.PositiveSmallIntegerField(default=10)

    def __str__(self):
        return f"{self.code} - {self.description}"

    def get_full(self):
        return f"codice SIAE {self.code} - Descrizione: {self.description} - IVA {self.iva} %"


class Show(models.Model):
    shw_title           = models.CharField(max_length=100, blank=False, default='My Title')
    shw_theater_company = models.CharField(max_length=100, blank=False, default='Laboratorio Teatrale di Cambiano')
    shw_author          = models.CharField(max_length=100, blank=False, default='My Author')
    shw_director        = models.CharField(max_length=100, blank=False, default='My Director')
    slug                = models.SlugField(max_length=200, unique=True)
    description         = models.TextField(max_length=2048, blank=True)
    shw_code            = models.CharField(max_length=8, unique=True, blank=True)
    section             = models.ForeignKey(Section, on_delete= models.CASCADE, default=1, blank=True )
    responsible_mail    = models.EmailField(max_length=100, blank=True, default='')
    shw_image           = models.ImageField(upload_to='photos/billboard', blank=True)
    siaetype            = models.ForeignKey(SiaeType, on_delete=models.CASCADE, default=2, blank=True)
    is_in_billboard     = models.BooleanField(default=True, blank=True)
    is_active           = models.BooleanField(default=True, blank=True)

    def __str__(self):
        return self.slug

    def get_url(self):
        return reverse('show_detail', args=[self.section.slug, self.slug])
    

class Venue(models.Model):
    name                    = models.CharField(max_length=50, unique=True)
    slug                    = models.SlugField(max_length=100, unique=True)
    address                 = models.CharField(max_length=100 )
    capacity                = models.PositiveIntegerField(default=234)
    ba_code_siae            = models.CharField(max_length=13, default="0050450366484" )
    local_code_siae         = models.CharField(max_length=5, default="  045" )
    configuration_file      = models.FileField(
        upload_to='venue_configs/',
        blank=True,
        null=True,
        help_text="Upload venue seating configuration file (JSON or XML format)"
    )

    def __str__(self) -> str:
        return self.name
    
    def get_config_file_path(self):
        """Returns the path to the uploaded configuration file"""
        if self.configuration_file:
            return self.configuration_file.path
        return None
    
    def get_config_file_format(self):
        """Returns the format of the configuration file (json or xml)"""
        if self.configuration_file:
            import os
            ext = os.path.splitext(self.configuration_file.name)[1].lower()
            if ext == '.json':
                return 'json'
            elif ext == '.xml':
                return 'xml'
        return None
    
    def save(self, *args, **kwargs):
        """Save venue instance"""
        super().save(*args, **kwargs)
        # Note: Auto-loading configuration will be available
        # after merging the feature/venue-management branch with
        # venue FK relationships in Seat and Row models
    