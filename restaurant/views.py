from django.shortcuts import render, redirect
from django.contrib import messages
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import MenuItems, Users, Orders, Cart
from .serializers import MenuItemsSerializer, CartSerializer, OrdersSerializer
from decimal import Decimal  # ✅ added for subtotal calculation precision

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
    items = MenuItems.objects.filter(is_available=1)
    return render(request, 'restaurant/menu.html', {'user': user, 'menu_items': items})

def cart_page(request):
    """Render cart page."""
    user = get_logged_in_user(request)
    if not user:
        return redirect('restaurant:login')

    # ✅ Updated to fetch and show cart items
    cart_items = Cart.objects.filter(user=user)
    total = sum(item.subtotal for item in cart_items)
    return render(request, 'restaurant/cart.html', {'user': user, 'cart_items': cart_items, 'total': total})

# -----------------------------
# Cart APIs
# -----------------------------
@api_view(['GET'])
def cart_api(request):
    """Return current user's cart items."""
    user = get_logged_in_user(request)
    if not user:
        return Response({"detail": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    items = Cart.objects.filter(user=user)
    serializer = CartSerializer(items, many=True)
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
        menu_item = MenuItems.objects.get(item_id=item_id)

        # ✅ Ensure existing cart item is properly handled
        cart_item, created = Cart.objects.get_or_create(user=user, item=menu_item)

        if created:
            cart_item.quantity = quantity
        else:
            cart_item.quantity = (cart_item.quantity or 0) + quantity  # handles null quantity safely

        # ✅ Always compute subtotal properly
        cart_item.subtotal = Decimal(menu_item.price) * Decimal(cart_item.quantity)
        cart_item.save()

        # ✅ Return flattened fields including image_url for frontend
        return Response({
            "detail": f"'{menu_item.name}' added to cart.",
            "cart_id": cart_item.cart_id,
            "item_id": menu_item.item_id,
            "name": menu_item.name,
            "price": str(menu_item.price),
            "quantity": cart_item.quantity,
            "subtotal": str(cart_item.subtotal),
            "image_url": menu_item.image_url
        }, status=status.HTTP_200_OK)

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
    # Create or get pending order for this user
    order, _ = Orders.objects.get_or_create(user=user, status='pending')

    cart_items = Cart.objects.filter(user=user)
    if not cart_items.exists():
        return Response({"detail": "No items in cart"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        order.total_amount = sum([ci.subtotal for ci in cart_items]) + Decimal('40.00')  # ✅ added Decimal for precision
        order.status = 'confirmed'
        order.save()

        # Optionally, clear cart after placing order
        cart_items.delete()

        return Response({"detail": "Order placed successfully"})
    except Exception as e:
        return Response({"detail": f"Error placing order: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
