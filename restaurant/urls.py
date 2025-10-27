from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MenuItemsViewSet, 
    home, 
    login_view, 
    dashboard, 
    menu_page,
    cart_page,
    cart_api,
    place_order_api,
    add_to_cart_api,
    logout_view
)

app_name = 'restaurant'

# DRF router for menu items
router = DefaultRouter()
router.register(r'menu', MenuItemsViewSet, basename='menu')

urlpatterns = [
    # Web pages
    path('', home, name='home'),                  # Home page
    path('login/', login_view, name='login'),     # Login / Sign Up page
    path('logout/', logout_view, name='logout'),  # Logout
    path('dashboard/', dashboard, name='dashboard'),
    path('menu/', menu_page, name='menu'),
    path('cart/', cart_page, name='cart'),

    # API endpoints
    path('api/', include(router.urls)),              # DRF Menu API
    path('api/cart/', cart_api, name='cart_api'),    # GET cart items
    path('api/cart/add/', add_to_cart_api, name='add_to_cart'),  # POST add item to cart
    path('api/orders/', place_order_api, name='place_order')     # POST new order
]
