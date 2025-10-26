from django.shortcuts import render, redirect
from django.contrib import messages
from rest_framework import viewsets
from .models import MenuItems, Users
from .serializers import MenuItemsSerializer
from django.contrib.auth.hashers import check_password  # optional if passwords are hashed

# DRF ViewSet for MenuItems
class MenuItemsViewSet(viewsets.ModelViewSet):
    queryset = MenuItems.objects.all()
    serializer_class = MenuItemsSerializer  


def home(request):
    """
    Render the public homepage.
    Pass 'user' from session if exists for profile display.
    """
    user_id = request.session.get('user_id')
    user = None

    if user_id:
        try:
            user = Users.objects.get(user_id=user_id)
        except Users.DoesNotExist:
            request.session.flush()

    return render(request, 'restaurant/index.html', {'user': user})


def dashboard(request):
    """
    Render the logged-in user's homepage (dashboard).
    Only accessible if user is logged in.
    """
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('restaurant:login')  # redirect if not logged in

    try:
        user = Users.objects.get(user_id=user_id)
    except Users.DoesNotExist:
        request.session.flush()
        return redirect('restaurant:login')

    return render(request, 'restaurant/index_logged_in.html', {'user': user})


def login_view(request):
    """
    Handle login requests.
    Checks email, password, and role.
    Redirects to dashboard after successful login.
    """
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")  # 'user' or 'admin'

        try:
            user = Users.objects.get(email=email, role=role)

            # Plain-text password check (not recommended)
            if user.password == password:
                request.session['user_id'] = user.user_id
                request.session['role'] = user.role
                return redirect('restaurant:dashboard')  # redirect to logged-in homepage

            # Hashed password check (recommended)
            # if check_password(password, user.password):
            #     request.session['user_id'] = user.user_id
            #     request.session['role'] = user.role
            #     return redirect('restaurant:dashboard')

            messages.error(request, "Invalid password")
        except Users.DoesNotExist:
            messages.error(request, "Invalid email or role")

    return render(request, 'restaurant/login.html')
