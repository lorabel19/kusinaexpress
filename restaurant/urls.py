from django.urls import path, include
from rest_framework.routers import DefaultRouter
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
    order_view,
    track_order_api,
)

app_name = 'restaurant'

# DRF router for menu items API
router = DefaultRouter()
router.register(r'menu', MenuItemsViewSet, basename='menu')

# URL Patterns
urlpatterns = [
    # --- Pages ---
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('menu/', menu_page, name='menu'),
    path('cart/', cart_page, name='cart'),
    path('order/', order_view, name='order'),
    path('contact/', views.contact_page, name='contact'),
    path('about/', views.about, name='about'),
    path('profile/', views.profile_view, name='profile'),
    path('public-menu/', views.menu, name='public_menu'),

    # --- Admin Pages ---
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('admin-menu/', views.admin_menu, name='admin-menu'),
    path('admin-menu/add/', views.admin_add_menu, name='admin-add-menu'),
    path('admin-menu/edit/<int:item_id>/', views.admin_edit_menu, name='admin-edit-menu'),
    path('admin-menu/delete/<int:item_id>/', views.admin_delete_menu, name='admin-delete-menu'),
    path('admin-orders/', views.admin_orders, name='admin-orders'),
    path('admin-orders/confirm/<int:order_id>/', views.confirm_order, name='admin-confirm-order'),
    path('admin-orders/update/<int:order_id>/', views.admin_update_orders, name='admin-update-order-status'),
    path('admin-feedback/', views.admin_feedback, name='admin-feedback'),
    

    # --- API Endpoints ---
    path('api/', include(router.urls)),                       # DRF Menu API
    path('api/cart/', cart_api, name='cart_api'),
    path('api/cart/add/', add_to_cart_api, name='add_to_cart_api'),
    path('api/orders/', place_order_api, name='place_order_api'),
    path('api/orders/<int:order_id>/', track_order_api, name='track_order_api'),
    path('api/orders/<int:order_id>/mark_seen/', views.mark_order_seen, name='mark_order_seen'),

    # --- Feedback API ---
    path('api/feedback/', views.submit_feedback, name='api-feedback'),  # New API for user feedback
]
