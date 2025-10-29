from django.contrib import admin
from .models import Users, MenuItems, Orders, Cart, Payments, Deliveries, Feedback

admin.site.register(Users)
admin.site.register(MenuItems)
admin.site.register(Orders)
admin.site.register(Cart)
admin.site.register(Payments)
admin.site.register(Deliveries)
admin.site.register(Feedback)
