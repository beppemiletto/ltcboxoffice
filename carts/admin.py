from django.contrib import admin
from .models import CartItem, Cart

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart_item_extended_name', 'ingresso', 'is_active') 

# Register your models here.
admin.site.register(Cart)
admin.site.register(CartItem, CartItemAdmin)
