from .models import Cart, CartItem
from .views import _cart_id

def counter(request):
    cart_count: int = 0
    if 'admin' in request.path:
        return {}
    else:
        try:
            cart = Cart.objects.filter(cart_id=_cart_id(request))
            if request.user.is_authenticated:
                cart_items = CartItem.objects.filter(user=request.user)
            else:
                cart_items = CartItem.objects.all().filter(cart=cart[:1])
            cart_count = cart_items.count()
        except (Cart.DoesNotExist, CartItem.DoesNotExist) as e:
            cart_count = 0
    return dict(cart_count=cart_count)
