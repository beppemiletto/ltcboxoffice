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
    venue           = models.ForeignKey(Venue, on_delete=models.CASCADE, blank=True, null=True, default= 1)
    event_slug      = models.CharField(max_length=200, blank=True)
    sold_out        = models.BooleanField(default=False)
    
    def __str__(self) -> str:
        return self.show.slug
    
    @property
    def get_unique_id(self):
        a = self.show.slug
        b = self.date_time.strftime('%Y%m%d')     #Day of the month as string
        c = self.show.shw_code
        return c+'_'+b+'_'+ a 


    def save(self, *args, **kwargs):
        self.event_slug = self.get_unique_id
        if self.pk:
            port_booking: bool = True
        else:
            port_booking: bool = False
        super(Event, self).save(*args, **kwargs)
        # json_filename = self.event_slug+'.json'
        # json_filename_fullpath = os.path.join(settings.HALL_STATUS_FILES_ROOT, json_filename)
            
        json_filename_fullpath = self.get_json_path()
        seats = Seat.objects.filter(active=True)
        event_hall = {}
        for seat in seats:
            seat_status= {
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

        if not os.path.exists(json_filename_fullpath):
            print('writing a new:{}'.format(json_filename_fullpath))
        else:
            print('exist:{}'.format(json_filename_fullpath))
        with open(json_filename_fullpath,'w') as fp:
            json.dump(event_hall,fp,indent=4, separators=(',', ': '))


    def get_json_path(self):
        json_filename = self.event_slug+'.json'
        json_filename_fullpath = os.path.join(settings.HALL_STATUS_FILES_ROOT, json_filename)
        return json_filename_fullpath
    
    def prices(self):
        return [0.0 , self.price_reduced, self.price_full]


    

