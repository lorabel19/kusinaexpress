from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MenuItemsViewSet

router = DefaultRouter()
router.register(r'menu', MenuItemsViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
