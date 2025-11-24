from django.db import models
from billboard.models import Show, Venue
from hall.models import Seat
from django.conf import settings
import os, json

# Create your models here.
class Event(models.Model):
    show            = models.ForeignKey(Show, on_delete=models.CASCADE)
    date_time       = models.DateTimeField()
    price_full      = models.FloatField()
    price_reduced   = models.FloatField()
    vat_rate        = models.FloatField(default=10)
    venue           = models.ForeignKey(Venue, on_delete=models.CASCADE, blank=True, null=True, default=2)
    event_slug      = models.CharField(max_length=200, blank=True)
    sold_out        = models.BooleanField(default=False)
    booking_deadline_hours = models.PositiveIntegerField(
        default=3,
        verbose_name="Ore limite prenotazione",
        help_text="Numero di ore prima dell'evento entro cui è possibile prenotare (da 1 a 24 ore)"
    )
    
    def __str__(self) -> str:
        return f'{self.show.slug} - {self.date_time}'
    
    @property
    def get_unique_id(self):
        a = self.show.slug
        b = self.date_time.strftime('%Y%m%d')     #Day of the month as string
        c = self.show.shw_code
        # Include event pk to support multiple events on the same day
        # If event is not yet saved (no pk), use timestamp for uniqueness
        if self.pk:
            d = str(self.pk)
        else:
            # For new events, use time component temporarily
            d = self.date_time.strftime('%H%M')
        return c+'_'+b+'_'+d+'_'+ a 

    def get_booking_deadline(self):
        """Calcola il timestamp limite per le prenotazioni basato su booking_deadline_hours"""
        from datetime import timedelta
        import pytz
        
        deadline_hours = self.booking_deadline_hours if self.booking_deadline_hours is not None else 3
        deadline = self.date_time - timedelta(hours=deadline_hours)
        
        # Assicura che abbia timezone
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=pytz.utc)
        
        return deadline
    
    def is_bookable(self):
        """Verifica se l'evento è ancora prenotabile in base al deadline"""
        from datetime import datetime
        import pytz
        
        now = datetime.now(pytz.utc)
        deadline = self.get_booking_deadline()
        
        return now < deadline and not self.sold_out 


    def save(self, *args, **kwargs):
        # Track old slug for file renaming if date/show changes
        old_slug = None
        old_json_path = None
        is_new = self.pk is None

        if self.pk:  # Existing event
            port_booking: bool = True
            try:
                # Get old event data before saving
                old_event = Event.objects.get(pk=self.pk)
                old_slug = old_event.event_slug
                old_json_path = old_event.get_json_path()
            except Event.DoesNotExist:
                pass
        else:
            port_booking: bool = False

        # Update event_slug based on current show/date
        self.event_slug = self.get_unique_id

        # Save to database
        super(Event, self).save(*args, **kwargs)

        # For new events, update slug again now that we have pk
        if is_new:
            old_slug = self.event_slug
            self.event_slug = self.get_unique_id
            # Save again with proper slug containing pk
            super(Event, self).save(update_fields=['event_slug'])

        # Handle JSON file renaming if slug changed
        if old_slug and old_slug != self.event_slug:
            self._rename_json_file(old_json_path)
            
        json_filename_fullpath = self.get_json_path()

        # Load seats, aisles, and row metadata from venue configuration file
        event_hall, venue_aisles, rows_metadata = self._load_seats_from_venue_config()
        if port_booking:
            from orders.models import OrderEvent
            orderevents = OrderEvent.objects.filter(event_id=self.pk)
            if orderevents.count() > 0:
                for orderevent in orderevents:
                    if orderevent.expired:
                        state = 5  # order expired so status 5 in event's HALL json file 
                    else:
                        state = 1 # order GOOD not expired so status 1 in event's HALL json file 
                    for seat_price in orderevent.seats_price.split(','):
                        if '$' in seat_price:
                            seat, price = seat_price.split('$')
                            event_hall[seat]['status'] = state
                            event_hall[seat]['order'] = orderevent.orderevent_number
                        else:
                            print("malformed orderevent seat_price: @ {} the seat_price string {}".format(orderevent.orderevent_number, orderevent.seats_price))

            from boxoffice.models import BoxOfficeBookingEvent
            bookings = BoxOfficeBookingEvent.objects.filter(event_id=self.pk)
            if bookings.count() > 0:
                for booking in bookings:
                    if booking.expired:
                        state = 5 # order expired so status 5 in event's HALL json file 
                    else:
                        state = 1 # order GOOD not expired so status 1 in event's HALL json file 
                    for seat_price in booking.seats_price.split(','):
                        if '$' in seat_price:
                            seat, price = seat_price.split('$')
                            event_hall[seat]['status'] = state
                            event_hall[seat]['order'] = booking.booking_number
                        else:
                            print("malformed booking seat_price:  @ {} the seat_price string {}".format(booking.booking_number, booking.seats_price))

        # Prepare complete event data including aisles and row metadata
        event_data = {
            'seats': event_hall,
            'aisles': venue_aisles,
            'rows_metadata': rows_metadata
        }

        if not os.path.exists(json_filename_fullpath):
            print('writing a new:{}'.format(json_filename_fullpath))
        else:
            print('exist:{}'.format(json_filename_fullpath))
        with open(json_filename_fullpath,'w') as fp:
            json.dump(event_data,fp,indent=4, separators=(',', ': '))


    def get_json_path(self):
        json_filename = self.event_slug+'.json'
        json_filename_fullpath = os.path.join(settings.HALL_STATUS_FILES_ROOT, json_filename)
        return json_filename_fullpath
    
    def _load_seats_from_venue_config(self):
        """Load seats, aisles, and row metadata from venue configuration file
        Returns: (event_hall dict, aisles dict, rows_metadata dict)
        """
        event_hall = {}
        venue_aisles = {}
        rows_metadata = {}

        # Get venue (use default Teatro Cambiano if not set)
        venue = self.venue
        if not venue:
            venue = Venue.objects.filter(slug='teatro-cambiano').first()
            if not venue:
                # Fallback to database seats if no venue configured
                return self._load_seats_from_database(), {}, {}

        # Get configuration file path
        config_path = venue.get_config_file_path()
        if not config_path or not os.path.exists(config_path):
            # Fallback to database seats if no config file
            return self._load_seats_from_database(), {}, {}

        # Load JSON configuration
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Extract aisles configuration (v2.0 format)
            venue_data = config_data.get('venue', {})
            venue_aisles = venue_data.get('aisles', {
                'horizontal': [],
                'vertical': []
            })

            # Build event_hall and rows_metadata from configuration
            seat_number = 1
            for row_data in config_data.get('rows', []):
                row_name = row_data['name']

                # Skip inactive rows
                if not row_data.get('is_active', True):
                    continue

                # Store row metadata (offset_start, offset_end, is_active)
                rows_metadata[row_name] = {
                    'name': row_name,
                    'offset_start': row_data.get('offset_start', 0),
                    'offset_end': row_data.get('offset_end', 0),
                    'is_active': row_data.get('is_active', True)
                }

                for seat_data in row_data.get('seats', []):
                    num_in_row = str(seat_data['num']).zfill(2)
                    seat_name = f'{row_name}{num_in_row}'

                    seat_status = {
                        "active": seat_data.get('active', True),
                        "id": seat_number,
                        "name": seat_name,
                        "num_in_row": num_in_row,
                        "number": seat_number,
                        "row": row_name,
                        "status": 0,
                        "order": None,
                    }
                    event_hall[seat_name] = seat_status
                    seat_number += 1

            return event_hall, venue_aisles, rows_metadata

        except Exception as e:
            print(f"Error loading venue config for event {self.event_slug}: {e}")
            # Fallback to database seats
            return self._load_seats_from_database(), {}, {}
    
    def _load_seats_from_database(self):
        """Fallback method to load seats from database (legacy)"""
        event_hall = {}
        seats = Seat.objects.filter(active=True)
        
        for seat in seats:
            seat_status = {
                "active": True,
                "id": seat.pk,
                "name": seat.name,
                "num_in_row": seat.num_in_row,
                "number": seat.number,
                "row": seat.row,
                "status": 0,
                "order": None,
            }
            event_hall[seat.name] = seat_status
        
        return event_hall
    
    def _rename_json_file(self, old_json_path):
        """Rename JSON file when event slug changes (date/show modified)"""
        if old_json_path and os.path.exists(old_json_path):
            new_json_path = self.get_json_path()
            try:
                os.rename(old_json_path, new_json_path)
                print(f'Renamed JSON: {os.path.basename(old_json_path)} → {os.path.basename(new_json_path)}')
            except Exception as e:
                print(f"Error renaming JSON file: {e}")
    
    def delete_json_file(self):
        """Delete JSON file associated with this event"""
        json_path = self.get_json_path()
        if json_path and os.path.exists(json_path):
            try:
                os.remove(json_path)
                print(f'Deleted JSON file: {os.path.basename(json_path)}')
                return True
            except Exception as e:
                print(f"Error deleting JSON file: {e}")
                return False
        return False
    
    def delete(self, *args, **kwargs):
        """Override delete to remove JSON file when event is deleted"""
        # Delete associated JSON file first
        self.delete_json_file()
        # Then delete the event from database
        super(Event, self).delete(*args, **kwargs)
    
    def prices(self):
        return [0.0 , self.price_reduced, self.price_full]


    

