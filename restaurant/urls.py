from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MenuItemsViewSet, home, login_view, dashboard  # added dashboard

app_name = 'restaurant'  # important for namespacing

# API router
router = DefaultRouter()
router.register(r'menu', MenuItemsViewSet)

urlpatterns = [
    # Web pages
    path('', home, name='home'),  # public homepage
    path('login/', login_view, name='login'),
    path('dashboard/', dashboard, name='dashboard'),  # logged-in homepage

    # API endpoints
    path('api/', include(router.urls)),
]
