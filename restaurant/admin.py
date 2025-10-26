from django.contrib import admin
from .models import Users, MenuItems, Orders, OrderItems, Payments, Deliveries, Feedback

admin.site.register(Users)
admin.site.register(MenuItems)
admin.site.register(Orders)
admin.site.register(OrderItems)
admin.site.register(Payments)
admin.site.register(Deliveries)
admin.site.register(Feedback)
