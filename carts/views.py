from django.shortcuts import render, redirect
from django.http import HttpResponse
from store.models import Event
from .models import Cart, CartItem

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



def cart(request):

    active_cart_id = request.session['active_cart_id']
    cart = Cart.objects.get(cart_id=active_cart_id)
    cart_items = CartItem.objects.filter(cart=cart)

    context = {
        'cart': cart,
        'cart_items': cart_items,
    }


    return render(request, 'store/cart.html', context)