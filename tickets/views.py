from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.templatetags.static import static
from django.contrib.auth.decorators import login_required

from .models import Ticket
from .forms import TicketListForm
from billboard.models import Show
from store.models import Event
from orders.models import OrderEvent
from .reportlab_ticket_printer import TicketPrinter, BookingPrinter
from datetime import datetime
import pytz
import os
import locale

# Create your views here.
def tickets(request):
    show_list = Show.objects.filter(is_in_billboard=True, is_active=True)
    show_dict = dict()
    for show in show_list:
        event_list = Event.objects.filter(show=show)
        show_dict[show.pk] = {
            'show':show,
            'event_list': event_list,
                              }


    context = {
        'show_dict': show_dict,

    }
    return render(request, 'tickets/tickets.html', context)

def event_list(request, event_slug):
    context ={

    }
    return render(request, 'tickets/event-list.html', context)

@login_required(login_url= 'login')
def print_ticket(request):
    order = int(request.GET['order'])
    orderevents = OrderEvent.objects.filter(order=order)

    tickets_list = []
    for ordereventobj in orderevents:
        event = Event.objects.get(id=ordereventobj.event.pk)
        show = Show.objects.get(id=event.show.pk)

        seats_dict = ordereventobj.seats_dict()
        # verifica utente per contesto di vendita
        # se utente Staff allora assume vendita in cassa
        if request.user.is_staff:
            if request.user.first_name == 'Cassa':
                sell_code = 'Cassa'
            else:
                sell_code = None
        else:
            sell_code = None
        
        if event.price_full == 0.0 and event.price_reduced == 0.00:
            sell_code = 'Prenotazione'

        # event_tickets = Ticket.objects.filter(orderevent__event=event)
        



        for k, seat in seats_dict.items():
            try:
                tickets_all = Ticket.objects.filter(orderevent__event=event)
                total_tickets_x_event = tickets_all.count()
                tickets_x_seat = tickets_all.filter(seat = k)
                how_many = tickets_x_seat.count()
                if how_many == 0:
                    action_ticket = "make_new"
                elif how_many == 1:
                    ticket = tickets_x_seat.first()
                    action_ticket = "change_it"
                elif how_many > 1:
                    count = 0
                    for single_ticket in tickets_x_seat:
                        if count == 0:
                            ticket = single_ticket
                        else:
                            single_ticket.delete()
                        count += 1
                    action_ticket = "change_it"
            except:
                print('Errore sulla query per generazione dei biglietti')

            if action_ticket == "make_new":
                price = int(seat[-1])
                ticket = Ticket()
                ticket.price = price
                ticket.payment = ordereventobj.payment
                ticket.orderevent = ordereventobj
                ticket.event = ordereventobj.event
                ticket.seat = k
                ticket.user = ordereventobj.user
                serial = total_tickets_x_event + 1
                ticket.number=f"{ticket.sell_mode[0]}{event.date_time.strftime('%Y%m%d')}.{show.pk:04d}.{f'{serial:03d}'}"
            elif action_ticket == "change_it":
                price = int(seat[-1])
                ticket.price = price
                ticket.payment = ordereventobj.payment
                ticket.orderevent = ordereventobj
                ticket.event = ordereventobj.event
                ticket.user = ordereventobj.user
                serial = int(ticket.number.split('.')[-1])

            if sell_code is not None:
                ticket.sell_mode = sell_code
            ticket.save()
            result, pdf_file = printer_tckts(ticket_number=ticket.number)
            if result:
                ticket.status= 'Printed'
                ticket.pdf_path = pdf_file.split('/')[-1]
                ticket.save()
            tickets_list.append(ticket)
    context = {
        'ticket_user': ordereventobj.user,
        'tickets_list':tickets_list,
    }

        


    return render(request, 'tickets/tickets_listing.html', context)

def printer_tckts(ticket_number):

    ingressi = ['Gratuito', 'Ridotto', 'Intero']

    status = None
    try:
        ticket = Ticket.objects.get(number=ticket_number)

    except Ticket.MultipleObjectsReturned:
        ticket = Ticket.objects.filter(number=ticket_number).first()

    except Ticket.DoesNotExist:
        print(f'The Ticket with number {ticket_number} does not exist')

    try:    
        event_id = ticket.orderevent.event.pk
        event = Event.objects.get(id=event_id)
        prices = [0.0, event.price_reduced, event.price_full]

        show = Show.objects.get(id=event.show.pk)

        ticket_print = TicketPrinter(
            save_path = 'media/tickets',
            numero=ticket.number,
            show= show.shw_title,
            evento_datetime=event.date_time, 
            evento = event,
            seat= ticket.seat, 
            ingresso= ingressi[ticket.price],
            price= prices[ticket.price]
        )
        filename = ticket_print.build_background()
        ticket_print.write_text()
        img = ticket_print.make_qrcode(user=ticket.user, event=event.pk)
        ticket_print.draw_qrcode(img_path=img)
        ticket.status = 'Printed'
        ticket.save()
        status = True

    except Ticket.MultipleObjectsReturned:
        tickets_many = Ticket.objects.filter(number=ticket_number)

    return status , filename

@login_required(login_url= 'login')
def tickets_listing(request):
    if request.method == 'POST':
        form = TicketListForm(request.POST)
        if form.is_valid():
            tickets_list = form.cleaned_data['tickets_list']
            print(tickets_list)
    tickets_list = []
    context = {
        'tickets_list': tickets_list
    }
    return render(request, 'tickets/tickets_listing.html', context)
