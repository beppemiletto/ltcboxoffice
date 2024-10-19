from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages, auth
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import EmptyResultSet, ObjectDoesNotExist, MultipleObjectsReturned
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.mail import EmailMultiAlternatives
from django.utils.formats import localize
from email.mime.image import MIMEImage
from accounts.models import Account
from .models import SellingSeats , PaymentMethod, BoxOfficeTransaction, CustomerProfile, BoxOfficeBookingEvent
from .forms import Barcode_Reader, OrderEventForm, CustomerProfileForm, CustomerShortForm
from .escpos_printer import EscPosPrinter, EscPosDummy, EscPosNetwork
from escpos.printer import Usb, USBNotFoundError, Dummy
from store.models import Event
from orders.models import OrderEvent, UserEvent, Order, Payment
from tickets.models import Ticket
from fiscalmgm.models import Ingresso
from tickets.reportlab_ticket_printer import TicketPrinter
from hall.models import Row
from billboard.models import Show
import time
from datetime import datetime, timedelta
import pytz
import json , os
from pdf2image import convert_from_path
from PIL import Image, ImageFilter
from collections import OrderedDict
import re

# Create your views here.
@login_required(login_url='login')
def boxoffice(request):
    if request.user.is_staff:
        now = datetime.now(pytz.timezone('Europe/Rome'))
        events = Event.objects.filter(show__is_in_billboard=True)
        time_diff = timedelta(
            days= 365
        )

        for event in events:
            td = event.date_time - now
            # print(event.pk, td)
            if td.days >= 0 and td<time_diff:
                time_diff = td
                next_close_event = event
        
        context = {

            'next_close_event' : next_close_event,
        }
                



        messages.success(request,"Sei entrato con utente di staff! Sei abilitato ad operare.")
        return render(request, 'boxoffice/boxoffice.html', context)
    else:
        return redirect ('user_not_allowed')
    
def user_not_allowed(request):
    messages.error(request,"Sei entrato con utente non di staff. Non puoi operare in Cassa.")
    return render(request, 'accounts/login.html')

def event(request, event_id):
    # print(event_id)
    current_event = Event.objects.get(id=event_id)
    event_orders = OrderEvent.objects.filter(event__id=current_event.pk)
    users_event = UserEvent.objects.filter(event__id=current_event.pk).order_by('user__last_name')
    event_bookings = BoxOfficeBookingEvent.objects.filter(event__id=current_event.pk).order_by('customer__last_name')

    # verifica esistenza dell'OrderEvent di apertura della cassa con utente 'cassa' , 'laboratorio', username 'amministrazione@teatrocambiano.com'
    # se manca il record specifico lo crea
    boxoffice_orderevent = None
    if event_orders.count() > 0:
        for item in event_orders:
            if item.user.first_name == "Cassa" and item.user.last_name == "Laboratorio":
                boxoffice_orderevent = item
                break
    
    if boxoffice_orderevent == None:
        boxoffice_user = Account.objects.get(username='ltcboxoffice')
        boxoffice_orderevent = OrderEvent()
        boxoffice_orderevent.user = boxoffice_user
        boxoffice_orderevent.event = current_event
        boxoffice_orderevent.orderevent_number= f'{current_event.pk:05}_000000_000000'
        boxoffice_orderevent.save()

    json_file_path= os.path.abspath(current_event.get_json_path())
    with open(json_file_path,'r') as jfp:
        hall_status = json.load(jfp)
    
    if request.method == 'POST':
        go = False
        selected_seats=[]
        selected_seats_str = request.POST['selected_seats']
        cart_items = []
        costs = current_event.prices()
        ingressi  = ['Gratuito','Ridotto' , 'Intero']
        total = 0.0
        try:
            sellingseats = SellingSeats.objects.all()
            for sellingseat in sellingseats:
                cart_items.append(sellingseat)
                go = True
        except:
            pass
        if len(selected_seats_str):
            selected_seats = selected_seats_str.strip().split(',')
            try:
                for seat in selected_seats:
                    hall_status[seat]['status'] = 4
                    sellingseat = SellingSeats()
                    sellingseat.seat = seat
                    sellingseat.event = current_event
                    if current_event.price_full > 0:
                        sellingseat.price = 2
                    else:
                        sellingseat.price = 0
                    sellingseat.cost=costs[sellingseat.price]
                    sellingseat.ingresso=ingressi[sellingseat.price]
                    total += sellingseat.cost
                    sellingseat.save()
                    cart_items.append(sellingseat)
                    go=True

                with open(json_file_path,'w') as jfp:
                    json.dump(hall_status,jfp, indent=2)

            except:
                print('Something wrong!')

        context = {
            'hall_status': hall_status,
            'event' : current_event,
            'cart_items' : cart_items,
            'total': total,
        }
        if go:
            return redirect(reverse('boxoffice_cart', kwargs={"event_id": current_event.pk}))
        else:
            return redirect(reverse('event', kwargs={"event_id": current_event.pk}))
        
            
    rows={}
    row ={}
    row_label = ''
    for k, seat in hall_status.items():
        if  row_label != seat['row']:
            if row_label != '':
                rows[row_label]=row
            row = {}
            row_label = seat['row']
            r_data = Row.objects.get(name = row_label)
            row['data']= {'name': r_data.name, 'off_start': r_data.offset_start, 'off_end': r_data.offset_end, 'is_act':r_data.is_active}
        row[seat['num_in_row']]= {'status':seat['status'], 'order':seat['order'], 'name':seat['name']}
    rows[row_label]=row  # last row closure


    # print(f"Found {event_orders.count()} ordini aggregati su {users_event.count()} utenti che hanno prenotato")

    orders =  OrderedDict()

    if users_event.count() > 0:

        for user_event in users_event:
            orders[user_event.user.email]={
                'id':user_event.pk, 
                'last_name':user_event.user.last_name, 
                'first_name':user_event.user.first_name,
                'orders':{} 
                }
            
            # The user_event can be emptied by users changes. The control variable 
            # empty_user_event is set to True - If no valid (NOT EXPIRED) ORDER EVENT
            # are found, the user event will be removed from the Dictionary
            empty_user_event = True
            for order_event in user_event.ordersevents.split(','):
                seats = []
                try:
                    orderevent = OrderEvent.objects.get(id=order_event)
                except OrderEvent.DoesNotExist:
                    order_events_NEW = ''
                    order_events_OLD = user_event.ordersevents
                    for orderevent_id in order_events_OLD.split(','):
                        if orderevent_id == order_event:
                            continue
                        else:
                            if len(order_events_NEW):
                                order_events_NEW += f',{orderevent_id}'
                            else:
                                order_events_NEW += f'{orderevent_id}'
                    continue

                if orderevent.expired:
                    continue
                else:
                    empty_user_event = False
                    for seat_price in orderevent.seats_price.split(','):
                        seat = f"{seat_price.split('$')[0]},"
                        seats.append(seat)
                    
                    del seat_price, seat

                    orders[user_event.user.email]['orders'][orderevent.pk] = seats
            del order_event, seats

            # The user event remained empty since the ordeevents have been expired or removed
            # so the item in the dictionary is removed
            if empty_user_event:
                del orders[user_event.user.email]
                



        del user_event, event_orders, event_id, jfp, boxoffice_orderevent, r_data, k

    boxofficebookingevent = BoxOfficeBookingEvent.objects.filter(event=current_event).filter(expired=False).order_by('customer__last_name')

    printer_status: bool = printer_ready()

    context = {
        'hall_status': hall_status,
        'rows': rows,
        'json_file' : json_file_path,
        'current_event' : current_event,
        'orders' : orders,
        'printer_ready': printer_status,
        'boxofficebookings': boxofficebookingevent,
    }

    # return HttpResponse(f"Apriamo allegramente la pagina di gestione della cassa per evento numero {event_id}.")
    return render(request, 'boxoffice/boxoffice_main.html',context)

def boxoffice_cart(request, event_id):
    cart_items = []
    current_event = Event.objects.get(id = event_id)
    sellingseats = SellingSeats.objects.all()
    total = 0.0
    for sellingseat in sellingseats:
        cart_items.append(sellingseat)
        total += sellingseat.cost
    tax = current_event.vat_rate
    taxable =int( (total / (100 + tax) )* 10000) / 100
    payment_methods = PaymentMethod.objects.all()
    context = {
        'event' : current_event,
        'cart_items' : cart_items,
        'total' : total,
        'taxable': taxable,
        'tax': tax,
        'payments_methods': payment_methods,
    }
    return render(request,'boxoffice/boxoffice_cart.html', context)

def boxoffice_cart_cancel(request, event_id):
    event = Event.objects.get(id = event_id)
    sellingseats = SellingSeats.objects.all()
    json_file_path= os.path.abspath(event.get_json_path())
    with open(json_file_path,'r') as jfp:
        hall_status = json.load(jfp)
    for sellingseat in sellingseats:
        if sellingseat.orderevent is not None:
            try:
                orderevent = OrderEvent.objects.get(orderevent_number=sellingseat.orderevent)
                if orderevent.expired:
                    orderevent.expired = False
                orderevent.save()
            except:
                print("Orderevent with number {} NOT FOUND PM".format(sellingseat.orderevent))
                pass
        seat = sellingseat.seat
        # Verify if status is :
        #   1 - booked
        #   3 - preassigned
        #   4 - under transition 
        if hall_status[seat]['status'] in [3,4]:
            hall_status[seat]['status'] = 0 
        sellingseat.delete()
    with open(json_file_path,'w') as jfp:
        json.dump(hall_status,jfp, indent=2)

    del sellingseats
    return redirect(reverse('event', kwargs={"event_id": event.pk}))

def boxoffice_remove_cart(request, item_id):

    item = get_object_or_404(SellingSeats, id=item_id)
    seat = item.seat
    event = item.event
    if item.orderevent != '':
        try:
            item_orderevent = OrderEvent.objects.get(orderevent_number = item.orderevent)
        except:
            item_orderevent = BoxOfficeBookingEvent.objects.get(booking_number = item.orderevent)

        seats_old = item_orderevent.seats_price.split(',')
        seats_NEW = ''
        for seat_single in seats_old:
            if seat in seat_single :
                continue
            else:
                if len(seats_NEW):
                    seats_NEW += f',{seat_single}'
                else: 
                    seats_NEW += f'{seat_single}'
        if len(seats_NEW):
            item_orderevent.seats_price = seats_NEW
            item_orderevent.save()
        else:
            item.orderevent.delete()
    item.delete()
    # del item
    json_file_path= os.path.abspath(event.get_json_path())
    with open(json_file_path,'r') as jfp:
        hall_status = json.load(jfp)
    try:
        # Verify if status is :
        #   1 - booked
        #   3 - preassigned
        #   4 - under transition 
        if hall_status[seat]['status'] in [1,3,4]:

            hall_status[seat]['status'] = 0 
            with open(json_file_path,'w') as jfp:
                json.dump(hall_status,jfp, indent=2)
    except FileNotFoundError:
        print('Something wrong!')
    return redirect(reverse('boxoffice_cart', kwargs={"event_id": event.pk}))


def boxoffice_plus_price(request, item_id = None):
    item = SellingSeats.objects.get(id=item_id)
    current_event = item.event
    costs = current_event.prices()
    ingressi  = ['Gratuito','Ridotto' , 'Intero']
    price_old = item.price
    if price_old < 2:
        price_new = price_old + 1
    else:
        price_new = 2
    item.price = price_new
    item.cost = costs[price_new]
    item.ingresso = ingressi[price_new]
    item.save()

    return redirect(reverse('boxoffice_cart', kwargs={"event_id": current_event.pk}))


def boxoffice_minus_price(request, item_id = None):
    item = SellingSeats.objects.get(id=item_id)
    current_event = item.event
    costs = current_event.prices()
    ingressi  = ['Gratuito','Ridotto' , 'Intero']
    price_old = item.price
    if price_old > 0:
        price_new = price_old - 1
    else:
        price_new = 0
    item.price = price_new
    item.cost = costs[price_new]
    item.ingresso = ingressi[price_new]
    item.save()

    return redirect(reverse('boxoffice_cart', kwargs={"event_id": current_event.pk}))

def boxoffice_print(request, event_id, method_id=None, orderevent_id=None, mode_id=None):
    printer_dummy = Dummy()
    # printer_net = EscPosNetwork(host='localhost', port= 9100)
    try:
        printer_usb = EscPosPrinter(idVendor=0x0483, idProduct=0x5840,timeout=0,in_ep=0x81, out_ep=0x03)
        recovery: bool = False
        # printer_usb = Usb(idVendor=0x0483, idProduct=0x5840,timeout=0,in_ep=0x81, out_ep=0x03)
    except USBNotFoundError:
        print('Manca la stampnate USB')
        printer_usb = printer_dummy
        recovery = True
        # with open('templates/boxoffice/usbnotfound.html', 'r') as html_fp:
        #     html = html_fp.read()
        # html = render_to_string('boxoffice/usbnotfound.html')
        # return HttpResponse(html)


    boxoffice_user = Account.objects.get(first_name = 'Cassa', last_name = 'Laboratorio')
    current_event = Event.objects.get(id = event_id)
    payment_method = PaymentMethod.objects.get(id = method_id)
    if orderevent_id is not None:
        if mode_id=='1':
            orderevent = OrderEvent.objects.get(id=orderevent_id)
            user = orderevent.user
        elif mode_id=='2':
            orderevent = BoxOfficeBookingEvent.objects.get(id=orderevent_id)
            user = boxoffice_user

    else:
        orderevent = OrderEvent.objects.get(event_id=current_event.pk, user=boxoffice_user )
        user = boxoffice_user

    costs = current_event.prices()
    ingressi = ['Gratuito','Ridotto', 'Intero']

    show= current_event.show
    sold_seats = SellingSeats.objects.all()

    # recalculate the total amount for payment
    amount_paid = 0
    for seat in sold_seats:
        amount_paid += seat.cost


    json_file_path= os.path.abspath(current_event.get_json_path())
    with open(json_file_path,'r') as jfp:
        hall_status = json.load(jfp)

    if orderevent_id is not None and mode_id=='1':
        payment = orderevent.order.payment
    else:
        payment = Payment()
        payment.user = user
        payment.payer_given_name = user.first_name
        payment.payer_surname = user.last_name
        payment.payer_mail = user.email
    payment.payment_method = payment_method.slug
    payment.amount_paid=amount_paid
    payment.status='COMPLETED'
    payment.save()

    header= {
        'date' : localize(current_event.date_time),
        'show' : show.shw_title,
    }

    tickets_list = []
    seats_number = sold_seats.count()
    for idx, sold_seat in enumerate(sold_seats):
        try:
            ticket = Ticket.objects.get(event=current_event, seat = sold_seat.seat)
        except:
            try:
                tickets_all = Ticket.objects.filter(event=current_event)
                serial = tickets_all.count() + 1
            except:
                serial = 1
            ticket = Ticket()
            ticket.seat = sold_seat.seat
            ticket.status = 'New'
            ticket.sell_mode = ticket.SELLING_MODE[ticket.SELLING_MODE.index(('C','Cassa'))][0]
            ticket.number=f"{ticket.sell_mode[0]}{current_event.date_time.strftime('%Y%m%d')}.{show.pk:04d}.{f'{serial:03d}'}"
            ticket.event = current_event
        data = {}
        data['seat'] = sold_seat.seat
        ticket.price = sold_seat.price
        data['ingresso'] = ingressi[sold_seat.price]
        data['costo'] = costs[sold_seat.price]
        ticket.orderevent = orderevent.pk
        ticket.user = user
        ticket.payment = payment
        data['numero']= ticket.number

        ticket.save()

        # # aggiorna il OrderEvent della Cassa per questo Evento
        # #OrderEvent di apertura della cassa con utente 'cassa' , 'laboratorio', username 'amministrazione@teatrocambiano.com'
        # try:
        #     boxoffice_orderevent = OrderEvent.objects.get(event__id=current_event.pk, user__last_name='Laboratorio', user__first_name = "Cassa"  )
        # except ObjectDoesNotExist:
        #     boxoffice_orderevent = None

        # if boxoffice_orderevent is not None:
        #     seats_price_str:str = boxoffice_orderevent.seats_price
        #     if len(seats_price_str) > 3:
        #         seats_price_str += f",{sold_seat.seat}${str(sold_seat.price)}"
        #     else:
        #         seats_price_str = f"{sold_seat.seat}${str(sold_seat.price)}"
        #     boxoffice_orderevent.seats_price = seats_price_str
        #     boxoffice_orderevent.save()


        # ticket_printer = TicketPrinter(
        #     save_path = 'media/tickets',
        #     numero=ticket.number,
        #     show= show.shw_title,
        #     evento_datetime=current_event.date_time, 
        #     evento = current_event,
        #     seat= ticket.seat, 
        #     ingresso= ingressi[ticket.price],
        #     price= costs[ticket.price]
        # )

        # filename = ticket_printer.build_background()
        # ticket_printer.write_text()
        # img = ticket_printer.make_qrcode(user=ticket.user, event=current_event.pk)
        # ticket_printer.draw_qrcode(img_path=img)
        # images = convert_from_path(filename)
        # images[-1].save('the_ticket.png', 'PNG')

        # with Image.open('the_ticket.png') as ticket_image_rgba:
        #     ticket_image_rgba.load()
        # ticket_image_l = ticket_image_rgba.convert('L')
        # w, h = ticket_image_l.size
        # k = 0.53
    
        # final_size = (int(w *k),int( h*k))
        # ticket_image_l_scaled= ticket_image_l.resize(final_size)
        # ticket_image_l_rotated= ticket_image_l.transpose(Image.ROTATE_90)
        # threshold = 127
        # ticket_image_l_rotated = ticket_image_l_rotated.point(lambda x: 255 if x > threshold else 0)
        # ticket_image_l_rotated = ticket_image_l_rotated.filter(ImageFilter.CONTOUR)
        if not recovery:
            if idx == 0:
                printer_usb.print_list_header(header=header)
            printer_usb.print_list_item(data=data)
            if idx == (seats_number -1):
                printer_usb.print_list_footer(data=data)



            # ticket_image_l_scaled.save('the_ticket.png', 'PNG')
            # time.sleep(0.25)

            # printer_usb.print_ticket_image('the_ticket.png')  
        else:
            pass
            # if os.name == 'posix':
            #     cmd_str = f'cp {filename} media/tickets/recovery/.'
            # else:
            #     cmd_str = f'copy {filename} media/tickets/recovery/.'
            
            # os.system(cmd_str)

    
        hall_status[ticket.seat]['status'] = 5
        tickets_list.append(ticket)

        
    context = {
       'event': current_event,
       'tickets_list':tickets_list,
       'payment_method': payment_method,

        }
    
    for tckt in tickets_list:
        request = auto_obliterate(request, tckt.number)


    with open(json_file_path,'w') as jfp:
        json.dump(hall_status,jfp, indent=2)
   

    response = close_transaction(request, context)
    return response
    # return render(request, 'boxoffice/ticket_printed.html', context)

def close_transaction(request, context={}):

    current_event = context['event']
    costs = current_event.prices()
    ingressi = ['Gratuito','Ridotto', 'Intero']
    show= current_event.show
    boxoffice_user = Account.objects.get(first_name = 'Cassa', last_name = 'Laboratorio')

    try:
        payments = BoxOfficeTransaction.objects.filter(event=current_event)
        serial_number:int = payments.count() + 1
    except:
        serial_number:int = 1 
    transaction = BoxOfficeTransaction(
        user = boxoffice_user,
        event = current_event,
        seats_sold = '',
        payment_id = f'{current_event.pk:05d}.{serial_number:03d}',
        payment_method = context['payment_method'],
        amount_paid = "total",
        status = 'Completed'
    )

    sold_seats = SellingSeats.objects.all()
    json_file_path= os.path.abspath(current_event.get_json_path())
    with open(json_file_path,'r') as jfp:
        hall_status = json.load(jfp)

    seats_list:list = []
    totale:float = 0
    for sold_seat in sold_seats:
        ticket = Ticket.objects.get(event=current_event, seat = sold_seat.seat)
        if ticket.status == 'New':
            ticket.status = 'Obliterated'
        totale += costs[ticket.price]
        ticket.save()
        seats_list.append(f'{sold_seat.seat}${ticket.price}')
        sold_seat.delete()
    
    transaction.seats_sold = ','.join(seats_list)
    transaction.amount_paid = "{:5.2f}".format(totale)
    transaction.save()
    
    return  redirect(reverse('event', kwargs={"event_id": current_event.pk}))

@login_required(login_url='login')
def event_list(request):
    if request.user.is_staff:
        now = datetime.now(pytz.timezone('Europe/Rome'))
        events = Event.objects.filter(show__is_in_billboard=True).order_by('date_time')
        eventlist:list = []
        for event in events:
            td = event.date_time - now
            # print(event.pk, td)
            if td.days >= 0:
                eventlist.append(event)
        
        context = {

            'eventlist' : eventlist,
        }
        return render(request, 'boxoffice/event_list.html', context)
    else:
        return redirect ('user_not_allowed')
    

    return

def change_bookings(request, event_id=None):
    current_event = Event.objects.get(id=event_id)
    event_orders = OrderEvent.objects.filter(event__id=current_event.pk)
    users_event = UserEvent.objects.filter(event__id=current_event.pk).order_by('user__username')
    event_bookings = BoxOfficeBookingEvent.objects.filter(event__id=current_event.pk).order_by('customer__last_name')
    # aggiorna il OrderEvent della Cassa per questo Evento
    #OrderEvent di apertura della cassa con utente 'cassa' , 'laboratorio', username 'amministrazione@teatrocambiano.com'
    try:
        boxoffice_orderevent = OrderEvent.objects.get(event__id=current_event.pk, user__last_name='Laboratorio', user__first_name = "Cassa"  )
    except:
        boxoffice_orderevent = None
    json_file_path= os.path.abspath(current_event.get_json_path())
    with open(json_file_path,'r') as jfp:
        hall_status = json.load(jfp)
       
    if request.method == 'POST':
        go = False
        selected_seats=[]
        selected_seats_str = request.POST['selected_seats']
        cart_items = []
        costs = current_event.prices()
        ingressi  = ['Gratuito','Ridotto' , 'Intero']
        total = 0.0
        try:
            sellingseats = SellingSeats.objects.all()
            for sellingseat in sellingseats:
                cart_items.append(sellingseat)
                go = True
        except:
            pass
        if len(selected_seats_str):
            selected_seats = selected_seats_str.strip().split(',')
            try:
                for seat in selected_seats:
                    hall_status[seat]['status'] = 4
                    sellingseat = SellingSeats()
                    sellingseat.seat = seat
                    sellingseat.event = current_event
                    if current_event.price_full > 0:
                        sellingseat.price = 2
                    else:
                        sellingseat.price = 0
                    sellingseat.cost=costs[sellingseat.price]
                    sellingseat.ingresso=ingressi[sellingseat.price]
                    total += sellingseat.cost
                    sellingseat.save()
                    cart_items.append(sellingseat)
                    go=True

                with open(json_file_path,'w') as jfp:
                    json.dump(hall_status,jfp, indent=2)

            except:
                print('Something wrong!')

        context = {
            'hall_status': hall_status,
            'event' : current_event,
            'cart_items' : cart_items,
            'total': total,
        }
        if go:
            return redirect(reverse('boxoffice_cart', kwargs={"event_id": current_event.pk}))
        else:
            return redirect(reverse('event', kwargs={"event_id": current_event.pk}))
        
    else:
        userevent_paginator = Paginator(users_event, 8)
        pageuserevent = request.GET.get('page')
        paged_users_event = userevent_paginator.get_page(pageuserevent)
        orderevents = {}

        for single_user in paged_users_event:
            cognome = single_user.user.last_name.strip()
            email = single_user.user.email
            userevent_id = single_user.pk
            orders_str = single_user.ordersevents
            orders_event = orders_str.split(',')
            orders_dict = {}
            for order_str in orders_event:
                # print(order_str, type(order_str))
                orderevent = OrderEvent.objects.get(id = int(order_str))
                seats_count = orderevent.seats_count()
                
                orders_dict[orderevent.pk] =  (seats_count, orderevent.created_at, orderevent.expired, orderevent.updated_at)
            

            orderevents[f'{cognome}-{email}'] = (userevent_id , orders_dict)      

        customerbooking_paginator = Paginator(event_bookings, 8)
        pagebooking = request.GET.get('pagebooking')
        paged_bookings = customerbooking_paginator.get_page(pagebooking)
        bookings = {}

        for single_booking in paged_bookings:
            booking_number = single_booking.booking_number
            cognome = single_booking.customer.last_name.strip()
            nome = single_booking.customer.first_name.strip()
            created_at = single_booking.created_at
            expired = single_booking.expired
            updated_at = single_booking.updated_at
            seats_count = single_booking.seats_count()

            bookings[f'{cognome}-{nome} #{booking_number[-6:]}'] = (seats_count, created_at, expired, updated_at, single_booking.pk)      



        context = {
            'hall_status': hall_status,
            'json_file' : json_file_path,
            'current_event' : current_event,
            'event_orders' : event_orders,
            'bookings' : bookings,
            'orderevents' : orderevents,
            'paged_users_event': paged_users_event,
            'paged_bookings' : paged_bookings,
        }


        return render(request, 'boxoffice/change_bookings.html', context)

def sell_booking(request, order = None, mode=None):
    if mode == '1':
        order_event =  OrderEvent.objects.get(id=order)
        order_number = order_event.orderevent_number
    elif mode=='2':
        order_event =  BoxOfficeBookingEvent.objects.get(id=order)
        order_number = order_event.booking_number

    ingressi= ['Gratuito', 'Ridotto', 'Intero']
    costs = order_event.event.prices()
    booked_seats_price = order_event.seats_price
    for seat_price in booked_seats_price.split(','):
        ordered_seat, ordered_price  = seat_price.split('$')
        ordered_sellingseat = SellingSeats(
            event = order_event.event,
            orderevent = order_number,
            seat = ordered_seat,
            price = int(ordered_price),
            cost = costs[int(ordered_price)],
            ingresso = costs[int(ordered_price)]
        )
        ordered_sellingseat.save()
    sellingseats = SellingSeats.objects.all()

    cart_items = []
    current_event = order_event.event
    total = 0.0
    for sellingseat in sellingseats:
        cart_items.append(sellingseat)
        total += sellingseat.cost
    tax = current_event.vat_rate
    taxable =int( (total / (100 + tax) )* 10000) / 100

    # OrderEvent is set as expired
    order_event.expired = True
    order_event.save()
    payment_methods = PaymentMethod.objects.all()
    context = {
        'event' : current_event,
        'cart_items' : cart_items,
        'total' : total,
        'taxable': taxable,
        'tax': tax,
        'payments_methods': payment_methods,
        'orderevent': order_event,
        'mode': mode,
    }
    return render(request,'boxoffice/boxoffice_cart.html', context)

@login_required(login_url='login')
def edit_order(request, orderevent_id):
    orderevent_edit = OrderEvent.objects.get(id=orderevent_id)
    order = orderevent_edit.order
    payment = orderevent_edit.payment
    user = orderevent_edit.user
    event = orderevent_edit.event
    seats_price = orderevent_edit.seats_price
    updated_at = orderevent_edit.updated_at
    barcode_path = orderevent_edit.barcode_path
    orderevent_number = orderevent_edit.orderevent_number
    expired = orderevent_edit.expired

    cart_items = orderevent_edit.seats_dicts()
    prices = event.prices()
    taxable:float = 0.0
    tax:float = event.vat_rate
    total:float = 0.0
    for key, item in cart_items.items():
        item['ingresso_str'] = prices[int(item['ingresso'])]
        total += float(item['ingresso_str']) 
    taxable=total/(1+tax/100)
    

    context = {
        'total': total,
        'taxable': taxable,
        'tax': tax,
        'cart_items' : cart_items,
        'event' : event,
        'user' : user,
        'number' : orderevent_number,
    }



    return render(request, 'boxoffice/orderevent_edit.html', context)

def erase_order(request, userorder_id, order_id):
    userevent = UserEvent.objects.get(id = userorder_id)
    orderevent = OrderEvent.objects.get(id = order_id)
    current_event = Event.objects.get(id = orderevent.event.id)
    json_file_path= os.path.abspath(current_event.get_json_path())
    orders_str = userevent.ordersevents
    seats_order_event_str = orderevent.seats_price
    orders_event = orders_str.split(',')
    seats_order_event = seats_order_event_str.split(',')
    seats_changed = []

    # Order Check - One to One or One to Many?
    main_order_id = orderevent.order.pk
    order = Order.objects.get(id=main_order_id)
    orderevents_count = OrderEvent.objects.filter(order_id= main_order_id).count()

    for seat in seats_order_event:
        seats_changed.append(seat)

    orders_event.remove(str(order_id))
    if len(orders_event) > 0:
        orders_str = ','.join(orders_event)
        userevent.ordersevents = orders_str
        userevent.save()
    else:
        orders_str = ''
        userevent.delete()

    with open(json_file_path,'r') as jfp:
        hall_status = json.load(jfp)

    for seat in seats_changed:
        key = seat.split('$')[0]
        hall_status[key]['status'] = 0


        tickets_all = Ticket.objects.filter(event = current_event)
        tickets = tickets_all.filter( seat = key)
        how_many = tickets.count()
        if how_many == 0:
                action_ticket = "none"
        elif how_many == 1:
            ticket = tickets[0]
            action_ticket = "change_it"
        elif how_many > 1:
            count = 0
            for single_ticket in tickets:
                if count == 0:
                    ticket = single_ticket
                else:
                    single_ticket.delete()
                count += 1
            action_ticket = "change_it"
        if action_ticket == "change_it":
            ticket.status = 'Cancelled'
            ticket.save()

    with open(json_file_path,'w') as jfp:
        json.dump(hall_status,jfp, indent=2)

    orderevent.delete()

    # Delete also the order if was the only orderevent in that order o update the economics
    # if removed only one o many ordervents
    if orderevents_count < 2:
        order.delete()
    else:
        updateorder(main_order_id)

    return redirect(event_list)

def printer_ready():
    try:
        printer_usb = EscPosPrinter(idVendor=0x0483, idProduct=0x5840,timeout=0,in_ep=0x81, out_ep=0x03)
        printer_ready: bool = True
        del printer_usb
    except USBNotFoundError:
        print('Manca la stampnate USB')
        printer_ready: bool = False

    return printer_ready


def obliterate(request, ticket_number):
    try:
        ticket = Ticket.objects.get(number = ticket_number)
        print(ticket.status)
    except ObjectDoesNotExist:
        context = {
            'ticket_number' : ticket_number,
        }
        return HttpResponse('Ticket {} NOT FOUND / mispelled or not exist'.format(ticket_number))
    event = ticket.event

    #for test
    event_date_time = event.date_time + timedelta(hours=2)
    now = event_date_time + timedelta(hours= -1)    

    # now = datetime.now(pytz.timezone('Europe/Rome'))
    time_diff = timedelta(hours = 6)

    td = event.date_time - now
    
    ticket_valid: bool = (abs(td) <= time_diff)

    print(f'Ticket valid = {ticket_valid}')

    ingresso = None

    if ticket.status == "Printed" or ticket.status == "New" :
        ticket.status= 'Obliterated'
        ticket.save()
        prices = ticket.event.prices()
        sell_mode_code = ticket_number[0]
        sell_modes = { 'W':'Web','C':'Cassa','P': 'Prenotazione' }
        ingresso = Ingresso(
                ticket_number = ticket.number,
                seat = ticket.seat,
                event = ticket.event,
                price = prices[ticket.price],
                sell_mode = sell_modes[sell_mode_code],
        )
        ingresso.save()
        result = True
    elif ticket.status == "Obliterated":
        result = False
        messages.error(request,"Il biglietto numero {} è già stato obliterato!".format(ticket_number))
    elif ticket.status == "Cancelled":
        result = False
        messages.warning(request,"Il biglietto numero {} è stato cancellato! Contatta la cassa per verificare!".format(ticket_number))

    context = {
    'ticket_number' : ticket_number,
    'result': result,
    'ticket' : ticket,
    'ingresso' : ingresso,
    }
 
    return render(request, 'boxoffice/obliterate_result.html', context)

def auto_obliterate( request, ticket_number):
    try:
        ticket = Ticket.objects.get(number = ticket_number)
        # print(ticket.status)
    except ObjectDoesNotExist:
        context = {
            'ticket_number' : ticket_number,
        }
        return HttpResponse('Ticket {} NOT FOUND / mispelled or not exist'.format(ticket_number))
    event = ticket.event

    #for test
    event_date_time = event.date_time + timedelta(hours=2)
    now = event_date_time + timedelta(hours= -1)    

    # now = datetime.now(pytz.timezone('Europe/Rome'))
    time_diff = timedelta(hours = 6)

    td = event.date_time - now
    
    ticket_valid: bool = (abs(td) <= time_diff)

    # print(f'Ticket valid = {ticket_valid}')

    ingresso = None

    if ticket.status == "Printed" or ticket.status == "New" :
        ticket.status= 'Obliterated'
        ticket.save()
        prices = ticket.event.prices()
        sell_mode_code = ticket_number[0]
        sell_modes = { 'W':'Web','C':'Cassa','P': 'Prenotazione' }
        ingresso = Ingresso(
                ticket_number = ticket.number,
                seat = ticket.seat,
                event = ticket.event,
                price = prices[ticket.price],
                sell_mode = sell_modes[sell_mode_code],
        )
        ingresso.save()
        result = True
    elif ticket.status == "Obliterated":
        result = False
        messages.error(request,"Il biglietto numero {} è già stato obliterato!".format(ticket_number))
    elif ticket.status == "Cancelled":
        result = False
        messages.warning(request,"Il biglietto numero {} è stato cancellato! Contatta la cassa per verificare!".format(ticket_number))
 
    return request

def barcode_read(request, event_id:int=None):
    orderevents = OrderEvent.objects.filter(event_id=event_id)
    form = Barcode_Reader(initial={'barcode_code': ''})
    if request.method == 'POST':
        form = Barcode_Reader(request.POST)
        if form.is_valid():
            barcode_code = form.cleaned_data['barcode_code']
            try:
                orderevent = OrderEvent.objects.get(orderevent_number=barcode_code)
                if orderevent in orderevents:
                    orderevent_form = OrderEventForm(data={'barcode_code':orderevent.orderevent_number,
                                                           'user': orderevent.user,
                                                           'event': orderevent.event,
                                                           'seats_price': orderevent.seats_price,
                                                           'created_at':orderevent.created_at,
                                                           'updated_at': orderevent.updated_at,
                                                           'expired': orderevent.expired})
                    valid_order:bool = not orderevent.expired

                    context = {
                        'valid': valid_order,
                        'form': orderevent_form,
                        'event' : event_id,
                        'orderevent' : orderevent,
                    }
                    messages.success(request,f"Il codice {barcode_code} letto o digitato è valido! Procedura di lettura del codice corretta.")
                    return render(request, 'boxoffice/orderevent_details.html',context)
                else:
                    print('NOT FOUND, coglione, altro spettacolo? Fake, mispelled?')

            except Exception as e:
                print(e)
                messages.warning(request,f"Il codice {barcode_code} letto o digitato non è valido! \n Procedura di lettura del codice per ordine fallita e abortita.")
                return redirect(reverse('event', kwargs={"event_id": event_id}))

    context = {
        'form':form,
        'event' : event_id,
        'orderevents' : orderevents,
    }
    return render(request, 'boxoffice/barcode_read.html',context)

def remove_seat(request, number = None, seat= None):
    item = get_object_or_404(OrderEvent, orderevent_number=number)
    removed_seat = seat
    event = item.event
    order = item.order
    user = item.user
    # item.delete()
    # UPDATE the JSON Hall file status
    json_file_path= os.path.abspath(event.get_json_path())
    with open(json_file_path,'r') as jfp:
        hall_status = json.load(jfp)
    try:
        if hall_status[removed_seat]['status'] == 1:
            hall_status[seat]['status'] = 0 
            # hall_status[seat]['status'] = 1 # for testing purposes 
            hall_status[seat]['order'] = '' 
            with open(json_file_path,'w') as jfp:
                json.dump(hall_status,jfp, indent=2)
    except:
        print('Something wrong!')
    
    # UPDATE Orderevent

    seats_price_old = item.seats_price
    seat_patterns = {
        'begin' : re.compile(f"^{removed_seat}\$[0-2],"),
        'center' : re.compile(f"^.+,{removed_seat}\$[0-2],"),
        'only' : re.compile(f"^{removed_seat}\$[0-2]$"),
        'end' : re.compile(f"^.+,{removed_seat}\$[0-2]$")
    }
    subs_type = None

    for key , pattern in seat_patterns.items():
        if bool(re.match(pattern, seats_price_old)):
            subs_type = key

    deleted_orderevent = None
    if subs_type == 'begin':
        seats_price_new = re.sub(seat_patterns['begin'],'',seats_price_old)
        item.seats_price = seats_price_new
        item.save()
    elif subs_type == 'center' or subs_type=='end':
        pattern = re.compile(f',{removed_seat}\$[0-2]')
        seats_price_new = re.sub(pattern,'',seats_price_old)
        item.seats_price = seats_price_new
        item.save()
    elif subs_type == 'only':
        deleted_orderevent = item.pk
        item.delete()
        
    #UPDATE Order if needed
    if subs_type == 'only':
        # the ordevent based on the identified order is the only one.
        # no other reason for identified order to remain active 
        items_number = OrderEvent.objects.filter(order_id=order.pk).count()
        if items_number < 2:
            order_killed = Order.objects.get(id=order.pk)
            order_killed.delete()
        else:
            total, tax = updateorder(order.pk)

    else:
        total, tax = updateorder(order.pk)

    #UPDATE UserOrder if needed
    userevent = UserEvent.objects.filter(event_id = event.pk).get(user_id=user.id)

    if deleted_orderevent is not None:
        orderevents_old = userevent.ordersevents
        orderevent_patterns = {
            'begin' : re.compile(f"^{deleted_orderevent},"),
            'center' : re.compile(f"^.+,{deleted_orderevent},"),
            'only' : re.compile(f"^{deleted_orderevent}$"),
            'end' : re.compile(f"^.+,{deleted_orderevent}$")
            }
        for key , pattern in orderevent_patterns.items():
            if bool(re.match(pattern, orderevents_old)):
                orderevent_subs_type = key
        if orderevent_subs_type == 'begin':
            orderevents_new = re.sub(orderevent_patterns['begin'],'',orderevents_old)
            userevent.ordersevents = orderevents_new
            userevent.save()
        elif orderevent_subs_type == 'center' or orderevent_subs_type=='end':
            pattern = re.compile(f',{deleted_orderevent}\$[0-2]')
            orderevents_new = re.sub(pattern,'',orderevents_old)
            userevent.ordersevents = orderevents_new
            userevent.save()
        elif orderevent_subs_type == 'only':
            userevent.delete()
                        

    try:
        item = OrderEvent.objects.get(orderevent_number=number)
        item_exists = True
    except ObjectDoesNotExist:
        item_exists = False


    if item_exists:

        return redirect(reverse('edit_order', kwargs={"orderevent_id": item.pk}))
    else:   
        return redirect(reverse('change_bookings', kwargs={"event_id": event.pk}))


def plus_ingresso(request, number = None, seat= None):
    item = get_object_or_404(OrderEvent, orderevent_number=number)
    event = item.event
    user = item.user

    seats_price = item.seats_price


    find_pattern = re.compile(f'{seat}\$[0-2]')
    seat_price_old = find_pattern.findall(seats_price)[0]
    place, price = seat_price_old.split('$')
    if int(price)<2:
        price_int = int(price)
        price_int += 1
        seat_price_new = f'{seat}${price_int}'
        change = True
    else:
        change= False
                
    if change:
        seats_price_new = re.sub(find_pattern,seat_price_new,seats_price)
        item.seats_price = seats_price_new
        item.save()
        #  Update also related Order Total
        main_order_id = item.order.pk
        total , tax = updateorder(main_order_id)

    return redirect(reverse('edit_order', kwargs={"orderevent_id": item.pk}))


def minus_ingresso(request, number = None, seat= None):
    item = get_object_or_404(OrderEvent, orderevent_number=number)
    event = item.event
    user = item.user

    seats_price = item.seats_price


    find_pattern = re.compile(f'{seat}\$[0-2]')
    seat_price_old = find_pattern.findall(seats_price)[0]
    place, price = seat_price_old.split('$')
    if int(price)>0:
        price_int = int(price)
        price_int -= 1
        seat_price_new = f'{seat}${price_int}'
        change = True
    else:
        change= False
                
    if change:
        seats_price_new = re.sub(find_pattern,seat_price_new,seats_price)
        item.seats_price = seats_price_new
        item.save()
        #  Update also related Order Total
        main_order_id = item.order.pk
        total , tax = updateorder(main_order_id)

    return redirect(reverse('edit_order', kwargs={"orderevent_id": item.pk}))

def hall_detail(request, event_slug=None, number=None):
    event = get_object_or_404(Event, event_slug=event_slug)
    orderevent = OrderEvent.objects.get(orderevent_number=number)
    user = orderevent.user
    userevent = UserEvent.objects.filter(event_id = event.pk).get(user_id=user.id)
    former_seats = orderevent.seats_list_name()
    json_file_path= os.path.abspath(event.get_json_path())
    with open(json_file_path,'r') as jfp:
        hall_status = json.load(jfp)
    if request.method == 'POST':
        selected_seats = request.POST['selected_seats'].split(',')
        orderevent_seats_price = orderevent.seats_price
        userevent_seats_price = orderevent.seats_price

        try:
            added_seats = ''
            for seat in selected_seats:
                hall_status[seat]['status'] = 1
                hall_status[seat]['order'] = number
                added_seats +=f',{seat}$2' 
            with open(json_file_path,'w') as jfp:
                json.dump(hall_status,jfp, indent=2)
        except:
            print('Something wrong!')

        orderevent_seats_price +=added_seats
        orderevent.seats_price = orderevent_seats_price
        orderevent.save()
        #  Update also related Order Total
        main_order_id = orderevent.order.pk
        total , tax = updateorder(main_order_id)

        return redirect(reverse('edit_order', kwargs={"orderevent_id": orderevent.pk}))
    else:
        # preparing rows
        row_hall = Row.objects.all()
        rows={}
        row ={}
        row_label = ''
        for k, seat in hall_status.items():
            if  row_label != seat['row']:
                if row_label != '':
                    rows[row_label]=row
                row = {}
                row_label = seat['row']
                r_data = Row.objects.get(name = row_label)
                row['data']= {'name': r_data.name, 'off_start': r_data.offset_start, 'off_end': r_data.offset_end, 'is_act':r_data.is_active}
            row[seat['num_in_row']]= {'status':seat['status'], 'order':seat['order'], 'name':seat['name']}
        rows[row_label]=row  # last row closure



        context = {
            'number': number,
            'hall_status': hall_status,
            'rows': rows,
            'json_file' : json_file_path,
            'event': event,
            'formerseats' : former_seats,
            'orderevent' : orderevent,
        }

        return render(request, 'boxoffice/hall_detail.html', context)
    
def send_updatemail(request, number):
    # Send order update email to customer
   # prepare a dictionary for email data
    email_data = {}
    orderevent = OrderEvent.objects.get(orderevent_number=number)
    event= orderevent.event

    prices = event.prices()
    booked_seats = {}

    for item in orderevent.seats_price.split(','):
        seat, price = item.split('$')

        booked_seats[seat] = prices[int(price)]

    email_data[orderevent.orderevent_number] = {
    'show':orderevent.event.show.shw_title,
    'datetime': orderevent.event.date_time,
    'seats': booked_seats,
    'barcode': orderevent.barcode_path.split('/')[-1],
    'barcode_path': orderevent.barcode_path 
    }



    # Count the order events included in the single order
    orderevents_count = len(email_data)

    # Send order received email to customer 

    current_site = get_current_site(request)

    mail_subject = f'LTC BoxOffice. La tua prenotazione {number} è stata aggiornata!'
    email_context = {
        'count': orderevents_count,
        'user': orderevent.user,
        'userevent': orderevent.user,
        'order': orderevent.order,
        'email_data' : email_data,
    }
    message = render_to_string('boxoffice/order_changed_email.html', email_context).strip()
    to_email = [orderevent.user.email,]
    # send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email = EmailMultiAlternatives(
        mail_subject,
        message,
        to=to_email
    )
    send_email.content_subtype = 'html'
    send_email.mixed_subtype = 'related'
    # send_email.attach(message, "text/html")
    img_dir = 'static/images'
    image = 'logo.png'
    file_path = os.path.join(img_dir, image)
    with open(file_path,'rb') as fip:
        img = MIMEImage(fip.read(),_subtype='png')
        img.add_header('Content-ID', '<{name}>'.format(name=image))
        # img.add_header('Content-Disposition', 'inline', filename=image)
    send_email.attach(img)

    for orderevent_number, orderevent_data in email_data.items():
        file_path:os.path = orderevent_data['barcode_path']
    #this name must be same as in the htmltemplate being only a placeholder
        barcode:str = orderevent_data['barcode']

        with open(file_path,'rb') as fip:
            brc = MIMEImage(fip.read(),_subtype='png')
            brc.add_header('Content-ID', '<{name}>'.format(name=barcode))
            # img.add_header('Content-Disposition', 'inline', filename=image)
        send_email.attach(brc)

    send_email.send()

    current_event=orderevent.event

    return redirect(reverse('change_bookings', kwargs={"event_id": current_event.pk}))

def updateorder(main_order_id=None):
    order= Order.objects.get(id=main_order_id)
    orderevents = OrderEvent.objects.filter(order_id= main_order_id)
    total = 0
    tax = 0

    for orderevent in orderevents:
        prices = orderevent.event.prices()
        seats_price = orderevent.seats_price
        subtotal = 0
        for seat_price in seats_price.split(','):
            seat, price = seat_price.split('$')
            subtotal += prices[int(price)]
        total += subtotal
    tax += total * orderevent.event.vat_rate / 100.0
    order.order_total = total
    order.tax = tax
    order.save()
    return (total, tax) 

def add_bookings(request, event_id=None, customer=None):
    current_event = Event.objects.get(id=event_id)
    if customer is not None:
        # preparing rows
        json_file_path= os.path.abspath(current_event.get_json_path())
        with open(json_file_path,'r') as jfp:
            hall_status = json.load(jfp)
        if request.method == 'POST':
            customer_profile_form = CustomerProfileForm(request.POST)
            if customer_profile_form.is_valid():
                email = customer_profile_form.cleaned_data['email']
                first_name = customer_profile_form.cleaned_data['first_name']
                last_name = customer_profile_form.cleaned_data['last_name']
                try:
                    maybe_customers = CustomerProfile.objects.filter(email=email)
                    if maybe_customers.count():
                        the_customer = maybe_customers.get(email=email)
                        if the_customer.last_name.lower != last_name.lower:
                            the_customer.first_name = first_name
                            the_customer.last_name = last_name
                            if customer_profile_form.cleaned_data['phone_number'] != '':
                                the_customer.phone_number = customer_profile_form.cleaned_data['phone_number']
                            if customer_profile_form.cleaned_data['address'] != '':
                                the_customer.address = customer_profile_form.cleaned_data['address']
                            if customer_profile_form.cleaned_data['city'] != '':
                                the_customer.city = customer_profile_form.cleaned_data['city']
                            if customer_profile_form.cleaned_data['province'] != '':
                                the_customer.province = customer_profile_form.cleaned_data['province']
                            if customer_profile_form.cleaned_data['post_code'] != '':
                                the_customer.post_code = customer_profile_form.cleaned_data['post_code']

                            the_customer.save()
                    else:
                        raise 
                except:
                    the_customer = CustomerProfile()
                    the_customer.first_name = first_name
                    the_customer.last_name = last_name
                    the_customer.email = customer_profile_form.cleaned_data['email']
                    the_customer.phone_number = customer_profile_form.cleaned_data['phone_number']
                    the_customer.address = customer_profile_form.cleaned_data['address']
                    the_customer.city = customer_profile_form.cleaned_data['city']
                    the_customer.province = customer_profile_form.cleaned_data['province']
                    the_customer.post_code = customer_profile_form.cleaned_data['post_code']

                    the_customer.save()
                selected_seats_str = request.POST['selected_seats']
                selected_seats = []
                if len(selected_seats_str) > 1:
                    selected_seats = selected_seats_str.split(',')

                if len(selected_seats):

                    try:
                        added_seats = ''
                        seat_count=0
                        for seat in selected_seats:
                            seat_count += 1
                            hall_status[seat]['status'] = 1
                            hall_status[seat]['order'] = 'boxoffice_pending'
                            if seat_count==1:
                                added_seats +=f'{seat}$2' 
                            else:
                                added_seats +=f',{seat}$2' 
                        with open(json_file_path,'w') as jfp:
                            json.dump(hall_status,jfp, indent=2)
                    except:
                        print('Something wrong!')

                    boxofficebookingevent = BoxOfficeBookingEvent(
                    customer = the_customer,
                    event = current_event,
                    seats_price = added_seats,
                    )
                    boxofficebookingevent.save()
                    boxofficebookingevent.booking_number = f'{current_event.pk:05d}_{the_customer.pk:05d}_{boxofficebookingevent.pk:06d}'
                    boxofficebookingevent.save()

                    return redirect(reverse('edit_booking', kwargs={"boxofficebookingevent_number": boxofficebookingevent.booking_number}))
                else:
                    return HttpResponse("Non ci sono posti selezionati")

        else:
            row_hall = Row.objects.all()
            rows={}
            row ={}
            row_label = ''
            for k, seat in hall_status.items():
                if  row_label != seat['row']:
                    if row_label != '':
                        rows[row_label]=row
                    row = {}
                    row_label = seat['row']
                    r_data = Row.objects.get(name = row_label)
                    row['data']= {'name': r_data.name, 'off_start': r_data.offset_start, 'off_end': r_data.offset_end, 'is_act':r_data.is_active}
                row[seat['num_in_row']]= {'status':seat['status'], 'order':seat['order'], 'name':seat['name']}
            rows[row_label]=row  # last row closure
            customer_obj = CustomerProfile.objects.get(email=customer)

            customer_profile_form = CustomerProfileForm(initial= {
                'first_name' : customer_obj.first_name ,
                'last_name' : customer_obj.last_name,
                'address' : customer_obj.address,
                'city' : customer_obj.city,
                'province' : customer_obj.province,
                'post_code' : customer_obj.post_code,
                'email' :customer_obj.email,
                'phone_number':customer_obj.phone_number,
            })

            context = {
                'customer_profile_form' : customer_profile_form,
                'hall_status': hall_status,
                'rows': rows,
                'json_file' : json_file_path,
                'event': current_event,
                'customer': customer_obj,
            }

            return render(request, 'boxoffice/addbooking_halldetail.html', context)
    else:
        return redirect(reverse('customers', kwargs={"event_id": current_event.pk}))       

@login_required(login_url='login')
def edit_booking(request, boxofficebookingevent_number=None):
    boxofficebookingevent_edit = BoxOfficeBookingEvent.objects.get(booking_number=boxofficebookingevent_number)
    customer = boxofficebookingevent_edit.customer
    event = boxofficebookingevent_edit.event

    cart_items = boxofficebookingevent_edit.seats_dicts()
    prices = event.prices()
    taxable:float = 0.0
    tax:float = event.vat_rate
    total:float = 0.0
    for key, item in cart_items.items():
        item['ingresso_str'] = prices[int(item['ingresso'])]
        total += float(item['ingresso_str']) 
    taxable=total/(1+tax/100)
    
    if request.method=='POST':
        # controlla dati cliente
        form = CustomerShortForm(request.POST)
        if form.is_valid():
            if customer.first_name != form.cleaned_data['first_name']:
                customer.first_name = form.cleaned_data['first_name'] 
            if customer.last_name != form.cleaned_data['last_name']:
                customer.last_name = form.cleaned_data['last_name'] 
            if customer.email != form.cleaned_data['email']:
                customer.email = form.cleaned_data['email'] 
            if customer.phone_number != form.cleaned_data['phone_number']:
                customer.phone_number = form.cleaned_data['phone_number'] 
            customer.save() 

        return redirect(event_list)
    # inserire la verifica. controllo della situazione hall json rispetto alla prenotazione cliente boxoffice registrata 
    else:
        form = CustomerShortForm({
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'email': customer.email,
            'phone_number': customer.phone_number,
                                   })

        context = {
            'form' : form,
            'total': total,
            'taxable': taxable,
            'tax': tax,
            'cart_items' : cart_items,
            'event' : event,
            'customer' : customer,
            'number' : boxofficebookingevent_number,
        }



        return render(request, 'boxoffice/booking_edit.html', context)

def plus_ingr_booking(request, number = None, seat= None):
    item = get_object_or_404(BoxOfficeBookingEvent, booking_number=number)
    seats_price = item.seats_price

    find_pattern = re.compile(f'{seat}\$[0-2]')
    seat_price_old = find_pattern.findall(seats_price)[0]
    place, price = seat_price_old.split('$')
    if int(price)<2:
        price_int = int(price)
        price_int += 1
        seat_price_new = f'{seat}${price_int}'
        change = True
    else:
        change= False
                
    if change:
        seats_price_new = re.sub(find_pattern,seat_price_new,seats_price)
        item.seats_price = seats_price_new
        item.save()


    return redirect(reverse('edit_booking', kwargs={"boxofficebookingevent_number": item.booking_number}))


def minus_ingr_booking(request, number = None, seat= None):
    item = get_object_or_404(BoxOfficeBookingEvent, booking_number=number)
    
    seats_price = item.seats_price


    find_pattern = re.compile(f'{seat}\$[0-2]')
    seat_price_old = find_pattern.findall(seats_price)[0]
    place, price = seat_price_old.split('$')
    if int(price)>0:
        price_int = int(price)
        price_int -= 1
        seat_price_new = f'{seat}${price_int}'
        change = True
    else:
        change= False
                
    if change:
        seats_price_new = re.sub(find_pattern,seat_price_new,seats_price)
        item.seats_price = seats_price_new
        item.save()

    return redirect(reverse('edit_booking', kwargs={"boxofficebookingevent_number": item.booking_number}))


def removeseat_booking(request, number = None, seat= None):
    item = get_object_or_404(BoxOfficeBookingEvent, booking_number=number)
    removed_seat = seat
    event = item.event
    user = item.customer
    # item.delete()
    # UPDATE the JSON Hall file status
    json_file_path= os.path.abspath(event.get_json_path())
    with open(json_file_path,'r') as jfp:
        hall_status = json.load(jfp)
    try:
        if hall_status[removed_seat]['status'] == 1:
            hall_status[seat]['status'] = 0 
            # hall_status[seat]['status'] = 1 # for testing purposes 
            hall_status[seat]['order'] = '' 
            with open(json_file_path,'w') as jfp:
                json.dump(hall_status,jfp, indent=2)
    except:
        print('Something wrong!')
    
    # UPDATE Orderevent

    seats_price_old = item.seats_price
    seat_patterns = {
        'begin' : re.compile(f"^{removed_seat}\$[0-2],"),
        'center' : re.compile(f"^.+,{removed_seat}\$[0-2],"),
        'only' : re.compile(f"^{removed_seat}\$[0-2]$"),
        'end' : re.compile(f"^.+,{removed_seat}\$[0-2]$")
    }
    subs_type = None

    for key , pattern in seat_patterns.items():
        if bool(re.match(pattern, seats_price_old)):
            subs_type = key

    if subs_type == 'begin':
        seats_price_new = re.sub(seat_patterns['begin'],'',seats_price_old)
        item.seats_price = seats_price_new
        item.save()
    elif subs_type == 'center' or subs_type=='end':
        pattern = re.compile(f',{removed_seat}\$[0-2]')
        seats_price_new = re.sub(pattern,'',seats_price_old)
        item.seats_price = seats_price_new
        item.save()
    elif subs_type == 'only':
        item.delete()
        
                        

    try:
        item = BoxOfficeBookingEvent.objects.get(booking_number=number)
        return redirect(reverse('edit_booking', kwargs={"boxofficebookingevent_number": item.booking_number}))
    except ObjectDoesNotExist:
        return redirect(event_list)

def erase_booking(request, customerbooking_id=None):
    booking = BoxOfficeBookingEvent.objects.get(id = customerbooking_id)
    current_event = Event.objects.get(id = booking.event.id)
    json_file_path= os.path.abspath(current_event.get_json_path())
    seats_booking_str = booking.seats_price
    seats_booking = seats_booking_str.split(',')
    seats_changed = []

    for seat in seats_booking:
        seats_changed.append(seat)

    with open(json_file_path,'r') as jfp:
        hall_status = json.load(jfp)

    for seat in seats_changed:
        key = seat.split('$')[0]
        print(hall_status[key]['status'])
        hall_status[key]['status'] = 0
        hall_status[key]['order'] = ''


    with open(json_file_path,'w') as jfp:
        json.dump(hall_status,jfp, indent=2)

    booking.delete()

    return redirect(reverse('change_bookings', kwargs={"event_id": current_event.pk}))

def customers(request, event_id=None, customer=None):
    if customer is not None:
        if request.method == 'POST':
            customer_profile_form = CustomerProfileForm(request.POST)
            if customer_profile_form.is_valid():
                email = customer_profile_form.cleaned_data['email']
                first_name = customer_profile_form.cleaned_data['first_name']
                last_name = customer_profile_form.cleaned_data['last_name']
                try:
                    maybe_customers = CustomerProfile.objects.filter(email=email)
                    if maybe_customers.count():
                        the_customer = maybe_customers.get(email=email)
                        if the_customer.last_name.lower != last_name.lower:
                            the_customer.first_name = first_name
                            the_customer.last_name = last_name
                            if customer_profile_form.cleaned_data['phone_number'] != '':
                                the_customer.phone_number = customer_profile_form.cleaned_data['phone_number']
                            if customer_profile_form.cleaned_data['address'] != '':
                                the_customer.address = customer_profile_form.cleaned_data['address']
                            if customer_profile_form.cleaned_data['city'] != '':
                                the_customer.city = customer_profile_form.cleaned_data['city']
                            if customer_profile_form.cleaned_data['province'] != '':
                                the_customer.province = customer_profile_form.cleaned_data['province']
                            if customer_profile_form.cleaned_data['post_code'] != '':
                                the_customer.post_code = customer_profile_form.cleaned_data['post_code']

                            the_customer.save()
                    else:
                        raise 
                except:
                    the_customer = CustomerProfile()
                    the_customer.first_name = first_name
                    the_customer.last_name = last_name
                    the_customer.email = customer_profile_form.cleaned_data['email']
                    the_customer.phone_number = customer_profile_form.cleaned_data['phone_number']
                    the_customer.address = customer_profile_form.cleaned_data['address']
                    the_customer.city = customer_profile_form.cleaned_data['city']
                    the_customer.province = customer_profile_form.cleaned_data['province']
                    the_customer.post_code = customer_profile_form.cleaned_data['post_code']

                    the_customer.save()
            customer_obj = the_customer

        else:

            customer_obj= CustomerProfile.objects.get(email=customer)
        return redirect(reverse('add_bookings', kwargs={'event_id': event_id, 'customer': customer_obj.email}))
    else:
        current_event = Event.objects.get(id=event_id)
        customers = CustomerProfile.objects.order_by('last_name', 'first_name', 'email')


        customers_paginator = Paginator(customers, 10)
        page = request.GET.get('page')
        paged_customers = customers_paginator.get_page(page)

        customer_profile_form = CustomerProfileForm()

        context =  {
            'new_customer': 'new_customer',
            'customer_profile_form': customer_profile_form,
            'customers': customers,
            'paged_customers': paged_customers,
            'current_event': current_event,
        }

        return render(request,'boxoffice/customers.html',context)    
