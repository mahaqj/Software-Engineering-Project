from django.contrib import admin
from .models import User, WarehouseManager, RestaurantManager, Batch, Item, Order, OrderItem, Payment

# Register your models here.

#to view models in the Django admin panel, register them
admin.site.register(User)
admin.site.register(WarehouseManager)
admin.site.register(RestaurantManager)
admin.site.register(Batch)
admin.site.register(Item)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
