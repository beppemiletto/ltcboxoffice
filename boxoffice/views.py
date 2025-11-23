from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages, auth
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import EmptyResultSet, ObjectDoesNotExist, MultipleObjectsReturned
from django.db import transaction, models
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.mail import EmailMultiAlternatives
from django.utils.formats import localize
from email.mime.image import MIMEImage
from accounts.models import Account
from wsgiref.util import FileWrapper
from .models import SellingSeats , PaymentMethod, BoxOfficeTransaction, CustomerProfile, BoxOfficeBookingEvent
from .forms import Barcode_Reader, OrderEventForm, CustomerProfileForm, CustomerShortForm
from .escpos_printer import EscPosPrinter, EscPosDummy, EscPosNetwork
from .price_utils import extend_price_array, safe_price_access, INGRESSI_NAMES, get_price_name, is_subscription
from escpos.printer import Usb, USBNotFoundError, Dummy
from store.models import Event
from orders.models import OrderEvent, UserEvent, Order, Payment
from subscriptions.models import SubscriptionUsage
from subscriptions.utils import is_subscription_price_code, get_subscription_by_price_code
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
from ltcboxoffice.settings import MEDIA_ROOT
from django.conf import settings
from openpyxl import Workbook


def get_printer():
    """
    Get the configured printer based on settings.
    Returns: (printer_object, recovery_mode)
    """
    printer_type = getattr(settings, 'PRINTER_TYPE', 'dummy')
    
    if printer_type == 'network':
        try:
            host = getattr(settings, 'PRINTER_NETWORK_HOST', '192.168.1.100')
            port = getattr(settings, 'PRINTER_NETWORK_PORT', 9100)
            timeout = getattr(settings, 'PRINTER_NETWORK_TIMEOUT', 60)
            printer = EscPosNetwork(host=host, port=port, timeout=timeout)
            print(f'Stampante di rete connessa: {host}:{port}')
            return (printer, False)
        except Exception as e:
            print(f'Errore connessione stampante di rete: {e}')
            return (EscPosDummy(), True)
    
    elif printer_type == 'usb':
        try:
            vendor = getattr(settings, 'PRINTER_USB_VENDOR', 0x0483)
            product = getattr(settings, 'PRINTER_USB_PRODUCT', 0x5840)
            timeout = getattr(settings, 'PRINTER_USB_TIMEOUT', 0)
            in_ep = getattr(settings, 'PRINTER_USB_IN_EP', 0x81)
            out_ep = getattr(settings, 'PRINTER_USB_OUT_EP', 0x03)
            printer = EscPosPrinter(
                idVendor=vendor,
                idProduct=product,
                timeout=timeout,
                in_ep=in_ep,
                out_ep=out_ep
            )
            print('Stampante USB connessa')
            return (printer, False)
        except (USBNotFoundError, Exception) as e:
            print(f'Errore stampante USB: {e}')
            return (EscPosDummy(), True)
    
    else:  # dummy mode
        print('Modalità stampante dummy (emulazione)')
        return (EscPosDummy(), True)


def get_or_create_session_id(request):
    """
    Get or create a unique session ID for isolating concurrent box office operations.
    Each browser session gets a unique ID to prevent cart conflicts between multiple cashiers.
    """
    if 'boxoffice_session_id' not in request.session:
        import uuid
        request.session['boxoffice_session_id'] = str(uuid.uuid4())
        request.session.modified = True
    return request.session['boxoffice_session_id']


def clear_session_cart(session_id, event_id=None):
    """
    Clear all SellingSeats for a specific session.
    If event_id is provided, only clear seats for that event.
    """
    query = SellingSeats.objects.filter(session_id=session_id)
    if event_id:
        query = query.filter(event_id=event_id)
    query.delete()


# Create your views here.
@login_required(login_url='login')
def boxoffice(request):
    if request.user.is_staff:
        now = datetime.now(pytz.timezone('Europe/Rome'))
        events = Event.objects.filter(show__is_in_billboard=True)
        time_diff = timedelta(
            days= 365
        )
        next_close_event = None
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
    
    session_id = get_or_create_session_id(request)
    
    if request.method == 'POST':
        go = False
        selected_seats=[]
        selected_seats_str = request.POST['selected_seats']
        cart_items = []
        costs = current_event.prices()
        ingressi  = ['Gratuito','Ridotto' , 'Intero']
        total = 0.0
        try:
            sellingseats = SellingSeats.objects.filter(session_id=session_id, event=current_event)
            for sellingseat in sellingseats:
                cart_items.append(sellingseat)
                go = True
        except:
            pass
        if len(selected_seats_str):
            selected_seats = selected_seats_str.strip().split(',')
            try:
                # Lock atomico per prevenire double-booking dello stesso posto da cassieri diversi
                with transaction.atomic():
                    # Rileggi JSON dentro la transazione per avere stato aggiornato
                    with open(json_file_path,'r') as jfp:
                        hall_status = json.load(jfp)
                    
                    for seat in selected_seats:
                        # Verifica che il posto sia ancora disponibile
                        if hall_status[seat]['status'] not in [0, 1]:  # 0=free, 1=selected by user
                            messages.warning(request, f"Il posto {seat} è già stato venduto da un altro operatore.")
                            continue
                        
                        hall_status[seat]['status'] = 4
                        sellingseat = SellingSeats()
                        sellingseat.seat = seat
                        sellingseat.event = current_event
                        sellingseat.session_id = session_id
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

                    # Scrivi JSON aggiornato dentro la transazione
                    with open(json_file_path,'w') as jfp:
                        json.dump(hall_status,jfp, indent=2)

            except Exception as e:
                print(f'Errore durante selezione posti in event(): {e}')
                messages.error(request, "Errore durante la selezione dei posti. Riprova.")

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
                    sold_count = 0
                    total_count = 0

                    # Count all seats with this orderevent_number in hall_status
                    # This includes both booked (status=1) and sold (status=5) seats
                    orderevent_number = orderevent.orderevent_number
                    for seat_name, seat_data in hall_status.items():
                        if seat_data.get('order') == orderevent_number:
                            total_count += 1
                            # Status 5 = sold (payed)
                            if seat_data['status'] == 5:
                                sold_count += 1

                    # Also add current seats still in booking to display
                    for seat_price in orderevent.seats_price.split(','):
                        seat_name = seat_price.split('$')[0]
                        seat = f"{seat_name},"
                        seats.append(seat)

                    del seat_price, seat

                    orders[user_event.user.email]['orders'][orderevent.pk] = {
                        'seats': seats,
                        'sold': sold_count,
                        'total': total_count
                    }
            del order_event, seats

            # The user event remained empty since the ordeevents have been expired or removed
            # so the item in the dictionary is removed
            if empty_user_event:
                del orders[user_event.user.email]
                



        del user_event, event_orders, event_id, jfp, boxoffice_orderevent, r_data, k

    boxofficebookingevent = BoxOfficeBookingEvent.objects.filter(event=current_event).filter(expired=False).order_by('customer__last_name')

    # Add sold/total count for boxoffice bookings
    boxoffice_bookings_with_count = []
    for booking in boxofficebookingevent:
        sold_count = 0
        total_count = 0
        seats_list = []

        # Count all seats with this booking_number in hall_status
        # This includes both booked (status=1) and sold (status=5) seats
        booking_number = booking.booking_number
        for seat_name, seat_data in hall_status.items():
            if seat_data.get('order') == booking_number:
                total_count += 1
                # Status 5 = sold (payed)
                if seat_data['status'] == 5:
                    sold_count += 1

        # Also collect current seats still in booking for display
        if booking.seats_price:
            for seat_price in booking.seats_price.split(','):
                if seat_price.strip():
                    seat_name = seat_price.split('$')[0]
                    seats_list.append(seat_name)

        boxoffice_bookings_with_count.append({
            'booking': booking,
            'sold': sold_count,
            'total': total_count,
            'seats': seats_list
        })

    printer_status: bool = printer_ready()

    context = {
        'hall_status': hall_status,
        'rows': rows,
        'json_file' : json_file_path,
        'current_event' : current_event,
        'orders' : orders,
        'printer_ready': printer_status,
        'boxofficebookings': boxoffice_bookings_with_count,
    }

    # return HttpResponse(f"Apriamo allegramente la pagina di gestione della cassa per evento numero {event_id}.")
    return render(request, 'boxoffice/boxoffice_main.html',context)

def boxoffice_cart(request, event_id):
    cart_items = []
    current_event = Event.objects.get(id = event_id)
    session_id = get_or_create_session_id(request)
    sellingseats = SellingSeats.objects.filter(session_id=session_id, event=current_event)
    total = 0.0
    for sellingseat in sellingseats:
        cart_items.append(sellingseat)
        total += sellingseat.cost
    tax = current_event.vat_rate
    taxable =int( (total / (100 + tax) )* 10000) / 100
    payment_methods = PaymentMethod.objects.all()
    
    # Check for any subscription issues
    subscription_warnings = []
    for item in cart_items:
        if is_subscription(item.price) and not item.subscription_code:
            subscription_warnings.append(f"Posto {item.seat}: inserire codice abbonamento")
    
    context = {
        'event' : current_event,
        'cart_items' : cart_items,
        'total' : total,
        'taxable': taxable,
        'tax': tax,
        'vat_rate': tax,
        'payments_methods': payment_methods,
        'subscription_warnings': subscription_warnings,
    }
    return render(request,'boxoffice/boxoffice_cart.html', context)

def boxoffice_cart_cancel(request, event_id):
    event = Event.objects.get(id = event_id)
    session_id = get_or_create_session_id(request)
    sellingseats = SellingSeats.objects.filter(session_id=session_id, event=event)
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
                try:
                    orderevent = BoxOfficeBookingEvent.objects.get(booking_number=sellingseat.orderevent)
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
    # Extend costs array to support subscription codes (3-6 = €0.00)
    costs_extended = extend_price_array(costs)
    ingressi = INGRESSI_NAMES
    
    price_old = item.price
    if price_old < 6:
        price_new = price_old + 1
    else:
        price_new = 0
    
    item.price = price_new
    item.cost = safe_price_access(costs_extended, price_new)
    item.ingresso = ingressi[price_new] if price_new < len(ingressi) else f"Codice {price_new}"
    item.save()

    return redirect(reverse('boxoffice_cart', kwargs={"event_id": current_event.pk}))


def boxoffice_minus_price(request, item_id = None):
    item = SellingSeats.objects.get(id=item_id)
    current_event = item.event
    costs = current_event.prices()
    # Extend costs array to support subscription codes (3-6 = €0.00)
    costs_extended = extend_price_array(costs)
    ingressi = INGRESSI_NAMES
    
    price_old = item.price
    if price_old > 0:
        price_new = price_old - 1
    else:
        price_new = 6  # Wrap around to max
    
    item.price = price_new
    item.cost = safe_price_access(costs_extended, price_new)
    item.ingresso = get_price_name(price_new)
    item.save()

    return redirect(reverse('boxoffice_cart', kwargs={"event_id": current_event.pk}))

def boxoffice_set_price(request, item_id=None, price_code=0):
    """
    Directly set the price code for a boxoffice item (called from dropdown).
    """
    item = SellingSeats.objects.get(id=item_id)
    current_event = item.event
    costs = current_event.prices()
    # Extend costs array to support subscription codes (3-6 = €0.00)
    costs_extended = extend_price_array(costs)
    ingressi = INGRESSI_NAMES
    
    price_new = int(price_code)
    
    # Validate the price code is in valid range
    if price_new < 0 or price_new > 6:
        return redirect(reverse('boxoffice_cart', kwargs={"event_id": current_event.pk}))
    
    item.price = price_new
    item.cost = safe_price_access(costs_extended, price_new)
    item.ingresso = ingressi[price_new] if price_new < len(ingressi) else f"Codice {price_new}"
    item.save()

    return redirect(reverse('boxoffice_cart', kwargs={"event_id": current_event.pk}))

def boxoffice_print(request, event_id, method_id=None, orderevent_id=None, mode_id=None):
    # Get configured printer
    printer, recovery = get_printer()
    
    boxoffice_user = Account.objects.get(first_name = 'Cassa', last_name = 'Laboratorio')
    current_event = Event.objects.get(id = event_id)
    
    # Handle free transactions (method_id=0 means no payment required)
    if method_id == 0 or method_id == '0':
        payment_method = None  # Will be set to first available or handled as free
    else:
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
    # Extend arrays to support subscription codes (3-6)
    costs_extended = extend_price_array(costs)
    ingressi = INGRESSI_NAMES

    show= current_event.show
    session_id = get_or_create_session_id(request)
    sold_seats = SellingSeats.objects.filter(session_id=session_id, event=current_event)

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
    payment.payment_method = payment_method.slug if payment_method else 'free'
    payment.amount_paid=amount_paid
    payment.status='COMPLETED'
    payment.save()

    header= {
        'date' : localize(current_event.date_time),
        'show' : show.shw_title,
    }

    # Printer emulation data
    emulated_print_data = []
    
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
        data['ingresso'] = ingressi[sold_seat.price] if sold_seat.price < len(ingressi) else f"Codice {sold_seat.price}"
        data['costo'] = safe_price_access(costs_extended, sold_seat.price)
        ticket.orderevent = orderevent.pk
        ticket.user = user
        ticket.payment = payment
        data['numero']= ticket.number

        ticket.save()

        # Track subscription usage when selling with subscription code
        if is_subscription_price_code(sold_seat.price) and sold_seat.subscription_code:
            from subscriptions.models import Subscription
            try:
                subscription = Subscription.objects.get(subscription_number=sold_seat.subscription_code)
                if subscription.is_valid():
                    # Check if usage already exists (evita duplicati)
                    existing_usage = SubscriptionUsage.objects.filter(
                        subscription=subscription,
                        event=current_event,
                        seat=sold_seat.seat
                    ).first()
                    
                    if not existing_usage:
                        # Create usage record with actual subscription owner
                        SubscriptionUsage.objects.create(
                            subscription=subscription,
                            event=current_event,
                            seat=sold_seat.seat,
                            used_by=request.user if request.user.is_authenticated else boxoffice_user,
                        )
                        # Counter incremented automatically by SubscriptionUsage.save()
            except Subscription.DoesNotExist:
                pass  # Should not happen, already verified

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
                printer.print_list_header(header=header)
            printer.print_list_item(data=data)
            if idx == (seats_number -1):
                printer.print_list_footer(data=data)
        else:
            # Emulation mode - collect data for display
            emulated_print_data.append({
                'seat': data['seat'],
                'ingresso': data['ingresso'],
                'costo': data['costo'],
                'numero': data['numero'],
            })

    
        hall_status[ticket.seat]['status'] = 5
        tickets_list.append(ticket)

        
    context = {
       'event': current_event,
       'tickets_list':tickets_list,
       'payment_method': payment_method,
       'recovery_mode': recovery,
       'emulated_print_data': emulated_print_data if recovery else None,
       'print_header': header if recovery else None,

        }
    
    for tckt in tickets_list:
        request = auto_obliterate(request, tckt.number)


    with open(json_file_path,'w') as jfp:
        json.dump(hall_status,jfp, indent=2)
   

    response = close_transaction(request, context=context)
    return response
    # return render(request, 'boxoffice/ticket_printed.html', context)

def close_transaction(request, event_id=None, context=None):
    if context is None:
        context = {}
    
    # If event_id is provided directly (from URL), get the event
    if event_id and 'event' not in context:
        context['event'] = Event.objects.get(id=event_id)

    current_event = context['event']
    costs = current_event.prices()
    # Extend costs array to support subscription codes (3-6 = €0.00)
    costs_extended = extend_price_array(costs)
    ingressi = ['Gratuito','Ridotto', 'Intero']
    show= current_event.show
    boxoffice_user = Account.objects.get(first_name = 'Cassa', last_name = 'Laboratorio')

    try:
        payments = BoxOfficeTransaction.objects.filter(event=current_event)
        serial_number:int = payments.count() + 1
    except:
        serial_number:int = 1 
    
    # Get payment_method from context or use default
    payment_method = context.get('payment_method')
    if payment_method is None:
        # Try to get first available payment method as default
        try:
            payment_method = PaymentMethod.objects.first()
        except:
            payment_method = None
    
    transaction = BoxOfficeTransaction(
        user = boxoffice_user,
        event = current_event,
        seats_sold = '',
        payment_id = f'{current_event.pk:05d}.{serial_number:03d}',
        payment_method = payment_method,
        amount_paid = "total",
        status = 'Completed'
    )

    session_id = get_or_create_session_id(request)
    sold_seats = SellingSeats.objects.filter(session_id=session_id, event=current_event)
    json_file_path= os.path.abspath(current_event.get_json_path())
    with open(json_file_path,'r') as jfp:
        hall_status = json.load(jfp)

    seats_list:list = []
    totale:float = 0
    for sold_seat in sold_seats:
        ticket = Ticket.objects.get(event=current_event, seat = sold_seat.seat)
        if ticket.status == 'New':
            ticket.status = 'Obliterated'
        totale += safe_price_access(costs_extended, ticket.price)
        ticket.save()
        seats_list.append(f'{sold_seat.seat}${ticket.price}')
        sold_seat.delete()
    
    transaction.seats_sold = ','.join(seats_list)
    transaction.amount_paid = "{:5.2f}".format(totale)
    transaction.save()
    
    # If in recovery mode, show emulated print instead of redirecting
    if context.get('recovery_mode', False):
        return render(request, 'boxoffice/ticket_printed.html', context)
    
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
            if td.days >= -15:
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
        session_id = get_or_create_session_id(request)
        try:
            sellingseats = SellingSeats.objects.filter(session_id=session_id, event=current_event)
            for sellingseat in sellingseats:
                cart_items.append(sellingseat)
                go = True
        except:
            pass
        if len(selected_seats_str):
            selected_seats = selected_seats_str.strip().split(',')
            try:
                # Lock atomico per prevenire double-booking dello stesso posto da cassieri diversi
                with transaction.atomic():
                    # Rileggi JSON dentro la transazione per avere stato aggiornato
                    with open(json_file_path,'r') as jfp:
                        hall_status = json.load(jfp)
                    
                    for seat in selected_seats:
                        # Verifica che il posto sia ancora disponibile
                        if hall_status[seat]['status'] not in [0, 1]:  # 0=free, 1=selected by user
                            messages.warning(request, f"Il posto {seat} è già stato venduto da un altro operatore.")
                            continue
                        
                        hall_status[seat]['status'] = 4
                        sellingseat = SellingSeats()
                        sellingseat.seat = seat
                        sellingseat.event = current_event
                        sellingseat.session_id = session_id
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

                    # Scrivi JSON aggiornato dentro la transazione
                    with open(json_file_path,'w') as jfp:
                        json.dump(hall_status,jfp, indent=2)

            except Exception as e:
                print(f'Errore durante selezione posti in change_bookings(): {e}')
                messages.error(request, "Errore durante la selezione dei posti. Riprova.")

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

def select_booking_seats(request, booking_id, mode):
    """
    Permette di selezionare quali posti della prenotazione vendere.
    Utile per ritiri parziali (es: gruppo di 4, poi 3, poi 6 da prenotazione di 13 posti)
    """
    if mode == '1':
        booking = OrderEvent.objects.get(id=booking_id)
        booking_number = booking.orderevent_number
        customer_name = f"{booking.user.first_name} {booking.user.last_name}"
    elif mode == '2':
        booking = BoxOfficeBookingEvent.objects.get(id=booking_id)
        booking_number = booking.booking_number
        customer_name = f"{booking.customer.first_name} {booking.customer.last_name}"
    
    # Parse seats from booking
    seats_data = []
    costs_extended = extend_price_array(booking.event.prices())
    
    for seat_price in booking.seats_price.split(','):
        seat, price_code = seat_price.split('$')
        price_code = int(price_code)
        
        seats_data.append({
            'seat': seat,
            'price_code': price_code,
            'price_name': get_price_name(price_code),
            'cost': safe_price_access(costs_extended, price_code),
        })
    
    print(f"DEBUG: booking.seats_price = {booking.seats_price}")
    print(f"DEBUG: seats_data = {seats_data}")
    
    if request.method == 'POST':
        # Get selected seats from form
        selected_seats = request.POST.getlist('selected_seats')
        
        if not selected_seats:
            messages.warning(request, "Seleziona almeno un posto da vendere.")
            return redirect('select_booking_seats', booking_id=booking_id, mode=mode)
        
        # Create SellingSeats for selected seats only
        session_id = get_or_create_session_id(request)
        costs_extended = extend_price_array(booking.event.prices())
        
        # Prima elimina eventuali posti già presenti nel carrello per questa prenotazione
        # per evitare duplicati se l'utente torna indietro e riseleziona
        SellingSeats.objects.filter(
            session_id=session_id,
            event=booking.event,
            orderevent=booking_number
        ).delete()
        
        for seat_price in booking.seats_price.split(','):
            seat, price_code = seat_price.split('$')
            
            # Only add to cart if seat was selected
            if seat in selected_seats:
                price_idx = int(price_code)
                ordered_sellingseat = SellingSeats(
                    event=booking.event,
                    orderevent=booking_number,
                    seat=seat,
                    price=price_idx,
                    cost=safe_price_access(costs_extended, price_idx),
                    ingresso=get_price_name(price_idx),
                    session_id=session_id
                )
                ordered_sellingseat.save()
        
        # Get cart items
        sellingseats = SellingSeats.objects.filter(session_id=session_id, event=booking.event)
        cart_items = list(sellingseats)
        total = sum(s.cost for s in cart_items)
        
        tax = booking.event.vat_rate
        taxable = int((total / (100 + tax)) * 10000) / 100
        
        # Check if all seats were selected
        all_seats_selected = len(selected_seats) == len(booking.seats_price.split(','))
        
        # Mark booking as expired only if all seats were taken
        if all_seats_selected:
            booking.expired = True
            booking.save()
            messages.success(request, f"Tutti i posti della prenotazione sono stati venduti. Prenotazione chiusa.")
        else:
            # Update booking removing sold seats
            remaining_seats = []
            for seat_price in booking.seats_price.split(','):
                seat, price = seat_price.split('$')
                if seat not in selected_seats:
                    remaining_seats.append(seat_price)
            
            booking.seats_price = ','.join(remaining_seats)
            booking.save()
            messages.info(request, f"Venduti {len(selected_seats)} posti. Rimangono {len(remaining_seats)} posti nella prenotazione.")
        
        payment_methods = PaymentMethod.objects.all()
        context = {
            'event': booking.event,
            'cart_items': cart_items,
            'total': total,
            'taxable': taxable,
            'tax': tax,
            'payments_methods': payment_methods,
            'orderevent': booking,
            'mode': mode,
        }
        return render(request, 'boxoffice/boxoffice_cart.html', context)
    
    # GET request - show selection form
    context = {
        'booking': booking,
        'booking_number': booking_number,
        'customer_name': customer_name,
        'seats_data': seats_data,
        'event': booking.event,
        'mode': mode,
        'total_seats': len(seats_data),
    }
    return render(request, 'boxoffice/select_booking_seats.html', context)

def confirm_booking_selection(request, event_id, orderevent_id, mode):
    """
    Rimuove dal carrello i posti NON selezionati e li rimette nella prenotazione.
    I posti selezionati rimangono nel carrello per procedere al pagamento.
    """
    if request.method != 'POST':
        return redirect('event', event_id=event_id)
    
    # Get selected seat IDs from form
    selected_seats_ids = request.POST.get('selected_seats', '').split(',')
    selected_seats_ids = [int(sid) for sid in selected_seats_ids if sid]
    
    if not selected_seats_ids:
        messages.warning(request, "Nessun posto selezionato!")
        return redirect('event', event_id=event_id)
    
    # Get booking
    if mode == '1':
        booking = OrderEvent.objects.get(id=orderevent_id)
    elif mode == '2':
        booking = BoxOfficeBookingEvent.objects.get(id=orderevent_id)
    
    # Get all seats in cart for this event and session
    session_id = get_or_create_session_id(request)
    all_cart_seats = SellingSeats.objects.filter(session_id=session_id, event_id=event_id)
    
    # Find seats to remove (not selected)
    seats_to_remove = []
    for seat in all_cart_seats:
        if seat.id not in selected_seats_ids:
            seats_to_remove.append(seat)
    
    # Add removed seats back to booking
    if seats_to_remove:
        current_seats = booking.seats_price.split(',') if booking.seats_price else []
        
        for seat in seats_to_remove:
            # Add back to booking: format "seat$price_code"
            seat_entry = f"{seat.seat}${seat.price}"
            current_seats.append(seat_entry)
            # Delete from cart
            seat.delete()
        
        # Update booking seats_price
        booking.seats_price = ','.join(current_seats)
        booking.save()
        
        messages.info(request, f"Rimossi {len(seats_to_remove)} posti dal carrello. Rimangono nella prenotazione.")
    
    # If all seats were removed, don't expire booking
    remaining_in_cart = SellingSeats.objects.filter(session_id=session_id, event_id=event_id).count()
    
    if remaining_in_cart == 0:
        messages.warning(request, "Tutti i posti sono stati rimossi! Prenotazione mantenuta attiva.")
        return redirect('event', event_id=event_id)
    
    messages.success(request, f"Confermati {remaining_in_cart} posti per la vendita.")
    
    # Redirect back to cart to proceed with payment
    return redirect('boxoffice_cart', event_id=event_id)

def sell_booking(request, order = None, mode=None):
    from subscriptions.utils import get_subscription_price_options
    
    if mode == '1':
        order_event =  OrderEvent.objects.get(id=order)
        order_number = order_event.orderevent_number
    elif mode=='2':
        order_event =  BoxOfficeBookingEvent.objects.get(id=order)
        order_number = order_event.booking_number

    ingressi= ['Gratuito', 'Ridotto', 'Intero']
    costs = order_event.event.prices()
    costs_extended = extend_price_array(costs)
    booked_seats_price = order_event.seats_price
    session_id = get_or_create_session_id(request)
    
    # Get user's available subscriptions and map codes to subscription objects
    user_subscriptions = {}
    subscription_codes = {}  # Maps price_code to subscription_number
    if order_event.user:
        subscription_options = get_subscription_price_options(order_event.user)
        for opt in subscription_options:
            if opt['remaining'] > 0:
                user_subscriptions[opt['code']] = opt
                subscription_codes[opt['code']] = opt['subscription_number']
    
    for seat_price in booked_seats_price.split(','):
        ordered_seat, ordered_price  = seat_price.split('$')
        price_idx = int(ordered_price)
        
        # Se il prezzo è un codice abbonamento (3-6) e l'utente ha quell'abbonamento disponibile,
        # mantieni il codice abbonamento e imposta il subscription_code
        final_price_idx = price_idx
        final_cost = safe_price_access(costs_extended, price_idx)
        subscription_number = None
        
        # Controlla se è un codice abbonamento e se l'utente ce l'ha ancora disponibile
        if is_subscription_price_code(price_idx) and price_idx in user_subscriptions:
            # Mantieni il codice abbonamento
            final_price_idx = price_idx
            final_cost = 0.0  # Abbonamenti hanno costo 0
            subscription_number = subscription_codes.get(price_idx)
        
        ordered_sellingseat = SellingSeats(
            event = order_event.event,
            orderevent = order_number,
            seat = ordered_seat,
            price = final_price_idx,
            cost = final_cost,
            ingresso = final_cost,
            session_id = session_id,
            subscription_code = subscription_number  # Imposta automaticamente il codice abbonamento
        )
        ordered_sellingseat.save()
    sellingseats = SellingSeats.objects.filter(session_id=session_id, event=order_event.event)

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
    """Check if the configured printer is ready."""
    try:
        printer, recovery = get_printer()
        return not recovery
    except Exception as e:
        print(f'Errore controllo stampante: {e}')
        return False


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
        # Extend prices array to support subscription codes (3-6 = €0.00)
        prices_extended = extend_price_array(prices)
        sell_mode_code = ticket_number[0]
        sell_modes = { 'W':'Web','C':'Cassa','P': 'Prenotazione' }
        ingresso = Ingresso(
                ticket_number = ticket.number,
                seat = ticket.seat,
                event = ticket.event,
                price = safe_price_access(prices_extended, ticket.price),
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
            barcode_code = form.cleaned_data['barcode_code'].replace('?', '_')
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
        'begin' : re.compile(rf"^{removed_seat}\$[0-2],"),
        'center' : re.compile(rf"^.+,{removed_seat}\$[0-2],"),
        'only' : re.compile(rf"^{removed_seat}\$[0-2]$"),
        'end' : re.compile(rf"^.+,{removed_seat}\$[0-2]$")
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
        pattern = re.compile(rf',{removed_seat}\$[0-2]')
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
            pattern = re.compile(rf',{deleted_orderevent}\$[0-2]')
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


    find_pattern = re.compile(rf'{seat}\$[0-2]')
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


    find_pattern = re.compile(rf'{seat}\$[0-2]')
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
    from subscriptions.utils import is_subscription_price_code
    
    email_data = {}
    orderevent = BoxOfficeBookingEvent.objects.get(booking_number=number)
    event= orderevent.event

    prices = event.prices()
    # Extend prices array to support subscription codes (3-6 = €0.00)
    prices_extended = extend_price_array(prices)
    ingressi_names = INGRESSI_NAMES
    booked_seats = {}

    for item in orderevent.seats_price.split(','):
        seat, price = item.split('$')
        price_code = int(price)
        
        # Build seat info dict similar to booking flow
        is_subscription = is_subscription_price_code(price_code)
        booked_seats[seat] = {
            'price': safe_price_access(prices_extended, price_code),
            'is_subscription': is_subscription,
            'ingresso_type': ingressi_names[price_code] if price_code < len(ingressi_names) else f"Codice {price_code}"
        }

    email_data[orderevent.booking_number] = {
    'show':orderevent.event.show.shw_title,
    'datetime': orderevent.event.date_time,
    'seats': booked_seats
    }



    # Count the order events included in the single order
    orderevents_count = len(email_data)

    # Send order received email to customer 

    current_site = get_current_site(request)

    mail_subject = f'LTC BoxOffice. La tua prenotazione {number} è stata registrata!'
    email_context = {
        'count': orderevents_count,
        'customer': orderevent.customer,
        'email_data' : email_data,
    }
    message = render_to_string('boxoffice/order_changed_email.html', email_context).strip()
    to_email = [orderevent.customer.email,]
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

    send_email.send()

    current_event=orderevent.event

    return redirect(reverse('change_bookings', kwargs={"event_id": current_event.pk}))


def send_cancelemail(request, number):
    # Send order update email to customer
   # prepare a dictionary for email data
    from subscriptions.utils import is_subscription_price_code
    
    email_data = {}
    orderevent = BoxOfficeBookingEvent.objects.get(booking_number=number)
    event= orderevent.event

    prices = event.prices()
    # Extend prices array to support subscription codes (3-6 = €0.00)
    prices_extended = extend_price_array(prices)
    ingressi_names = INGRESSI_NAMES
    booked_seats = {}

    for item in orderevent.seats_price.split(','):
        seat, price = item.split('$')
        price_code = int(price)
        
        # Build seat info dict similar to booking flow
        is_subscription = is_subscription_price_code(price_code)
        booked_seats[seat] = {
            'price': safe_price_access(prices_extended, price_code),
            'is_subscription': is_subscription,
            'ingresso_type': ingressi_names[price_code] if price_code < len(ingressi_names) else f"Codice {price_code}"
        }

    email_data[orderevent.booking_number] = {
    'show':orderevent.event.show.shw_title,
    'datetime': orderevent.event.date_time,
    'seats': booked_seats
    }

    # Send order cancel email to customer 

    current_site = get_current_site(request)

    mail_subject = f'LTC BoxOffice. La tua prenotazione {number} è stata cancellata!'
    email_context = {
        'number': number,
        'customer': orderevent.customer,
        'email_data' : email_data,
    }
    message = render_to_string('boxoffice/order_erased_email.html', email_context).strip()
    to_email = [orderevent.customer.email,]
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

    send_email.send()

    current_event=orderevent.event

    orderevent.delete()

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
    # Extend prices array to support subscription codes (3-6 = €0.00)
    prices_extended = extend_price_array(prices)
    taxable:float = 0.0
    tax:float = event.vat_rate
    total:float = 0.0
    for key, item in cart_items.items():
        ingresso_code = int(item['ingresso'])
        item['ingresso_str'] = safe_price_access(prices_extended, ingresso_code)
        total += float(item['ingresso_str']) 
    taxable=total/(1+tax/100)
    
    if request.method=='POST':
        # controlla dati cliente
        form = CustomerShortForm(request.POST)
        if form.is_valid():
            modified_customer = False
            if customer.first_name != form.cleaned_data['first_name']:
                customer.first_name = form.cleaned_data['first_name'] 
                modified_customer = True
            if customer.last_name != form.cleaned_data['last_name']:
                customer.last_name = form.cleaned_data['last_name'] 
                modified_customer = True
            if customer.email != form.cleaned_data['email']:
                customer.email = form.cleaned_data['email'] 
                modified_customer = True
            if customer.phone_number != form.cleaned_data['phone_number']:
                customer.phone_number = form.cleaned_data['phone_number'] 
                modified_customer = True
            if modified_customer:
                customer.save() 
            del modified_customer
        return redirect(reverse('send_updatemail', kwargs={"number": boxofficebookingevent_number}))   
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

    find_pattern = re.compile(rf'{seat}\$[0-6]')
    seat_price_old = find_pattern.findall(seats_price)[0]
    place, price = seat_price_old.split('$')
    if int(price)<6:
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


    find_pattern = re.compile(rf'{seat}\$[0-6]')
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


def set_ingr_booking(request, number=None, seat=None, price_code=0):
    """
    Directly set the price code for a booking seat (called from dropdown).
    """
    item = get_object_or_404(BoxOfficeBookingEvent, booking_number=number)
    seats_price = item.seats_price
    
    price_new = int(price_code)
    
    # Validate the price code is in valid range
    if price_new < 0 or price_new > 6:
        return redirect(reverse('edit_booking', kwargs={"boxofficebookingevent_number": item.booking_number}))
    
    # Find and replace the seat price
    find_pattern = re.compile(rf'{seat}\$[0-6]')
    seat_price_old = find_pattern.findall(seats_price)
    
    if seat_price_old:
        seat_price_new = f'{seat}${price_new}'
        seats_price_new = re.sub(find_pattern, seat_price_new, seats_price)
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
        'begin' : re.compile(rf"^{removed_seat}\$[0-2],"),
        'center' : re.compile(rf"^.+,{removed_seat}\$[0-2],"),
        'only' : re.compile(rf"^{removed_seat}\$[0-2]$"),
        'end' : re.compile(rf"^.+,{removed_seat}\$[0-2]$")
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
        pattern = re.compile(rf',{removed_seat}\$[0-2]')
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

    number = booking.booking_number

    return redirect(reverse('send_cancelemail', kwargs={"number": number}))   

    booking.delete()

    return redirect(reverse('change_bookings', kwargs={"event_id": current_event.pk}))

def customers(request, event_id=None, customer=None):
    current_event = Event.objects.get(id=event_id)    
    if customer is not None:
        if request.method == 'POST':
            customer_profile_form = CustomerProfileForm(request.POST)
            if customer_profile_form.is_valid():
                email = customer_profile_form.cleaned_data['email']
                first_name = customer_profile_form.cleaned_data['first_name']
                last_name = customer_profile_form.cleaned_data['last_name']
                if customer_profile_form.cleaned_data['phone_number'] != '':
                    phone_number = customer_profile_form.cleaned_data['phone_number']
                if customer_profile_form.cleaned_data['address'] != '':
                    address = customer_profile_form.cleaned_data['address']
                if customer_profile_form.cleaned_data['city'] != '':
                    city = customer_profile_form.cleaned_data['city']
                if customer_profile_form.cleaned_data['province'] != '':
                    province = customer_profile_form.cleaned_data['province']
                if customer_profile_form.cleaned_data['post_code'] != '':
                    post_code = customer_profile_form.cleaned_data['post_code']
                try:
                    maybe_customers = CustomerProfile.objects.filter(email=email)
                    if maybe_customers.count() > 1:
                        pass
                    elif maybe_customers.count() > 0:
                        the_customer_already = maybe_customers.get(email=email)

                        the_customer_new = CustomerProfile()
                        the_customer_new_dict= {}
                        the_customer_new.first_name = first_name
                        the_customer_new_dict['first_name'] = first_name
                        the_customer_new.last_name = last_name
                        the_customer_new_dict['last_name'] = last_name
                        the_customer_new.email = email
                        the_customer_new_dict['email'] = email
                        the_customer_new.phone_number = customer_profile_form.cleaned_data['phone_number']
                        the_customer_new_dict['phone_number'] = customer_profile_form.cleaned_data['phone_number']
                        the_customer_new.address = customer_profile_form.cleaned_data['address']
                        the_customer_new_dict['address']  = customer_profile_form.cleaned_data['address']
                        the_customer_new.city = customer_profile_form.cleaned_data['city']
                        the_customer_new_dict['city'] = customer_profile_form.cleaned_data['city']
                        the_customer_new.province = customer_profile_form.cleaned_data['province']
                        the_customer_new_dict['province'] = customer_profile_form.cleaned_data['province']
                        the_customer_new.post_code = customer_profile_form.cleaned_data['post_code']
                        the_customer_new_dict['post_code'] = customer_profile_form.cleaned_data['post_code']

                        # save a JSON file to keep new data wothout passing them to and back from a template.

                        new_data_json = "new_data_customer.json"
                        with open(new_data_json,'w') as jfp:
                            json.dump(the_customer_new_dict,jfp, indent=2)

                        context =  {
                            'new_customer': the_customer_new,
                            'already_customer': the_customer_already,
                            'current_event': current_event,
                        }
                        return render(request,'boxoffice/customer_already_recorded.html',context) 

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

def customer_new_already(request, event_id=None, customer=None):
    current_event = Event.objects.get(id=event_id)    
    customer_already = CustomerProfile.objects.get(id=int(customer))
    if request.method == 'POST':
        # read a JSON file to keep new data wothout passing them to and back from a template.
        new_data_json = "new_data_customer.json"
        with open(new_data_json,'r') as jfp:
            customer_new_dict = json.load(jfp)
        customer_already.first_name = customer_new_dict['first_name']
        customer_already.last_name = customer_new_dict['last_name']
        customer_already.email = customer_new_dict['email']
        customer_already.phone_number =  customer_new_dict['phone_number']
        customer_already.address =  customer_new_dict['address']
        customer_already.city =  customer_new_dict['city']
        customer_already.province =  customer_new_dict['province']
        customer_already.post_code =  customer_new_dict['post_code']

        customer_already.save()

        del customer_new_dict

    return redirect(reverse('add_bookings', kwargs={'event_id': event_id, 'customer': customer_already.email}))



def list_bookings(request, event_id=None, customer=None):
    current_event = Event.objects.get(id=event_id)

    now = datetime.now(pytz.timezone('Europe/Rome'))
    
    xlsx_filename = f"{current_event.event_slug}_bookings_{now.strftime('%Y%m%d')}.xlsx"
    
    wb = Workbook()
    ws= wb.create_sheet(f'{current_event.show.shw_code}',0)
    ws.merge_cells('A1:G1')
    ws['A1'] = f"{current_event.show.shw_title} del {current_event.date_time}"
    start_row = 1
    try:
        start_row += 2
        ws.merge_cells(f'A{start_row}:G{start_row}')
        ws[f'A{start_row}'] = 'Prenotazioni attive da utenti WEB'
        start_row+=1
        active_orderevents = OrderEvent.objects.filter(event=current_event).filter(expired=False).order_by('user__last_name')
        if active_orderevents.count() < 1:
            raise
        ws[f'A{start_row}'] = 'O.E. Number' 
        ws[f'B{start_row}'] = 'Cognome' 
        ws[f'C{start_row}'] = 'Nome' 
        ws[f'D{start_row}'] = 'Email'
        ws[f'E{start_row}'] = 'Telefono'
        ws[f'F{start_row}'] = 'Posti' 
        ws[f'G{start_row}'] = 'Totale' 
        for order in active_orderevents:
            start_row+=1
            ws[f'A{start_row}'] = f'{order.pk}'
            ws[f'B{start_row}'] = f'{order.user.last_name}'
            ws[f'C{start_row}'] = f'{order.user.first_name}'
            ws[f'D{start_row}'] = f'{order.user.email}'
            ws[f'E{start_row}'] = f'{order.user.phone_number}'
            ws[f'F{start_row}'] = f'{order.seats_price}'             
            ws[f'G{start_row}'] = order.seats_count()             
    except:
        active_orderevents = None
        ws.merge_cells(f'A{start_row}:G{start_row}')
        ws[f'A{start_row}'] = 'Non ci sono prenotazioni attive di utenti WEB'
    
    try:
        start_row += 2
        ws.merge_cells(f'A{start_row}:G{start_row}')
        ws[f'A{start_row}'] = 'Prenotazioni attive da Box Office per clienti (email, social, segreteria,...)'
        start_row+=1
        active_boxofficebookingevent = BoxOfficeBookingEvent.objects.filter(event=current_event).filter(expired=False).order_by('customer__last_name')
        if active_boxofficebookingevent.count() < 1:
            raise 
        ws[f'A{start_row}'] = 'O. Number' 
        ws[f'B{start_row}'] = 'Cognome' 
        ws[f'C{start_row}'] = 'Nome' 
        ws[f'D{start_row}'] = 'Email'
        ws[f'E{start_row}'] = 'Telefono'
        ws[f'F{start_row}'] = 'Posti' 
        ws[f'G{start_row}'] = 'Totale' 
        for order in active_boxofficebookingevent:
            start_row+=1
            ws[f'A{start_row}'] = f'{order.pk}'
            ws[f'B{start_row}'] = f'{order.customer.last_name}'
            ws[f'C{start_row}'] = f'{order.customer.first_name}'
            ws[f'D{start_row}'] = f'{order.customer.email}'
            ws[f'E{start_row}'] = f'{order.customer.phone_number}'
            ws[f'F{start_row}'] = f'{order.seats_price}'             
            ws[f'G{start_row}'] = order.seats_count()             

    except:
        active_boxofficebookingevent = None
        ws.merge_cells(f'A{start_row}:G{start_row}')
        ws[f'A{start_row}'] = 'Non ci sono prenotazioni attive da clienti BoxOffice'

    try:
        start_row += 2
        ws.merge_cells(f'A{start_row}:G{start_row}')
        ws[f'A{start_row}'] = 'Prenotazioni vendute di utenti WEB (expired)'
        start_row+=1
        expired_orderevents = OrderEvent.objects.filter(event=current_event).filter(expired=True).order_by('user__last_name')
        if expired_orderevents.count() < 1:
            raise 
        ws[f'A{start_row}'] = 'O. Number' 
        ws[f'B{start_row}'] = 'Cognome' 
        ws[f'C{start_row}'] = 'Nome' 
        ws[f'D{start_row}'] = 'Email'
        ws[f'E{start_row}'] = 'Telefono'
        ws[f'F{start_row}'] = 'Posti' 
        ws[f'G{start_row}'] = 'Totale' 
        for order in expired_orderevents:
            start_row+=1
            ws[f'A{start_row}'] = f'{order.pk}'
            ws[f'B{start_row}'] = f'{order.user.last_name}'
            ws[f'C{start_row}'] = f'{order.user.first_name}'
            ws[f'D{start_row}'] = f'{order.user.email}'
            ws[f'E{start_row}'] = f'{order.user.phone_number}'
            ws[f'F{start_row}'] = f'{order.seats_price}'             
            ws[f'G{start_row}'] = order.seats_count()             

    except:
        expired_orderevents = None
        ws.merge_cells(f'A{start_row}:G{start_row}')
        ws[f'A{start_row}'] = 'Non ci sono prenotazioni vendute di utenti WEB'
    
    try:
        start_row += 2
        ws.merge_cells(f'A{start_row}:G{start_row}')
        ws[f'A{start_row}'] = 'Prenotazioni vendute di clienti BoxOffice mail, social, segreteria ... (expired)'
        start_row+=1
        expired_boxofficebookingevent = BoxOfficeBookingEvent.objects.filter(event=current_event).filter(expired=True).order_by('customer__last_name')
        if expired_boxofficebookingevent.count() < 1:
            raise 
        ws[f'A{start_row}'] = 'O. Number' 
        ws[f'B{start_row}'] = 'Cognome' 
        ws[f'C{start_row}'] = 'Nome' 
        ws[f'D{start_row}'] = 'Email'
        ws[f'E{start_row}'] = 'Telefono'
        ws[f'F{start_row}'] = 'Posti' 
        ws[f'G{start_row}'] = 'Totale' 
        for order in expired_orderevents:
            start_row+=1
            ws[f'A{start_row}'] = f'{order.pk}'
            ws[f'B{start_row}'] = f'{order.customer.last_name}'
            ws[f'C{start_row}'] = f'{order.customer.first_name}'
            ws[f'D{start_row}'] = f'{order.customer.email}'
            ws[f'E{start_row}'] = f'{order.customer.phone_number}'
            ws[f'F{start_row}'] = f'{order.seats_price}'             
            ws[f'G{start_row}'] = order.seats_count()    
    except:
        expired_boxofficebookingevent = None
        ws.merge_cells(f'A{start_row}:G{start_row}')
        ws[f'A{start_row}'] = 'Non ci sono prenotazioni vendute da clienti BoxOffice'


    file_path = os.path.join(MEDIA_ROOT , 'order_list_xlsx',xlsx_filename)
    relative_file_path = os.path.join('order_list_xlsx',xlsx_filename)

    
    try:
        wb.save(filename=file_path)
    except:
        os.makedirs(os.path.join(MEDIA_ROOT,'order_list_xlsx'))
        wb.save(filename=file_path)


    context = {
            'xlsx_filename':xlsx_filename,
            'file_path': file_path,
            'relative_file_path':relative_file_path,
            'event' : current_event,
            'active_orderevent': active_orderevents,
            'active_boxofficebookingevent' : active_boxofficebookingevent,
            'expired_orderevents': expired_orderevents,
            'expired_boxofficebookingevent':  expired_boxofficebookingevent

    }

    return render(request, 'boxoffice/event_order_list_xlsx.html', context)


# ==================== GESTIONE ABBONAMENTI ====================

@login_required(login_url='login')
def subscriptions_main(request):
    """
    Menu principale gestione abbonamenti
    """
    from subscriptions.models import Subscription, SubscriptionType
    
    # Statistiche rapide
    active_subscriptions = Subscription.objects.filter(status='ACTIVE').count()
    expired_subscriptions = Subscription.objects.filter(status='EXPIRED').count()
    
    # Ultimi abbonamenti venduti
    recent_subscriptions = Subscription.objects.select_related('user', 'subscription_type').all().order_by('-created_at')[:5]
    
    # Tipi di abbonamento disponibili
    subscription_types = SubscriptionType.objects.filter(is_active=True)
    
    context = {
        'active_subscriptions': active_subscriptions,
        'expired_subscriptions': expired_subscriptions,
        'recent_subscriptions': recent_subscriptions,
        'subscription_types': subscription_types,
    }
    
    return render(request, 'boxoffice/subscriptions_main.html', context)


@login_required(login_url='login')
def sell_subscription(request):
    """
    Vendita nuovo abbonamento
    """
    from subscriptions.models import Subscription, SubscriptionType
    from datetime import date, timedelta
    import random
    import string
    
    if request.method == 'POST':
        # Get form data
        subscription_type_id = request.POST.get('subscription_type')
        user_id = request.POST.get('user_id')
        payment_method_id = request.POST.get('payment_method')
        
        # Get or create user
        if user_id:
            user = Account.objects.get(id=user_id)
        else:
            # Create new customer
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            phone = request.POST.get('phone', '')
            
            user, created = Account.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone_number': phone,
                    'username': email,
                }
            )
        
        subscription_type = SubscriptionType.objects.get(id=subscription_type_id)
        payment_method = PaymentMethod.objects.get(id=payment_method_id)
        
        # Calculate validity
        valid_from = date.today()
        valid_to = valid_from + timedelta(days=subscription_type.valid_days)
        
        # Create subscription (subscription_number will be auto-generated in model.save())
        subscription = Subscription.objects.create(
            user=user,
            subscription_type=subscription_type,
            valid_from=valid_from,
            valid_to=valid_to,
            events_included=subscription_type.max_events,
            events_used=0,
            status='ACTIVE',
        )
        
        messages.success(request, f"Abbonamento {subscription.subscription_number} creato con successo! <a href='/boxoffice/subscriptions/print/{subscription.id}/' target='_blank' class='btn btn-sm btn-primary ml-2'><i class='fas fa-print'></i> Stampa Ricevuta</a>")
        return redirect('subscriptions_main')
    
    # GET request
    from subscriptions.models import SubscriptionType
    subscription_types = SubscriptionType.objects.filter(is_active=True)
    payment_methods = PaymentMethod.objects.all()
    
    context = {
        'subscription_types': subscription_types,
        'payment_methods': payment_methods,
    }
    
    return render(request, 'boxoffice/sell_subscription.html', context)


@login_required(login_url='login')
def verify_subscription(request):
    """
    Pagina di ricerca abbonamento
    """
    return render(request, 'boxoffice/verify_subscription.html')


@login_required(login_url='login')
def search_subscription(request):
    """
    Ricerca abbonamento per codice o cliente
    """
    from subscriptions.models import Subscription
    
    query = request.GET.get('q', '')
    
    if not query:
        return redirect('verify_subscription')
    
    # Search by subscription number or user name/email
    subscriptions = Subscription.objects.filter(
        models.Q(subscription_number__icontains=query) |
        models.Q(user__first_name__icontains=query) |
        models.Q(user__last_name__icontains=query) |
        models.Q(user__email__icontains=query)
    ).select_related('user', 'subscription_type')
    
    context = {
        'query': query,
        'subscriptions': subscriptions,
    }
    
    return render(request, 'boxoffice/search_subscription_results.html', context)


@login_required(login_url='login')
def subscription_detail(request, subscription_id):
    """
    Dettaglio abbonamento con storico utilizzi
    """
    from subscriptions.models import Subscription, SubscriptionUsage
    
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    # Get usage history
    usages = SubscriptionUsage.objects.filter(
        subscription=subscription
    ).select_related('event').order_by('-used_at')
    
    context = {
        'subscription': subscription,
        'usages': usages,
        'remaining': subscription.events_included - subscription.events_used,
    }
    
    return render(request, 'boxoffice/subscription_detail.html', context)


@login_required(login_url='login')
def edit_subscription(request, subscription_id):
    """
    Modifica dati abbonamento (anagrafica cliente, date validità, note)
    """
    from subscriptions.models import Subscription
    
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    if request.method == 'POST':
        # Update customer data
        subscription.user.first_name = request.POST.get('first_name', '').strip()
        subscription.user.last_name = request.POST.get('last_name', '').strip()
        subscription.user.email = request.POST.get('email', '').strip()
        subscription.user.phone_number = request.POST.get('phone_number', '').strip()
        subscription.user.save()
        
        # Update subscription data
        from datetime import datetime
        valid_from_str = request.POST.get('valid_from')
        valid_to_str = request.POST.get('valid_to')
        
        if valid_from_str:
            subscription.valid_from = datetime.strptime(valid_from_str, '%Y-%m-%d').date()
        if valid_to_str:
            subscription.valid_to = datetime.strptime(valid_to_str, '%Y-%m-%d').date()
        
        subscription.notes = request.POST.get('notes', '').strip()
        subscription.status = request.POST.get('status', subscription.status)
        
        subscription.save()
        
        messages.success(request, "Abbonamento aggiornato con successo!")
        return redirect('subscription_detail', subscription_id=subscription.id)
    
    context = {
        'subscription': subscription,
    }
    
    return render(request, 'boxoffice/edit_subscription.html', context)


@login_required(login_url='login')
def add_manual_usage(request, subscription_id):
    """
    Aggiungi utilizzo manuale all'abbonamento
    """
    from subscriptions.models import Subscription, SubscriptionUsage
    from store.models import Event
    
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        seat = request.POST.get('seat', '').strip()
        
        if not event_id or not seat:
            messages.error(request, "Evento e posto sono obbligatori")
            return redirect('subscription_detail', subscription_id=subscription.id)
        
        try:
            event = Event.objects.get(id=event_id)
            
            # Crea utilizzo manuale
            SubscriptionUsage.objects.create(
                subscription=subscription,
                event=event,
                seat=seat,
                used_by=request.user,
                notes="Inserimento manuale"
            )
            
            messages.success(request, f"Utilizzo registrato: {event.show.shw_title} - Posto {seat}")
            
        except Event.DoesNotExist:
            messages.error(request, "Evento non trovato")
        except Exception as e:
            messages.error(request, f"Errore: {str(e)}")
        
        return redirect('subscription_detail', subscription_id=subscription.id)
    
    # GET: mostra form
    from store.models import Event
    from datetime import datetime, timedelta
    
    # Eventi futuri o recenti (ultimi 30 giorni)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    events = Event.objects.filter(date_time__gte=thirty_days_ago).order_by('-date_time')[:50]
    
    context = {
        'subscription': subscription,
        'events': events,
    }
    
    return render(request, 'boxoffice/add_manual_usage.html', context)


@login_required(login_url='login')
def delete_usage(request, usage_id):
    """
    Elimina utilizzo abbonamento
    """
    from subscriptions.models import SubscriptionUsage
    
    usage = get_object_or_404(SubscriptionUsage, id=usage_id)
    subscription_id = usage.subscription.id
    
    if request.method == 'POST':
        # Decrementa contatore prima di eliminare
        subscription = usage.subscription
        if subscription.events_used > 0:
            subscription.events_used -= 1
            # Riattiva se era esaurito
            if subscription.status == 'EXHAUSTED' and subscription.events_used < subscription.events_included:
                subscription.status = 'ACTIVE'
            subscription.save()
        
        usage.delete()
        messages.success(request, "Utilizzo eliminato con successo")
        
    return redirect('subscription_detail', subscription_id=subscription_id)


@login_required(login_url='login')
def print_subscription(request, subscription_id):
    """
    Stampa ricevuta abbonamento
    """
    from subscriptions.models import Subscription
    
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    context = {
        'subscription': subscription,
    }
    
    return render(request, 'boxoffice/print_subscription.html', context)


# ==================== VERIFICA ABBONAMENTO PER VENDITA ====================

@login_required(login_url='login')
def verify_subscription_code_ajax(request):
    """
    Verifica validità codice abbonamento via AJAX
    Returns JSON con info abbonamento o errore
    """
    from django.http import JsonResponse
    from subscriptions.models import Subscription
    
    code = request.GET.get('code', '').strip()
    price_code = int(request.GET.get('price_code', 0))
    
    if not code:
        return JsonResponse({'valid': False, 'error': 'Codice mancante'})
    
    try:
        subscription = Subscription.objects.select_related('user', 'subscription_type').get(
            subscription_number=code,
            status='ACTIVE'
        )
        
        # Verifica validità
        if not subscription.is_valid():
            if subscription.status == 'EXPIRED':
                return JsonResponse({'valid': False, 'error': 'Abbonamento scaduto'})
            elif subscription.status == 'EXHAUSTED':
                return JsonResponse({'valid': False, 'error': 'Abbonamento esaurito'})
            else:
                return JsonResponse({'valid': False, 'error': 'Abbonamento non valido'})
        
        # Verifica corrispondenza tipo
        from subscriptions.utils import PRICE_CODE_TO_SUBSCRIPTION
        expected_prefix = PRICE_CODE_TO_SUBSCRIPTION.get(price_code)
        if expected_prefix and subscription.subscription_type.code_prefix != expected_prefix:
            return JsonResponse({
                'valid': False, 
                'error': f'Codice non corrisponde: questo è {subscription.subscription_type.code_prefix}, selezionato {expected_prefix}'
            })
        
        return JsonResponse({
            'valid': True,
            'customer': f"{subscription.user.first_name} {subscription.user.last_name}",
            'type': subscription.subscription_type.name,
            'remaining': subscription.remaining_events(),
            'code': subscription.subscription_number,
        })
        
    except Subscription.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Abbonamento non trovato'})
    except Exception as e:
        return JsonResponse({'valid': False, 'error': str(e)})


@login_required(login_url='login')
def attach_subscription_to_seat(request, item_id):
    """
    Associa codice abbonamento verificato a SellingSeats
    """
    if request.method == 'POST':
        subscription_code = request.POST.get('subscription_code', '').strip()
        
        try:
            selling_seat = SellingSeats.objects.get(id=item_id)
            selling_seat.subscription_code = subscription_code
            selling_seat.save()
            
            messages.success(request, f"Abbonamento {subscription_code} associato al posto {selling_seat.seat}")
            return redirect('boxoffice_cart', event_id=selling_seat.event.id)
            
        except SellingSeats.DoesNotExist:
            messages.error(request, "Posto non trovato")
            return redirect('boxoffice')
    
    return redirect('boxoffice')


@login_required(login_url='login')
def search_subscriptions_autocomplete(request):
    """
    Autocomplete per ricerca abbonamenti attivi
    Returns JSON con lista abbonamenti che matchano query
    """
    from django.http import JsonResponse
    from subscriptions.models import Subscription
    
    query = request.GET.get('q', '').strip()
    price_code = request.GET.get('price_code', '')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Filtra abbonamenti attivi
    subscriptions = Subscription.objects.filter(
        status='ACTIVE',
        subscription_number__icontains=query
    ).select_related('user', 'subscription_type')
    
    # Filtra per tipo se specificato
    if price_code:
        from subscriptions.utils import PRICE_CODE_TO_SUBSCRIPTION
        expected_prefix = PRICE_CODE_TO_SUBSCRIPTION.get(int(price_code))
        if expected_prefix:
            subscriptions = subscriptions.filter(subscription_type__code_prefix=expected_prefix)
    
    # Limita risultati
    subscriptions = subscriptions[:10]
    
    results = []
    for sub in subscriptions:
        if sub.is_valid():
            results.append({
                'code': sub.subscription_number,
                'label': f"{sub.subscription_number} - {sub.user.first_name} {sub.user.last_name} ({sub.remaining_events()} ingressi)",
                'customer': f"{sub.user.first_name} {sub.user.last_name}",
                'remaining': sub.remaining_events(),
                'type': sub.subscription_type.name,
            })
    
    return JsonResponse({'results': results})


@login_required(login_url='login')
def export_subscriptions_excel(request):
    """
    Esporta tutti gli abbonamenti in formato Excel con dettaglio utilizzi
    """
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from django.http import HttpResponse
    from subscriptions.models import Subscription, SubscriptionUsage
    from datetime import datetime
    
    # Crea workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Abbonamenti"
    
    # Header styling
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    # Headers base
    headers = [
        'Codice Abbonamento',
        'Cliente',
        'Email',
        'Telefono',
        'Tipo Abbonamento',
        'Prezzo',
        'Ingressi Inclusi',
        'Ingressi Usati',
        'Ingressi Rimanenti',
        'Valido Dal',
        'Valido Fino',
        'Stato',
        'Data Acquisto',
    ]
    
    # Aggiungi headers per utilizzi (massimo 8 utilizzi per abbonamento)
    max_usages = 8
    for i in range(1, max_usages + 1):
        headers.extend([
            f'Utilizzo {i} - Data',
            f'Utilizzo {i} - Evento',
            f'Utilizzo {i} - Posto',
        ])
    
    # Scrivi headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
    
    # Get all subscriptions con utilizzi
    subscriptions = Subscription.objects.select_related('user', 'subscription_type').prefetch_related('usages__event').order_by('-created_at')
    
    # Status mapping
    status_map = {
        'ACTIVE': 'Attivo',
        'EXPIRED': 'Scaduto',
        'EXHAUSTED': 'Esaurito',
        'CANCELLED': 'Annullato',
    }
    
    # Data rows
    for row_num, sub in enumerate(subscriptions, 2):
        col = 1
        
        # Dati base abbonamento
        ws.cell(row=row_num, column=col).value = sub.subscription_number
        col += 1
        ws.cell(row=row_num, column=col).value = f"{sub.user.first_name} {sub.user.last_name}"
        col += 1
        ws.cell(row=row_num, column=col).value = sub.user.email
        col += 1
        ws.cell(row=row_num, column=col).value = sub.user.phone_number or ''
        col += 1
        ws.cell(row=row_num, column=col).value = sub.subscription_type.name
        col += 1
        ws.cell(row=row_num, column=col).value = float(sub.subscription_type.price)
        col += 1
        ws.cell(row=row_num, column=col).value = sub.events_included
        col += 1
        ws.cell(row=row_num, column=col).value = sub.events_used
        col += 1
        ws.cell(row=row_num, column=col).value = sub.events_included - sub.events_used
        col += 1
        ws.cell(row=row_num, column=col).value = sub.valid_from.strftime('%d/%m/%Y')
        col += 1
        ws.cell(row=row_num, column=col).value = sub.valid_to.strftime('%d/%m/%Y')
        col += 1
        ws.cell(row=row_num, column=col).value = status_map.get(sub.status, sub.status)
        col += 1
        ws.cell(row=row_num, column=col).value = sub.created_at.strftime('%d/%m/%Y %H:%M')
        col += 1
        
        # Utilizzi dell'abbonamento
        usages = sub.usages.all().order_by('used_at')
        for usage in usages[:max_usages]:  # Limita a max_usages
            ws.cell(row=row_num, column=col).value = usage.used_at.strftime('%d/%m/%Y %H:%M')
            col += 1
            ws.cell(row=row_num, column=col).value = usage.event.show.shw_title if usage.event and usage.event.show else ''
            col += 1
            ws.cell(row=row_num, column=col).value = usage.seat
            col += 1
    
    # Auto-adjust column widths per le prime 13 colonne
    for i in range(1, 14):
        column = ws[openpyxl.utils.get_column_letter(i)]
        max_length = 0
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = adjusted_width
    
    # Larghezza fissa per colonne utilizzi
    for i in range(14, len(headers) + 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = 15
    
    # Prepare response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"abbonamenti_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response


