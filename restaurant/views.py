from django.shortcuts import render, redirect
from django.contrib import messages
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import MenuItems, Users, Orders, OrderItems
from .serializers import MenuItemsSerializer, OrderItemsSerializer, OrdersSerializer

# -----------------------------
# Menu Items API
# -----------------------------
class MenuItemsViewSet(viewsets.ModelViewSet):
    queryset = MenuItems.objects.all()
    serializer_class = MenuItemsSerializer

# -----------------------------
# Helper: Get logged-in user
# -----------------------------
def get_logged_in_user(request):
    """Return currently logged-in user, or None if not logged in."""
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        return Users.objects.get(user_id=user_id)
    except Users.DoesNotExist:
        request.session.flush()
        return None

# -----------------------------
# Pages
# -----------------------------
def home(request):
    """Render home page."""
    user = get_logged_in_user(request)
    return render(request, 'restaurant/index.html', {'user': user})

def dashboard(request):
    """Render dashboard for logged-in users."""
    user = get_logged_in_user(request)
    if not user:
        return redirect('restaurant:login')
    return render(request, 'restaurant/index_logged_in.html', {'user': user})

def login_view(request):
    """Login / Sign Up page handling."""
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        try:
            user = Users.objects.get(email=email, role=role)
            if user.password == password:  # plaintext check
                request.session['user_id'] = user.user_id
                request.session['role'] = user.role
                return redirect('restaurant:dashboard')
            else:
                messages.error(request, "Invalid password")
        except Users.DoesNotExist:
            messages.error(request, "Invalid email or role")

    return render(request, 'restaurant/login.html')

def logout_view(request):
    """Log out the user."""
    request.session.flush()
    return redirect('restaurant:login')

def menu_page(request):
    """Render menu page."""
    user = get_logged_in_user(request)
    return render(request, 'restaurant/menu.html', {'user': user})

def cart_page(request):
    """Render cart page."""
    user = get_logged_in_user(request)
    if not user:
        return redirect('restaurant:login')
    return render(request, 'restaurant/cart.html', {'user': user})

# -----------------------------
# Cart APIs
# -----------------------------
@api_view(['GET'])
def cart_api(request):
    """Return current user's cart items."""
    user = get_logged_in_user(request)
    if not user:
        return Response({"detail": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    order = Orders.objects.filter(user_id=user.user_id, status='pending').first()
    if not order:
        return Response([])

    items = OrderItems.objects.filter(order=order)
    serializer = OrderItemsSerializer(items, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def add_to_cart_api(request):
    """Add a menu item to the cart or update quantity."""
    user = get_logged_in_user(request)
    if not user:
        return Response({"detail": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    item_id = request.data.get('item_id')
    quantity = int(request.data.get('quantity', 1))

    if not item_id:
        return Response({"detail": "Item ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        menu_item = MenuItems.objects.get(id=item_id)
        order, _ = Orders.objects.get_or_create(user_id=user.user_id, status='pending')
        order_item, created = OrderItems.objects.get_or_create(order=order, item=menu_item)
        if not created:
            order_item.quantity += quantity
        else:
            order_item.quantity = quantity
        order_item.subtotal = menu_item.price * order_item.quantity
        order_item.save()
        return Response({"detail": "Item added to cart"})
    except MenuItems.DoesNotExist:
        return Response({"detail": "Menu item not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"detail": f"Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def place_order_api(request):
    """Confirm and place the current order."""
    user = get_logged_in_user(request)
    if not user:
        return Response({"detail": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    data = request.data
    order = Orders.objects.filter(user_id=user.user_id, status='pending').first()
    if not order:
        return Response({"detail": "No items in cart"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        order.delivery_address = data.get('address', '')
        order.contact_number = data.get('contact', '')
        order.delivery_option = data.get('delivery_option', 'pickup')
        order.notes = data.get('notes', '')
        order.payment_method = data.get('payment_method', 'cash')
        order.total = sum([oi.subtotal for oi in order.orderitems_set.all()]) + 40  # delivery fee
        order.status = 'confirmed'
        order.save()
        return Response({"detail": "Order placed successfully"})
    except Exception as e:
        return Response({"detail": f"Error placing order: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
