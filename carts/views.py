from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from store.models import Event
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
                    hall_status[seat]['status'] = 3 
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
                )
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
    item.save()

    # return HttpResponse('<H1>CartItem number {} move ingresso from {} to {}</H1>'.format(item_id, ingresso_old, ingresso_new))
    return redirect('cart')

def cart(request, total=0, cart_items=None):
    vat_rate = 10 # % IVA
    prices=[]
    try: 
        cart = Cart.objects.get(cart_id=_cart_id(request))
        # active_cart_id = request.session['active_cart_id']
        # cart = Cart.objects.get(cart_id=active_cart_id)
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for item in cart_items:
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
