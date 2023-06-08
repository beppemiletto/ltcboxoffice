from django.shortcuts import render, redirect
from django.http import HttpResponse , JsonResponse
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from carts.models import CartItem
from .models import Order, Payment, OrderEvent
from store.models import Event
from .forms import OrderForm
import datetime
import json
import os

def round_euro(the_float):
    return int(the_float * 100 + 0.5) / 100


def payments(request):
    current_user = request.user
    body = json.loads(request.body)
    print(body)
    order = Order.objects.get(user=current_user, is_ordered=False, order_number= body['orderID'])
    payment = Payment(
        user=current_user,
        payment_id=body['transID'],
        payment_method=body['payment_method'],
        amount_paid=order.order_total,
        status=body['status'],
        # payer_id=body['payer']['payer_id'],
        # payer_mail=body['payer']['email_address'],
        # payer_surname=body['payer']['name']['surname'],
        # payer_given_name=body['payer']['name']['given_name'],
        )
    payment.save()
    order.payment = payment
    order.is_ordered = True
    order.save()

    # Move the cart items to the Order Product table and modifiy the Hall Status Json file of event
    # Reduce the quantity of sold products
    cart_items = CartItem.objects.filter(user=request.user).order_by('event')
    for item in cart_items:
        seat= item.seat
        event = item.event
        json_filename_fullpath = event.get_json_path()
        if os.path.exists(json_filename_fullpath):
            with open(json_filename_fullpath,'r') as fp:
                event_hall = json.load(fp)
            event_hall[seat]['status'] = 5  # set status to Sold 
            with open(json_filename_fullpath,'w') as fp:
                json.dump(event_hall,fp,indent=4, separators=(',', ': '))
        else:
            print('Problems with {} file doesnt exist!'.format(json_filename_fullpath))
        try:
            orderevent = OrderEvent.objects.get(user=current_user, event=event)
            items = orderevent.seats_price
            items += ',{}${}'.format(seat, item.ingresso)
            orderevent.seats_price = items
            orderevent.save()
        except:
            orderevent = OrderEvent()
            orderevent.order = order
            orderevent.payment = payment
            orderevent.event = event
            orderevent.user = current_user
            items = '{}${}'.format(seat, item.ingresso)
            orderevent.seats_price = items
            orderevent.save()




 
    # Clear the cart

    CartItem.objects.filter(user=current_user).delete()

    # Send order received email to customer

    current_site = get_current_site(request)
    mail_subject = 'Grazie per il tuo ordine!'
    email_context = {
        'user': request.user,
        'order': order,
    }
    message = render_to_string('orders/order_received_email.html', email_context, request)
    to_email = current_user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    # Send order number and transaction id back to sendData method via JsonResponse

    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,

    }

    return JsonResponse(data)



def place_order(request):
    current_user = request.user

    # If the cart count is less or equal to zero
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')
    
    grand_total = 0
    grouped_cart_items = {}
    for item in cart_items:
        vat_rate = item.event.vat_rate
        price = round_euro(item.price)
        taxable = round_euro(price / (1 + vat_rate / 100))
        tax = round_euro(price - taxable) 
        if item.event.event_slug in grouped_cart_items:
            grouped_cart_items[item.event.event_slug]['count'] += 1
            grouped_cart_items[item.event.event_slug]['price_tot'] += price
            grouped_cart_items[item.event.event_slug]['taxable_tot'] += taxable
            grouped_cart_items[item.event.event_slug]['tax_tot'] += tax
            grouped_cart_items[item.event.event_slug]['seat'] += ', '+item.seat

        else:
            grouped_cart_items[item.event.event_slug]= {}
            grouped_cart_items[item.event.event_slug]['count'] = 1
            grouped_cart_items[item.event.event_slug]['price_tot'] = price
            grouped_cart_items[item.event.event_slug]['taxable_tot'] = taxable
            grouped_cart_items[item.event.event_slug]['tax_tot'] = tax
            grouped_cart_items[item.event.event_slug]['seat'] = item.seat
            grouped_cart_items[item.event.event_slug]['event'] = item.event

    taxable = 0.0
    tax = 0.0

    for k, item in grouped_cart_items.items():
        grand_total += item['price_tot']
        taxable += item['taxable_tot']
        tax += item['tax_tot'] 

    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Store all the billing information inside Order Table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.post_code = form.cleaned_data['post_code']
            data.city = form.cleaned_data['city']
            data.province = form.cleaned_data['province']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save() 

            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt, dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)

            context = {
                'order': order,
                'cart_items': cart_items,
                'total': taxable,
                'grand_total': grand_total,
                'tax': tax,
                'cart_count': cart_count,
                'grouped_cart_items' : grouped_cart_items,
            }

            # return HttpResponse('Ok the form is valid and I saved the Order Record')
            return render(request, 'orders/payments.html', context)
        else:
            return HttpResponse("<H1>Entered the POST clause</H1><br>Got the following form that is NOT VALID <br> {}".format(form))

    else:
        return redirect('checkout')
    
def order_complete(request):
    return

