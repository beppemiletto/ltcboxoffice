from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.templatetags.static import static
from django.contrib.auth.decorators import login_required

from .models import Ticket
from .forms import TicketListForm
from billboard.models import Show
from store.models import Event
from orders.models import OrderEvent


from .reportlab_ticket_printer import TicketPrinter
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

        event_tickets = Ticket.objects.filter(orderevent__event=event)
        



        for k, seat in seats_dict.items():
            try:
                tickets_all = Ticket.objects.filter(orderevent__event=event)
                ticket = get_object_or_404(tickets_all, seat= k)
            except:
                print('va stampato')

                price = int(seat[-1])
                ticket = Ticket()
                ticket.price = price
                ticket.payment = ordereventobj.payment
                ticket.orderevent = ordereventobj
                ticket.event = ordereventobj.event
                ticket.seat = k
                ticket.user = ordereventobj.user

                # definisce il numero seriale del biglietto su base serata
                try:
                    event_tickets = Ticket.objects.filter(orderevent__event=event)
                    serial = event_tickets.count()+1
                except:
                    serial=1
                if sell_code is not None:
                    ticket.sell_mode = sell_code
                ticket.number=f"{ticket.sell_mode[0]}{event.date_time.strftime('%Y%m%d')}.{show.pk:04d}.{f'{serial:03d}'}"
                ticket.save()
                result, pdf_file = printer(ticket_number=ticket.number)
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

def printer(ticket_number):

    ingressi = ['Gratuito', 'Intero', 'Ridotto']
    timezones=pytz.all_timezones
    cambiano = pytz.timezone('Europe/Rome')

    status = None
    try:
        ticket = Ticket.objects.get(number=ticket_number)
        event_id = ticket.orderevent.event.pk
        event = Event.objects.get(id=event_id)
        prices = []
        for idx in range(3):
            if idx == 0:
                prices.append(0.0)
            elif idx==1:
                prices.append(event.price_full)
            else:
                prices.append(event.price_reduced)

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
        status = True

    except:
        print('Something wrong happen')
        status = False

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

