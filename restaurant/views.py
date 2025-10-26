from django.http import HttpResponse
from rest_framework import viewsets
from .models import MenuItems
from .serializers import MenuItemsSerializer

class MenuItemsViewSet(viewsets.ModelViewSet):
    queryset = MenuItems.objects.all()
    serializer_class = MenuItemsSerializer

def home(request):
    return HttpResponse("<h1>Welcome to Kusina Express </h1>")
