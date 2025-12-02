from django.shortcuts import render, redirect
from django.contrib import messages
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import MenuItems, Users, Orders, Cart
from .serializers import MenuItemsSerializer, CartSerializer, OrdersSerializer
from decimal import Decimal  
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Orders, Users
import json
from decimal import Decimal
from django.utils import timezone



# Menu Items API
class MenuItemsViewSet(viewsets.ModelViewSet):
    queryset = MenuItems.objects.all()
    serializer_class = MenuItemsSerializer


# Helper: Get logged-in user
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

# Pages
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

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Users

def login_view(request):
    """Login page handling for all users, redirecting admins to admin dashboard."""
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        try:
            user = Users.objects.get(email=email, role=role)
            
            if user.password == password:  # plaintext check
                # Store user info in session
                request.session['user_id'] = user.user_id
                request.session['role'] = user.role

                # Redirect based on role
                if user.role.lower() == 'admin':
                    return redirect('restaurant:admin-dashboard')
                else:
                    return redirect('restaurant:dashboard')  # regular user dashboard

            else:
                messages.error(request, "Invalid password")
        except Users.DoesNotExist:
            messages.error(request, "Invalid email or role")

    return render(request, 'restaurant/login.html')


def logout_view(request):
    """Log out the user."""
    request.session.flush()
    return redirect('restaurant:login')

from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal

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

    cart_items = Cart.objects.filter(user=user)
    total = sum(item.subtotal for item in cart_items)
    return render(request, 'restaurant/cart.html', {'user': user, 'cart_items': cart_items, 'total': total})



# Cart APIs
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
    """Add a menu item to the cart, update quantity, or remove if quantity <= 0."""
    user = get_logged_in_user(request)
    if not user:
        return Response({"detail": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    item_id = request.data.get('item_id')
    quantity = int(request.data.get('quantity', 1))  # default to 1 if not provided

    if not item_id:
        return Response({"detail": "Item ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        menu_item = MenuItems.objects.get(item_id=item_id)
        cart_item, created = Cart.objects.get_or_create(user=user, item=menu_item)

        # Update quantity
        if created:
            cart_item.quantity = quantity
        else:
            cart_item.quantity = (cart_item.quantity or 0) + quantity

        # Delete cart item if quantity <= 0
        if cart_item.quantity <= 0:
            cart_item.delete()
            return Response({"detail": f"'{menu_item.name}' removed from cart."}, status=status.HTTP_200_OK)

        # Compute subtotal
        cart_item.subtotal = Decimal(menu_item.price) * Decimal(cart_item.quantity)
        cart_item.save()

        # Return flattened response for frontend
        return Response({
            "detail": f"'{menu_item.name}' added/updated in cart.",
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


#remove single cart item
@api_view(['DELETE'])
def remove_from_cart_api(request, cart_id):
    """Remove an item from cart (manual delete since managed=False)."""
    user = get_logged_in_user(request)
    if not user:
        return Response({"detail": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM cart WHERE cart_id = %s AND user_id = %s", [cart_id, user.user_id])
        return Response({"detail": "Item removed successfully"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"detail": f"Error removing item: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# views.py
from django.http import JsonResponse
from decimal import Decimal
from django.utils import timezone
import json

from .models import Orders, OrderItems, Cart, MenuItems, Users

# Helper to get the logged-in user
def get_logged_in_user(request):
    user_id = request.session.get('user_id')  # set this in your login view
    if not user_id:
        return None
    try:
        return Users.objects.get(user_id=user_id)
    except Users.DoesNotExist:
        return None

# Place Order API
def place_order_api(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    user = get_logged_in_user(request)
    if not user:
        return JsonResponse({"detail": "Not logged in"}, status=401)

    cart_items = Cart.objects.filter(user_id=user.user_id)
    if not cart_items.exists():
        return JsonResponse({"detail": "No items in cart"}, status=400)

    try:
        data = json.loads(request.body)

        # calculate total
        subtotal = sum([ci.subtotal for ci in cart_items])
        shipping_fee = Decimal('40.00')
        total_amount = subtotal + shipping_fee

        # create order
        now = timezone.localtime()
        order = Orders.objects.create(
            user_id=user.user_id,  # FK to your Users table
            total_amount=total_amount,
            delivery_address=data.get('address', ''),
            contact_number=data.get('contact', ''),
            delivery_option=data.get('delivery_option', ''),
            notes=data.get('notes', ''),
            payment_method=data.get('payment_method', ''),
            status='Pending',
            order_date=now
        )

        # create order items
        for ci in cart_items:
            OrderItems.objects.create(
                order_id=order.order_id,  # FK to Orders
                item_id=ci.item.item_id,  # FK to MenuItems
                quantity=ci.quantity,
                subtotal=ci.subtotal
            )

        # clear cart
        cart_items.delete()

        return JsonResponse({
            "detail": "Order placed successfully",
            "order_id": order.order_id
        }, status=201)

    except Exception as e:
        return JsonResponse({"detail": f"Error placing order: {str(e)}"}, status=500)





# Order Page View
def order_view(request):
    """Render order tracking page."""
    user = get_logged_in_user(request)
    if not user:
        return render(request, 'restaurant/order.html', {'order': None, 'order_id': None})

    # Get latest order
    order = Orders.objects.filter(user=user).order_by('-order_date').first()
    
    context = {
        'order': order,  # pass the full order object
        'order_id': order.order_id if order else None  # keep for your JS
    }
    return render(request, 'restaurant/order.html', context)




# API: Track Order
def track_order_api(request, order_id):
    """Return order status and timestamps for tracking."""
    user = get_logged_in_user(request)
    if not user:
        return JsonResponse({'error': 'User not logged in'}, status=403)

    order = get_object_or_404(Orders, pk=order_id, user=user)

    steps = ["Order Confirmed", "Preparing Order", "Out for Delivery", "Delivered"]

    # convert all timestamps to localtime
    data = {
        'order_id': order.order_id,
        'status': order.status or "Order Confirmed",
        'order_date': timezone.localtime(order.order_date).strftime('%Y-%m-%d %H:%M') if order.order_date else None,
        'total_amount': float(order.total_amount),
        'steps': steps,
        'timestamps': {
            "Order Confirmed": timezone.localtime(order.confirmed_at).strftime("%I:%M %p") if order.confirmed_at else None,
            "Preparing Order": timezone.localtime(order.preparing_at).strftime("%I:%M %p") if order.preparing_at else None,
            "Out for Delivery": timezone.localtime(order.out_for_delivery_at).strftime("%I:%M %p") if order.out_for_delivery_at else None,
            "Delivered": timezone.localtime(order.delivered_at).strftime("%I:%M %p") if order.delivered_at else None,
        }
    }
    return JsonResponse(data)

def contact_page(request):
    return render(request, 'restaurant/contact.html')

from rest_framework import generics, permissions
from .models import ContactMessage, Users
from .serializers import ContactMessageSerializer

class ContactMessageListCreateAPIView(generics.ListCreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.AllowAny]  # or IsAuthenticated if you want

    def perform_create(self, serializer):
        # Replace this with how you identify the logged-in Users instance
        # For example, if you store `user_id` in session:
        user_id = self.request.session.get('user_id')  
        user_instance = Users.objects.filter(user_id=user_id).first() if user_id else None
        serializer.save(user=user_instance)
        

def about(request):
    return render(request, 'restaurant/about.html')

from django.shortcuts import render, redirect
from .models import Users, Orders

def profile_view(request):
    # Assuming you store the logged-in user's id in the session
    user_id = request.session.get('user_id')  # Example session key
    
    if not user_id:
        # Redirect to login page if not logged in
        return redirect('login')  

    user = Users.objects.filter(user_id=user_id).first()
    
    # Fetch delivered orders for this user
    orders = Orders.objects.filter(user=user, delivered_at__isnull=False).order_by('-delivered_at')

    context = {
        'user': user,
        'orders': orders,  # Pass orders to template
    }
    return render(request, 'restaurant/profile.html', context)


from django.shortcuts import redirect
from django.contrib.auth import logout

def logout_view(request):
    logout(request)  # log out the user
    return redirect('restaurant:login')

from django.shortcuts import render
from .models import MenuItems

def menu(request):
    meals = MenuItems.objects.filter(category='meals')
    drinks = MenuItems.objects.filter(category='drinks')
    desserts = MenuItems.objects.filter(category='desserts')
    
    context = {
        'meals': meals,
        'drinks': drinks,
        'desserts': desserts
    }
    return render(request, 'restaurant/mainmenu.html', context)

from django.shortcuts import render
from .models import Orders, MenuItems, Users

def admin_dashboard(request):
    context = {
        'total_orders': Orders.objects.count(),
        'pending_orders': Orders.objects.filter(status='Pending').count(),
        'total_menu': MenuItems.objects.count(),
        'total_users': Users.objects.count(),
        'orders': Orders.objects.all().order_by('-order_date')[:10]  # last 10 orders
    }
    return render(request, 'restaurant/admin_dashboard.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import MenuItems

def admin_menu(request):
    """Display all menu items."""
    menu_items = MenuItems.objects.all()
    return render(request, 'restaurant/admin_menu.html', {'menu_items': menu_items})

def admin_add_menu(request):
    """Add new menu item."""
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        price = request.POST.get("price")
        category = request.POST.get("category")
        image_url = request.POST.get("image_url")
        is_available = int(request.POST.get("is_available", 1))

        MenuItems.objects.create(
            name=name,
            description=description,
            price=price,
            category=category,
            image_url=image_url,
            is_available=is_available
        )
        messages.success(request, f"{name} added successfully!")
        return redirect('restaurant:admin-menu')

    return render(request, 'restaurant/admin_menu_add.html')

def admin_edit_menu(request, item_id):
    """Edit existing menu item."""
    item = get_object_or_404(MenuItems, item_id=item_id)

    if request.method == "POST":
        item.name = request.POST.get("name")
        item.description = request.POST.get("description")
        item.price = request.POST.get("price")
        item.category = request.POST.get("category")
        item.image_url = request.POST.get("image_url")
        item.is_available = int(request.POST.get("is_available", 1))
        item.save()
        messages.success(request, f"{item.name} updated successfully!")
        return redirect('restaurant:admin-menu')

    return render(request, 'restaurant/admin_menu_edit.html', {'item': item})

def admin_delete_menu(request, item_id):
    """Delete a menu item."""
    item = get_object_or_404(MenuItems, item_id=item_id)
    item.delete()
    messages.success(request, f"{item.name} deleted successfully!")
    return redirect('restaurant:admin-menu')

from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Orders
from .models import Orders, OrderItems



# =========================
# ADMIN: LIST ORDERS
# =========================
from django.shortcuts import render
from django.db.models import Prefetch
from .models import Orders, OrderItems, MenuItems

def admin_orders(request):
    # Get status filter from query params
    status_filter = request.GET.get('status', 'pending')

    # Base queryset with prefetch of order items and related menu item
    orders = Orders.objects.all().prefetch_related(
        Prefetch('items', queryset=OrderItems.objects.select_related('item'))
    )

    # Apply status filter
    if status_filter == 'pending':
        orders = orders.filter(confirmed_at__isnull=True)
    elif status_filter == 'preparing':
        orders = orders.filter(
            confirmed_at__isnull=False,
            preparing_at__isnull=False,
            out_for_delivery_at__isnull=True
        )
    elif status_filter == 'out_for_delivery':
        orders = orders.filter(
            out_for_delivery_at__isnull=False,
            delivered_at__isnull=True
        )
    elif status_filter == 'delivered':
        orders = orders.filter(delivered_at__isnull=False)

    # Render template with orders and current status filter
    return render(
        request,
        "restaurant/admin_orders.html",
        {
            'orders': orders,
            'status_filter': status_filter
        }
    )


# =========================
# ADMIN: UPDATE STATUS
# =========================
def admin_update_orders(request, order_id):
    order = get_object_or_404(Orders, order_id=order_id)

    if request.method == "POST":
        new_status = request.POST.get("status")
        now = timezone.now()

        if new_status == "preparing":
            order.confirmed_at = order.confirmed_at or now
            order.preparing_at = now
            order.status = "preparing"

        elif new_status == "out_for_delivery":
            order.preparing_at = order.preparing_at or now
            order.out_for_delivery_at = now
            order.status = "out_for_delivery"

        elif new_status == "delivered":
            order.confirmed_at = order.confirmed_at or now
            order.preparing_at = order.preparing_at or now
            order.out_for_delivery_at = order.out_for_delivery_at or now
            order.delivered_at = now
            order.status = "delivered"

        order.save()

        # Redirect to correct filtered view
        return redirect(f'/admin-orders/?status={new_status}')

    # fallback redirect
    return redirect('/admin-orders/')



# =========================
# ADMIN: CONFIRM ORDER
# (PENDING → PREPARING)
# =========================
def confirm_order(request, order_id):
    order = get_object_or_404(Orders, order_id=order_id)

    if request.method == "POST":
        now = timezone.now()
        order.confirmed_at = now
        order.preparing_at = now
        order.status = "preparing"
        order.save()

    return redirect('/admin-orders/?status=preparing')


from django.shortcuts import render
from .models import Feedback
from .serializers import FeedbackSerializer


def admin_feedback(request):
    # Fetch all feedback, newest first
    feedback_list = Feedback.objects.all().order_by('-date_submitted')
    context = {
        'feedback_list': feedback_list
    }
    return render(request, 'restaurant/admin_feedback.html', context)

@api_view(['POST'])
def submit_feedback(request):
    # Get user from session
    user_id = request.session.get('user_id')
    if not user_id:
        return Response({'detail': 'You must be logged in to submit feedback.'}, status=status.HTTP_403_FORBIDDEN)

    user = Users.objects.get(pk=user_id)
    serializer = FeedbackSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(user=user, date_submitted=timezone.now())
        return Response({'message': 'Feedback submitted successfully!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Orders

@csrf_exempt
def mark_order_seen(request, order_id):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    
    try:
        order = Orders.objects.get(pk=order_id)
        # Reset timestamps (o mark all as not seen)
        order.timestamps = {}  # assuming JSONField
        order.save()
        return JsonResponse({"detail": "Order marked as seen"})
    except Orders.DoesNotExist:
        return JsonResponse({"detail": "Order not found"}, status=404)





