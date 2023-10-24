from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages, auth
from django.core.exceptions import EmptyResultSet, ObjectDoesNotExist, MultipleObjectsReturned
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from .models import SellingSeats, BoxOfficeTransaction
from .escpos_printer import EscPosPrinter, EscPosDummy, EscPosNetwork
from escpos.printer import Usb, USBNotFoundError, Dummy
from store.models import Event
from orders.models import OrderEvent, UserEvent
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
    users_event = UserEvent.objects.filter(event__id=current_event.pk)
    # verifica esistenza dell'OrderEvent di apertura della cassa con utente 'cassa' , 'laboratorio', username 'amministrazione@teatrocambiano.com'
    # se manca il record specifico lo crea
    boxoffice_orderevent = None
    if event_orders.count() > 0:
        for item in event_orders:
            if item.user.first_name == "Cassa" and item.user.last_name == "Laboratorio":
                boxoffice_orderevent = item

    if boxoffice_orderevent is None:
        boxoffice_user = Account.objects.get(first_name = 'Cassa', last_name = 'Laboratorio')
        boxoffice_orderevent = OrderEvent()
        boxoffice_orderevent.user = boxoffice_user
        boxoffice_orderevent.event = current_event
        boxoffice_orderevent.save()
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

    printer_status: bool = printer_ready()

    context = {
        'hall_status': hall_status,
        'rows': rows,
        'json_file' : json_file_path,
        'current_event' : current_event,
        'event_orders' : event_orders,
        'users_event' : users_event,
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
    context = {
        'event' : current_event,
        'cart_items' : cart_items,
        'total' : total,
        'taxable': taxable,
        'tax': tax,
    }
    return render(request,'boxoffice/boxoffice_cart.html', context)

def boxoffice_remove_cart(request, item_id):

    item = get_object_or_404(SellingSeats, id=item_id)
    seat = item.seat
    event = item.event
    item.delete()
    # del item
    json_file_path= os.path.abspath(event.get_json_path())
    with open(json_file_path,'r') as jfp:
        hall_status = json.load(jfp)
    try:
        if hall_status[seat]['status'] == 3 or hall_status[seat]['status'] == 4:
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

def boxoffice_print(request, event_id):
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
        ticket.orderevent = OrderEvent.objects.get(event_id=current_event.pk, user=boxoffice_user )
        ticket.event = current_event
        ticket.user = boxoffice_user
        
        ticket.number=f"{ticket.sell_mode[0]}{current_event.date_time.strftime('%Y%m%d')}.{show.pk:04d}.{f'{serial:03d}'}"
        data['numero']= ticket.number

        ticket.save()

        # aggiorna il OrderEvent della Cassa per questo Evento
        #OrderEvent di apertura della cassa con utente 'cassa' , 'laboratorio', username 'amministrazione@teatrocambiano.com'
        boxoffice_orderevent = OrderEvent.objects.get(event__id=current_event.pk, user__last_name='Laboratorio', user__first_name = "Cassa"  )

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
        ticket_image_l_rotated= ticket_image_l.transpose(Image.ROTATE_90)
        # threshold = 127
        # ticket_image_l_rotated = ticket_image_l_rotated.point(lambda x: 255 if x > threshold else 0)
        # ticket_image_l_rotated = ticket_image_l_rotated.filter(ImageFilter.CONTOUR)
        if not recovery:
            ticket_image_l_rotated.save('the_ticket.png', 'PNG')
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

        }
    with open(json_file_path,'w') as jfp:
        json.dump(hall_status,jfp)
   


    return render(request, 'boxoffice/ticket_printed.html', context)

def close_transaction(request, event_id):
    current_event = Event.objects.get(id = event_id)
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
        payment_method = '',
        amount_paid = '0,0',
        status = 'Paid'
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
        paginator = Paginator(users_event, 5)
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
                print(order_str, type(order_str))
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

def edit_order(requeste, order_id):
    return HttpResponse(f'<H1>The page of change order {order_id}.</H1>')

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