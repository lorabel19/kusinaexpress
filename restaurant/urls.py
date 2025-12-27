from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    MenuItemsViewSet, 
    home, 
    login_view, 
    create_account,
    dashboard, 
    menu_page,
    cart_page,
    cart_api,
    add_to_cart_api,
    remove_from_cart_api,
    place_order_api,
    order_view,
    track_order_api,
    user_logout_view,
    admin_logout_view,
    profile_view,
    about,
    contact_page,
    menu,
    submit_feedback,
    admin_dashboard,
    admin_menu,
    admin_add_menu,
    admin_edit_menu,
    admin_delete_menu,
    admin_orders,
    confirm_order,
    admin_update_orders,
    admin_feedback,
    mark_order_seen
)

app_name = 'restaurant'

# DRF router for menu items API
router = DefaultRouter()
router.register(r'menu', MenuItemsViewSet, basename='menu')

# URL Patterns
urlpatterns = [
    # --- Public Pages ---
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('create-account/', create_account, name='create_account'),
    path('public-menu/', menu, name='public_menu'),
    
    # --- User Pages (Require Login) ---
    path('dashboard/', dashboard, name='dashboard'),
    path('logout/', user_logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('menu/', menu_page, name='menu'),
    path('cart/', cart_page, name='cart'),
    path('order/', order_view, name='order'),
    path('contact/', contact_page, name='contact'),
    path('about/', about, name='about'),
    
    # --- Admin Pages (Require Admin Login) ---
    path('admin-dashboard/', admin_dashboard, name='admin-dashboard'),
    path('admin-logout/', admin_logout_view, name='admin-logout'),
    path('admin-menu/', admin_menu, name='admin-menu'),
    path('admin-menu/add/', admin_add_menu, name='admin-add-menu'),
    path('admin-menu/edit/<int:item_id>/', admin_edit_menu, name='admin-edit-menu'),
    path('admin-menu/delete/<int:item_id>/', admin_delete_menu, name='admin-delete-menu'),
    path('admin-orders/', admin_orders, name='admin-orders'),
    path('admin-orders/confirm/<int:order_id>/', confirm_order, name='admin-confirm-order'),
    path('admin-orders/update/<int:order_id>/', admin_update_orders, name='admin-update-order-status'),
    path('admin-feedback/', admin_feedback, name='admin-feedback'),
    path('admin-users/', views.manage_users, name='admin-users'),
    path('admin-add-admin/', views.add_admin, name='add-admin'),
    path('admin-edit-admin/', views.edit_admin, name='edit-admin'),
    path('admin-delete-admin/', views.delete_admin, name='delete-admin'),
    path('admin-settings/', views.admin_settings, name='admin-settings'),
    
    # --- API Endpoints ---
    path('api/', include(router.urls)),  # DRF Menu API
    
    # Cart API
    path('api/cart/', cart_api, name='cart_api'),
    path('api/cart/add/', add_to_cart_api, name='add_to_cart_api'),
    path('api/cart/remove/<int:cart_id>/', remove_from_cart_api, name='remove_from_cart_api'),
    
    # Order API
    path('api/orders/', place_order_api, name='place_order_api'),
    path('api/orders/<int:order_id>/', track_order_api, name='track_order_api'),
    path('api/orders/<int:order_id>/mark_seen/', mark_order_seen, name='mark_order_seen'),
    
    # Feedback API
    path('api/feedback/', submit_feedback, name='api-feedback'),
    path('submit-feedback/', views.submit_feedback_form, name='submit-feedback'),
    
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
]