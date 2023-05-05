from .models import Cart, CartItem
from .views import _cart_id

def counter(request):
    cart_count: int = 0
    if 'admin' in request.path:
        return {}
    else:
        try:
            cart = Cart.objects.filter(cart_id=_cart_id(request))
            cart_items = CartItem.objects.all().filter(cart=cart[:1])
            cart_count = cart_items.count()
        except (Cart.DoesNotExist, CartItem.DoesNotExist) as e:
            cart_count = 0
    return dict(cart_count=cart_count)
