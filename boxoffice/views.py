from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages, auth
from django.core.exceptions import EmptyResultSet, ObjectDoesNotExist, MultipleObjectsReturned
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from .models import SellingSeats , PaymentMethod, BoxOfficeTransaction
from .forms import Barcode_Reader, OrderEventForm
from .escpos_printer import EscPosPrinter, EscPosDummy, EscPosNetwork
from escpos.printer import Usb, USBNotFoundError, Dummy
from store.models import Event
from orders.models import OrderEvent, UserEvent, Order
from tickets.models import Ticket
from fiscalmgm.models import Ingresso
from tickets.reportlab_ticket_printer import TicketPrinter
from accounts.models import Account
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
    # verifica esistenza dell'OrderEvent di apertura della cassa con utente 'cassa' , 'laboratorio', username 'amministrazione@teatrocambiano.com'
    # se manca il record specifico lo crea
    boxoffice_orderevent = None
    if event_orders.count() > 0:
        for item in event_orders:
            if item.user.first_name == "Cassa" and item.user.last_name == "Laboratorio":
                boxoffice_orderevent = item

    json_file_path= os.path.abspath(current_event.get_json_path())
    with open(json_file_path,'r') as jfp:
        hall_status = json.load(jfp)
    
    if request.method == 'POST':
        go = False
        selected_seats=[]
        selected_seats_str = request.POST['selected_seats']
        cart_items = []
        costs = [0.0,  current_event.price_reduced, current_event.price_full]
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
                    json.dump(hall_status,jfp)

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


    print(f"Found {event_orders.count()} ordini aggregati su {users_event.count()} utenti che hanno prenotato")

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

    printer_status: bool = printer_ready()

    context = {
        'hall_status': hall_status,
        'rows': rows,
        'json_file' : json_file_path,
        'current_event' : current_event,
        'orders' : orders,
        'printer_ready': printer_status,
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
            orderevent = OrderEvent.objects.get(id=sellingseat.orderevent.pk)
            if orderevent.expired:
                orderevent.expired = False
            orderevent.save()
        seat = sellingseat.seat
        # Verify if status is :
        #   1 - booked
        #   3 - preassigned
        #   4 - under transition 
        if hall_status[seat]['status'] in [3,4]:
            hall_status[seat]['status'] = 0 
        sellingseat.delete()
    with open(json_file_path,'w') as jfp:
        json.dump(hall_status,jfp)

    del sellingseats
    return redirect(reverse('event', kwargs={"event_id": event.pk}))

def boxoffice_remove_cart(request, item_id):

    item = get_object_or_404(SellingSeats, id=item_id)
    seat = item.seat
    event = item.event
    if item.orderevent is not None:
        seats_old = item.orderevent.seats_price.split(',')
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
            item.orderevent.seats_price = seats_NEW
            item.orderevent.save()
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
                json.dump(hall_status,jfp)
    except FileNotFoundError:
        print('Something wrong!')
    return redirect(reverse('boxoffice_cart', kwargs={"event_id": event.pk}))


def boxoffice_plus_price(request, item_id = None):
    item = SellingSeats.objects.get(id=item_id)
    current_event = item.event
    costs = [0.0,  current_event.price_reduced, current_event.price_full]
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
    costs = [0.0,  current_event.price_reduced, current_event.price_full]
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

def boxoffice_print(request, event_id, method_id=None, orderevent_id=None):
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


    current_event = Event.objects.get(id = event_id)
    payment_method = PaymentMethod.objects.get(id = method_id)
    costs = [0, current_event.price_reduced, current_event.price_full]
    ingressi = ['Gratuito','Ridotto', 'Intero']
    show= current_event.show
    sold_seats = SellingSeats.objects.all()
    json_file_path= os.path.abspath(current_event.get_json_path())
    with open(json_file_path,'r') as jfp:
        hall_status = json.load(jfp)

    tickets_list = []
    for sold_seat in sold_seats:
        try:
            tickets_all = Ticket.objects.filter(event=current_event)
            serial = tickets_all.count() + 1
        except:
            serial = 1
        ticket = Ticket()
        data = {}
        ticket.sell_mode = ticket.SELLING_MODE[ticket.SELLING_MODE.index(('C','Cassa'))][0]
        ticket.status = 'New'

        ticket.seat = sold_seat.seat
        data['seat'] = sold_seat.seat

        ticket.price = sold_seat.price
        data['ingresso'] = ingressi[sold_seat.price]
        data['costo'] = costs[sold_seat.price]

        ticket.payment = None
        boxoffice_user = Account.objects.get(first_name = 'Cassa', last_name = 'Laboratorio')
        if orderevent_id is not None:
            ticket.orderevent = OrderEvent.objects.get(id=orderevent_id)
        else:
            ticket.orderevent = OrderEvent.objects.get(event_id=current_event.pk, user=boxoffice_user )
        ticket.event = current_event
        ticket.user = boxoffice_user
        
        ticket.number=f"{ticket.sell_mode[0]}{current_event.date_time.strftime('%Y%m%d')}.{show.pk:04d}.{f'{serial:03d}'}"
        data['numero']= ticket.number

        ticket.save()

        # aggiorna il OrderEvent della Cassa per questo Evento
        #OrderEvent di apertura della cassa con utente 'cassa' , 'laboratorio', username 'amministrazione@teatrocambiano.com'
        try:
            boxoffice_orderevent = OrderEvent.objects.get(event__id=current_event.pk, user__last_name='Laboratorio', user__first_name = "Cassa"  )
        except ObjectDoesNotExist:
            boxoffice_orderevent = None

        if boxoffice_orderevent is not None:
            seats_price_str:str = boxoffice_orderevent.seats_price
            if len(seats_price_str) > 3:
                seats_price_str += f",{sold_seat.seat}${str(sold_seat.price)}"
            else:
                seats_price_str = f"{sold_seat.seat}${str(sold_seat.price)}"
            boxoffice_orderevent.seats_price = seats_price_str
            boxoffice_orderevent.save()


        ticket_printer = TicketPrinter(
            save_path = 'media/tickets',
            numero=ticket.number,
            show= show.shw_title,
            evento_datetime=current_event.date_time, 
            evento = current_event,
            seat= ticket.seat, 
            ingresso= ingressi[ticket.price],
            price= costs[ticket.price]
        )

        filename = ticket_printer.build_background()
        ticket_printer.write_text()
        img = ticket_printer.make_qrcode(user=ticket.user, event=current_event.pk)
        ticket_printer.draw_qrcode(img_path=img)
        images = convert_from_path(filename)
        images[-1].save('the_ticket.png', 'PNG')

        with Image.open('the_ticket.png') as ticket_image_rgba:
            ticket_image_rgba.load()
        ticket_image_l = ticket_image_rgba.convert('L')
        w, h = ticket_image_l.size
        k = 0.53
    
        final_size = (int(w *k),int( h*k))
        ticket_image_l_scaled= ticket_image_l.resize(final_size)
        # ticket_image_l_rotated= ticket_image_l.transpose(Image.ROTATE_90)
        # threshold = 127
        # ticket_image_l_rotated = ticket_image_l_rotated.point(lambda x: 255 if x > threshold else 0)
        # ticket_image_l_rotated = ticket_image_l_rotated.filter(ImageFilter.CONTOUR)
        if not recovery:
            ticket_image_l_scaled.save('the_ticket.png', 'PNG')
            time.sleep(0.25)

            printer_usb.print_ticket_image('the_ticket.png')  
        else:
            if os.name == 'posix':
                cmd_str = f'cp {filename} media/tickets/recovery/.'
            else:
                cmd_str = f'copy {filename} media/tickets/recovery/.'
            
            os.system(cmd_str)

    
        hall_status[ticket.seat]['status'] = 5
        tickets_list.append(ticket)

        
    context = {
       'event': current_event,
       'tickets_list':tickets_list,
       'payment_method': payment_method,

        }
    
    for tckt in tickets_list:
        auto_obliterate(tckt.number)


    with open(json_file_path,'w') as jfp:
        json.dump(hall_status,jfp)
   

    response = close_transaction(request, context)
    return response
    # return render(request, 'boxoffice/ticket_printed.html', context)

def close_transaction(request, context={}):

    current_event = context['event']
    costs = [0, current_event.price_reduced, current_event.price_full]
    ingressi = ['Gratuito','Ridotto', 'Intero']
    show= current_event.show
    boxoffice_user = Account.objects.get(first_name = 'Cassa', last_name = 'Laboratorio')

    try:
        payments = BoxOfficeTransaction.objects.filter(event=current_event)
        serial_number:int = payments.count() + 1
    except:
        serial_number:int = 1 
    payment = BoxOfficeTransaction(
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
        ticket.status = 'Printed'
        totale += costs[ticket.price]
        ticket.save()
        seats_list.append(f'{sold_seat.seat}${ticket.price}')
        sold_seat.delete()
    
    payment.seats_sold = ','.join(seats_list)
    payment.amount_paid = "{:5.2f}".format(totale)
    payment.save()
    
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

def change_bookings(request, event_id):
    current_event = Event.objects.get(id=event_id)
    event_orders = OrderEvent.objects.filter(event__id=current_event.pk)
    users_event = UserEvent.objects.filter(event__id=current_event.pk)
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
        costs = [0.0,  current_event.price_reduced, current_event.price_full]
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
                    json.dump(hall_status,jfp)

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
        paginator = Paginator(users_event, 8)
        page = request.GET.get('page')
        paged_users_event = paginator.get_page(page)
        bookings = {}

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
                orders_dict[orderevent.pk] =  (orderevent.seats_price, orderevent.created_at)
            

            bookings[f'{cognome}-{email}'] = (userevent_id , orders_dict)      

        context = {
            'hall_status': hall_status,
            'json_file' : json_file_path,
            'current_event' : current_event,
            'event_orders' : event_orders,
            'bookings' : bookings,
            'paged_users_event': paged_users_event,
        }


        return render(request, 'boxoffice/change_bookings.html', context)

def sell_booking(request, order = None):

    order_event =  OrderEvent.objects.get(id=order)
    ingressi= ['Gratuito', 'Ridotto', 'Intero']
    costs = [0.0,  order_event.event.price_reduced, order_event.event.price_full]
    booked_seats_price = order_event.seats_price
    for seat_price in booked_seats_price.split(','):
        ordered_seat, ordered_price  = seat_price.split('$')
        ordered_sellingseat = SellingSeats(
            event = order_event.event,
            orderevent = order_event,
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
    prices = [0,event.price_reduced, event.price_full]
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
    seats_user_event_str = userevent.seats_price
    seats_order_event_str = orderevent.seats_price
    orders_event = orders_str.split(',')
    seats_user_event = seats_user_event_str.split(',')
    seats_order_event = seats_order_event_str.split(',')
    seats_changed = []

    for seat in seats_order_event:
        seats_user_event.remove(seat)
        seats_changed.append(seat)
    if len(seats_user_event) > 0:
        seats_user_event_str = ','.join(seats_user_event)
        userevent.seats_price = seats_user_event_str
    else:
        seats_user_event_str = ''

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
        json.dump(hall_status,jfp)

    orderevent.delete()

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
        prices = (0.0, ticket.event.price_reduced, ticket.event.price_full)
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

def auto_obliterate(ticket_number):
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

    print(f'Ticket valid = {ticket_valid}')

    ingresso = None

    if ticket.status == "Printed" or ticket.status == "New" :
        ticket.status= 'Obliterated'
        ticket.save()
        prices = (0.0, ticket.event.price_reduced, ticket.event.price_full)
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
 
    return 

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
                json.dump(hall_status,jfp)
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
        items = OrderEvent.objects.filter(order_id=order.pk)
        items_number = items.count()
        if items_number < 2:
            order_killed = Order.objects.get(id=order.pk)
            order_killed.delete()

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
        elif orderevent_subs_type == 'center' or orderevent_subs_type=='end':
            pattern = re.compile(f',{deleted_orderevent}\$[0-2]')
            orderevents_new = re.sub(pattern,'',orderevents_old)
            userevent.ordersevents = orderevents_new
        elif orderevent_subs_type == 'only':
            pass
            # userevent.delete()
                        



    seats_price_old = userevent.seats_price
    seats_price_new = ''




    for key , pattern in seat_patterns.items():
        if bool(re.match(pattern, seats_price_old)):
            subs_type = key

    if subs_type == 'begin':
        seats_price_new = re.sub(seat_patterns['begin'],'',seats_price_old)
        userevent.seats_price = seats_price_new
        userevent.save()
    elif subs_type == 'center' or subs_type=='end':
        pattern = re.compile(f',{removed_seat}\$[0-2]')
        seats_price_new = re.sub(pattern,'',seats_price_old)
        userevent.seats_price = seats_price_new
        userevent.save()
    elif subs_type == 'only':
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
    
        userevent = UserEvent.objects.filter(event_id = event.pk).get(user_id=user.id)
        seats_price = userevent.seats_price
        seats_price_new = re.sub(find_pattern,seat_price_new,seats_price)
        userevent.seats_price = seats_price_new

        userevent.save    

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
    
        userevent = UserEvent.objects.filter(event_id = event.pk).get(user_id=user.id)
        seats_price = userevent.seats_price
        seats_price_new = re.sub(find_pattern,seat_price_new,seats_price)
        userevent.seats_price = seats_price_new

        userevent.save    

    return redirect(reverse('edit_order', kwargs={"orderevent_id": item.pk}))