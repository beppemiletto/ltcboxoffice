from django.db import models
from accounts.models import Account
from store.models import Event
from orders.models import Payment
from django.utils import timezone
from datetime import timedelta


class SubscriptionType(models.Model):
    """
    Tipologia di abbonamento: Intero, Ridotto, Omaggio
    Es: "Abbonamento 4 ingressi ridotti", "Abbonamento 8 ingressi interi"
    """
    TYPE_CHOICES = (
        ('FULL', 'Intero'),
        ('REDUCED', 'Ridotto'),
        ('COMPLIMENTARY', 'Omaggio'),
    )
    
    name = models.CharField(max_length=100, verbose_name="Nome Abbonamento", 
                           help_text="Es: Abbonamento 4 ingressi ridotti")
    code_prefix = models.CharField(max_length=10, verbose_name="Prefisso Codice",
                                   help_text="Es: R4, I8, I4, R8")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='FULL', verbose_name="Tipo")
    description = models.TextField(blank=True, verbose_name="Descrizione")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prezzo")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, 
                                          verbose_name="Sconto %",
                                          help_text="Percentuale sconto rispetto al prezzo pieno")
    max_events = models.PositiveIntegerField(verbose_name="Numero Eventi Inclusi")
    valid_days = models.PositiveIntegerField(default=365, verbose_name="Giorni di Validità")
    is_active = models.BooleanField(default=True, verbose_name="Attivo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tipo Abbonamento"
        verbose_name_plural = "Tipi Abbonamento"
        ordering = ['type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()}) - {self.max_events} eventi"


class Subscription(models.Model):
    """
    Abbonamento venduto a un cliente
    """
    STATUS_CHOICES = (
        ('ACTIVE', 'Attivo'),
        ('EXPIRED', 'Scaduto'),
        ('EXHAUSTED', 'Esaurito'),
        ('CANCELLED', 'Annullato'),
    )
    
    subscription_number = models.CharField(max_length=50, unique=True, verbose_name="Numero Abbonamento")
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='subscriptions', verbose_name="Cliente")
    subscription_type = models.ForeignKey(SubscriptionType, on_delete=models.PROTECT, verbose_name="Tipo Abbonamento")
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Pagamento")
    
    # Validità
    valid_from = models.DateField(verbose_name="Valido Da")
    valid_to = models.DateField(verbose_name="Valido Fino")
    
    # Contatori utilizzo
    events_included = models.PositiveIntegerField(verbose_name="Eventi Inclusi")
    events_used = models.PositiveIntegerField(default=0, verbose_name="Eventi Utilizzati")
    
    # Barcode per identificazione fisica
    barcode_path = models.CharField(max_length=512, null=True, blank=True, verbose_name="Percorso Barcode")
    
    # Stato
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', verbose_name="Stato")
    
    # Note
    notes = models.TextField(blank=True, verbose_name="Note")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Abbonamento"
        verbose_name_plural = "Abbonamenti"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subscription_number']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.subscription_number} - {self.user.full_name()} ({self.subscription_type.name})"
    
    def remaining_events(self):
        """Calcola eventi rimanenti"""
        if self.events_included is None or self.events_used is None:
            return 0
        return self.events_included - self.events_used
    
    def is_valid(self):
        """Verifica se l'abbonamento è valido e utilizzabile"""
        if self.status != 'ACTIVE':
            return False
        if not self.valid_to or self.valid_to < timezone.now().date():
            return False
        if self.events_included is None or self.events_used is None:
            return False
        if self.events_used >= self.events_included:
            return False
        return True
    
    def use_event(self):
        """Incrementa il contatore di utilizzo e aggiorna lo stato"""
        self.events_used += 1
        if self.events_used >= self.events_included:
            self.status = 'EXHAUSTED'
        self.save()
    
    def save(self, *args, **kwargs):
        # Genera subscription_number se nuovo
        # Formato: {PREFIX}-{progressive:04d}  Es: R4-0001, I8-0012
        if not self.subscription_number:
            prefix = self.subscription_type.code_prefix
            last_sub = Subscription.objects.filter(
                subscription_type=self.subscription_type
            ).order_by('-subscription_number').first()
            
            if last_sub and last_sub.subscription_number:
                try:
                    last_num = int(last_sub.subscription_number.split('-')[1])
                    new_num = last_num + 1
                except (IndexError, ValueError):
                    new_num = 1
            else:
                new_num = 1
            
            self.subscription_number = f'{prefix}-{new_num:04d}'
        
        # Auto-calcola valid_to se non impostato
        if not self.valid_to and self.valid_from:
            self.valid_to = self.valid_from + timedelta(days=self.subscription_type.valid_days)
        
        # Auto-aggiorna status se scaduto
        if self.valid_to and self.valid_to < timezone.now().date() and self.status == 'ACTIVE':
            self.status = 'EXPIRED'
        
        super().save(*args, **kwargs)


class SubscriptionUsage(models.Model):
    """
    Registro utilizzo abbonamento per ingresso a evento
    """
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='usages', verbose_name="Abbonamento")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="Evento")
    seat = models.CharField(max_length=10, verbose_name="Posto")
    
    # Registrazione utilizzo
    used_at = models.DateTimeField(auto_now_add=True, verbose_name="Data/Ora Utilizzo")
    used_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name='subscription_validations', verbose_name="Validato Da")
    
    # Link opzionale al payment/orderevent se utilizzato in combinazione con vendita
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Pagamento Associato")
    
    notes = models.TextField(blank=True, verbose_name="Note")
    
    class Meta:
        verbose_name = "Utilizzo Abbonamento"
        verbose_name_plural = "Utilizzi Abbonamenti"
        ordering = ['-used_at']
        unique_together = [['subscription', 'event', 'seat']]  # Impedisce doppio utilizzo stesso posto
        indexes = [
            models.Index(fields=['subscription', 'event']),
            models.Index(fields=['event', 'used_at']),
        ]
    
    def __str__(self):
        return f"{self.subscription.subscription_number} - {self.event.show.shw_title} - Posto {self.seat}"
    
    def save(self, *args, **kwargs):
        # Primo salvataggio: incrementa contatore abbonamento
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            self.subscription.use_event()

