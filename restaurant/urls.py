from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContactMessageListCreateAPIView
from . import views
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
    logout_view,
    order_view,        # <-- added
    track_order_api    # <-- added
)

app_name = 'restaurant'

# DRF router for menu items API
router = DefaultRouter()
router.register(r'menu', MenuItemsViewSet, basename='menu')

# URL Patterns
urlpatterns = [
    path('', home, name='home'),                      # Home page
    path('login/', login_view, name='login'),         # Login / Sign Up page
    path('logout/', logout_view, name='logout'),      # Logout
    path('dashboard/', dashboard, name='dashboard'),  # Logged-in dashboard
    path('menu/', menu_page, name='menu'),            # Menu page
    path('cart/', cart_page, name='cart'),            # Cart page
    path('order/', order_view, name='order'),         # Order pageS
    path('contact/', views.contact_page, name='contact'), #Contact Page
    path('about/', views.about, name='about'),          #About Page
    path('profile/', views.profile_view, name='profile'),
    path('public-menu/', views.menu, name='public_menu'),  # public menu page
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('admin-menu/', views.admin_menu, name='admin-menu'),
    path('admin-menu/add/', views.admin_add_menu, name='admin-add-menu'),
    path('admin-menu/edit/<int:item_id>/', views.admin_edit_menu, name='admin-edit-menu'),
    path('admin-menu/delete/<int:item_id>/', views.admin_delete_menu, name='admin-delete-menu'),
    path('admin-orders/', views.admin_orders, name='admin-orders'),
    path('admin-orders/confirm/<int:order_id>/', views.confirm_order, name='admin-confirm-order'),
    path('admin-orders/update/<int:order_id>/', views.admin_update_orders, name='admin-update-order-status'),

    

    # API Endpoints
    path('api/', include(router.urls)),                       # DRF Menu API
    path('api/cart/', cart_api, name='cart_api'),             # GET cart items
    path('api/cart/add/', add_to_cart_api, name='add_to_cart_api'),  # POST add to cart
    path('api/orders/', place_order_api, name='place_order_api'),     # POST place order
    path('api/orders/<int:order_id>/', track_order_api, name='track_order_api'),  # Track order API
    path('api/contact/', ContactMessageListCreateAPIView.as_view(), name='api-contact'),
]
