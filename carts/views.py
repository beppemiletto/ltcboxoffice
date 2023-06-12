from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from store.models import Event
from orders.models import Order
from accounts.models import UserProfile
from .models import Cart, CartItem
import os, json

# Create your views here.
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, event_id):
    event = Event.objects.get(id=event_id)
    if request.method == 'POST':
        selected_seats=[]
        selected_seats_str = request.POST['selected_seats']
        if len(selected_seats_str):
            selected_seats = selected_seats_str.strip().split(',')
            # update json file 
            json_file_path= os.path.abspath(event.get_json_path())
            with open(json_file_path,'r') as jfp:
                hall_status = json.load(jfp)
            try:
                for k, seat in hall_status.items():
                    if seat['status']== 3:
                        seat['status'] = 0
                for seat in selected_seats:
                    hall_status[seat]['status'] = 4 
                with open(json_file_path,'w') as jfp:
                    json.dump(hall_status,jfp)
            except:
                print('Something wrong!')
        # return HttpResponse("The method is POST and we got {} as selected seats".format(all_data))
    
    if len(selected_seats):
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request)) # get the cart using the cart_id present in the session
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id = _cart_id(request)
            )
            cart.save()
        for seat in selected_seats:
            try:
                cart_item = CartItem.objects.get(event=event, cart=cart, seat=seat)
            except CartItem.DoesNotExist:
                cart_item = CartItem.objects.create(
                    event = event,
                    cart = cart,
                    seat = seat,
                    ingresso = 1,
                    price = event.price_full,
                    
                    
                )
                if request.user.is_authenticated:
                    cart_item.user=request.user
                    
                cart_item.save()
    else:
        return HttpResponse("<H1>Nessun posto selezionato message error</H1><br><a href='/'>Torna al cartellone</a>")
    
    request.session['active_cart_id'] = cart.cart_id

    return redirect('cart')

def remove_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    seat = item.seat
    event = item.event
    item.delete()
    json_file_path= os.path.abspath(event.get_json_path())
    with open(json_file_path,'r') as jfp:
        hall_status = json.load(jfp)
    try:
        if hall_status[seat]['status'] == 3:
            hall_status[seat]['status'] = 0 
            with open(json_file_path,'w') as jfp:
                json.dump(hall_status,jfp)
    except:
        print('Something wrong!')
    return redirect('cart')


def plus_ingresso(request, item_id = None):
    item = CartItem.objects.get(id=item_id)
    ingresso_old = item.ingresso
    if ingresso_old < 2:
        ingresso_new = ingresso_old + 1
    else:
        ingresso_new = 2
    item.ingresso = ingresso_new
    if ingresso_new == 0:
        item.price = 0.0
    elif ingresso_new == 1:
        item.price = item.event.price_full
    elif ingresso_new == 2:
        item.price = item.event.price_reduced

    item.save()

    # return HttpResponse('<H1>CartItem number {} move ingresso from {} to {}</H1>'.format(item_id, ingresso_old, ingresso_new))
    return redirect('cart')


def minus_ingresso(request, item_id = None):
    item = CartItem.objects.get(id=item_id)
    ingresso_old = item.ingresso
    if ingresso_old > 0:
        ingresso_new = ingresso_old - 1
    else:
        ingresso_new = 0
    item.ingresso = ingresso_new
    if ingresso_new == 0:
        item.price = 0.0
    elif ingresso_new == 1:
        item.price = item.event.price_full
    elif ingresso_new == 2:
        item.price = item.event.price_reduced
    item.save()

    # return HttpResponse('<H1>CartItem number {} move ingresso from {} to {}</H1>'.format(item_id, ingresso_old, ingresso_new))
    return redirect('cart')

def cart(request, total=0, cart_items=None):
    prices=[]
    vat_rate = 0.0
    try: 
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
            if cart_items:
                cart = cart_items[0].cart
            else:
                cart = None

        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        # active_cart_id = request.session['active_cart_id']
        # cart = Cart.objects.get(cart_id=active_cart_id)
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for item in cart_items:
            vat_rate = item.event.vat_rate
            prices = [0.00, item.event.price_full, item.event.price_reduced]
            total += (prices[item.ingresso])
        taxable = int(total / (1 + vat_rate / 100) *100)/100
        tax = int((total - taxable) *100)/100

        context = {
            'cart': cart,
            'cart_items': cart_items,
            'total': total,
            'taxable': taxable,
            'tax': tax,
            'vat_rate': vat_rate,
            'prices': prices,
        }
    except ObjectDoesNotExist:
        context = {}

    return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request, total=0, cart_items=None):
    taxable = 0.0
    tax = 0.0
    vat_rate = 10 # % IVA
    try: 
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
            if cart_items:
                cart = cart_items[0].cart
            else:
                cart = None

        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for item in cart_items:
            vat_rate = item.event.vat_rate
            total += item.price
            taxable += int(item.price / (1 + vat_rate / 100) *100)/100
        
        tax = int((total - taxable) *100)/100

        current_user = request.user
        try:
            former_order = Order.objects.filter(user=current_user).order_by('-created_at').first()
            user_data = {
            'user': current_user,
            'first_name': former_order.first_name,
            'last_name': former_order.last_name,
            'phone': former_order.phone,
            'email': former_order.email,
            'address_line_1': former_order.address_line_1,
            'address_line_2': former_order.address_line_2,
            'post_code': former_order.post_code,
            'city': former_order.city,
            'province': former_order.province,
            'order_note': former_order.order_note,
            }

        except:
            userprofile = UserProfile.objects.get(user=current_user)

            user_data = {
            'user': current_user,
            'first_name': userprofile.user.first_name,
            'last_name': userprofile.user.last_name,
            'phone': userprofile.user.phone_number,
            'email': userprofile.user.email,
            'address_line_1': userprofile.address_line1,
            'address_line_2': userprofile.address_line2,
            'post_code': userprofile.post_code,
            'city': userprofile.city,
            'province': userprofile.province,
            'order_note': '',

            }



        context = {
            'user_data': user_data,
            'cart': cart,
            'cart_items': cart_items,
            'total': total,
            'taxable': taxable,
            'tax': tax,
            'vat_rate': vat_rate,
        }
    except ObjectDoesNotExist:
        context = {}
    return render(request, 'store/checkout.html', context)
