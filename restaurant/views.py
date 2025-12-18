# ============================================================================
# IMPORTS
# ============================================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.http import JsonResponse
from django.db import connection
from django.db.models import Sum, Prefetch
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .models import Payments, Deliveries


from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response

from decimal import Decimal
import json
from datetime import datetime

from .models import (
    MenuItems, Users, Orders, Cart, OrderItems, 
    ContactMessage, Feedback
)
from .serializers import (
    MenuItemsSerializer, CartSerializer, OrdersSerializer,
    ContactMessageSerializer, FeedbackSerializer
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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


def format_time(dt):
    """Convert datetime to string format."""
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

from django.contrib.auth.hashers import check_password

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        try:
            user = Users.objects.get(email=email)

            if check_password(password, user.password):   # <-- FIXED

                if user.role.lower() != role.lower():
                    if role.lower() == 'admin':
                        messages.error(request, "This email is not registered as an admin")
                    else:
                        messages.error(request, "This email is not registered as a regular user")
                    return render(request, 'restaurant/login.html')

                request.session['user_id'] = user.user_id
                request.session['role'] = user.role
                request.session['email'] = user.email
                request.session['first_name'] = user.first_name
                request.session['last_name'] = user.last_name

                if user.role.lower() == 'admin':
                    messages.success(request, f"Welcome back, Admin {user.first_name}!")
                    return redirect('restaurant:admin-dashboard')
                else:
                    messages.success(request, f"Welcome back, {user.first_name}!")
                    return redirect('restaurant:dashboard')

            else:
                messages.error(request, "Invalid password")

        except Users.DoesNotExist:
            messages.error(request, "Invalid email address")

    if 'user_id' in request.session:
        del request.session['user_id']
    if 'role' in request.session:
        del request.session['role']
    
    return render(request, 'restaurant/login.html')

# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .models import Users
from django.utils import timezone
import re

def create_account(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        # Validation
        errors = []
        
        # Check if email is valid
        if not email:
            errors.append('Email is required')
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('Please enter a valid email address')
        elif Users.objects.filter(email=email).exists():
            errors.append('Email already exists')
        
        # Check password
        if not password:
            errors.append('Password is required')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters')
        elif not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter')
        elif not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter')
        elif not re.search(r'[0-9]', password):
            errors.append('Password must contain at least one number')
        
        # Check password confirmation
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        # Check names
        if not first_name:
            errors.append('First name is required')
        if not last_name:
            errors.append('Last name is required')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('restaurant:login')
        
        try:
            # Create user with hashed password
            user = Users(
                email=email,
                password=make_password(password),  # Hash the password
                first_name=first_name,
                last_name=last_name,
                role='user',  # Default role is user
                date_joined=timezone.now(),
                is_active=1  # Set as active
            )
            user.save()
            
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('restaurant:login')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('restaurant:login')
    
    return redirect('restaurant:login')

def logout_view(request):
    """Log out the user."""
    logout(request)  # log out the user
    request.session.flush()
    return redirect('restaurant:login')


# ============================================================================
# PUBLIC PAGES
# ============================================================================

def home(request):
    """Render home page."""
    user = get_logged_in_user(request)
    
    # Get featured menu items from the database
    try:
        # Option 1: Get available meals (you can adjust the filter)
        featured_items = MenuItems.objects.filter(
            is_available=1,  # Using 1 for available since it's IntegerField
            category='meals'  # Assuming you want to feature meals
        )[:3]
        
        # If you want to create a featured flag later, you can add:
        # featured_items = MenuItems.objects.filter(is_available=1, is_featured=True)[:3]
        
        # Convert QuerySet to list of dictionaries for template compatibility
        featured_items_list = []
        for item in featured_items:
            featured_items_list.append({
                'name': item.name,
                'description': item.description or '',
                'price': float(item.price),  # Convert Decimal to float for template
                'image_url': item.image_url or '',
                'is_available': item.is_available == 1,
                'item_id': item.item_id
            })
        
    except Exception as e:
        print(f"Error fetching featured items: {e}")  # For debugging
        # Fallback to static items if database query fails
        featured_items_list = [
            {
                'name': 'Adobo',
                'description': 'Tender pork or chicken slowly cooked in soy sauce, vinegar, garlic, and bay leaves.',
                'price': 180,
                'image_url': 'https://images.deliveryhero.io/image/fd-ph/LH/t7o8-listing.jpg',
                'is_available': True,
                'item_id': 1
            },
            {
                'name': 'Sinigang',
                'description': 'A comforting sour soup made with tamarind, fresh vegetables, and your choice of pork.',
                'price': 200,
                'image_url': 'https://www.unileverfoodsolutions.com.ph/dam/global-ufs/mcos/SEA/calcmenu/recipes/PH-recipes/appetisers/sizzling-pork-sisig-manila/sizzling-pork-sisig-manila-main.jpg',
                'is_available': True,
                'item_id': 2
            }
        ]
    
    context = {
        'user': user,
        'featured_items': featured_items_list
    }
    
    return render(request, 'restaurant/index.html', context)

def about(request):
    """Render about page."""
    return render(request, 'restaurant/about.html')


def contact_page(request):
    """Render contact page."""
    return render(request, 'restaurant/contact.html')


def menu(request):
    """Render menu page with categories."""
    meals = MenuItems.objects.filter(category='meals')
    drinks = MenuItems.objects.filter(category='drinks')
    desserts = MenuItems.objects.filter(category='desserts')
    
    context = {
        'meals': meals,
        'drinks': drinks,
        'desserts': desserts
    }
    return render(request, 'restaurant/mainmenu.html', context)




# ============================================================================
# USER DASHBOARD & PROFILE
# ============================================================================

def dashboard(request):
    """Render dashboard for logged-in users."""
    user = get_logged_in_user(request)
    if not user:
        return redirect('restaurant:login')
    
    # Get featured items for logged-in users (you could customize this)
    featured_items = MenuItems.objects.filter(is_available=1)[:6]  # Show more items on dashboard
    
    context = {
        'user': user,
        'featured_items': featured_items
    }
    
    return render(request, 'restaurant/index_logged_in.html', context)


def profile_view(request):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')

    user = Users.objects.filter(user_id=user_id).first()

    # Fetch all deliveries for this user where delivered_at is set
    deliveries = Deliveries.objects.filter(
        order__user=user,
        delivered_at__isnull=False
    ).select_related('order').prefetch_related('order__items').order_by('-delivered_at')

    context = {
        'user': user,
        'deliveries': deliveries,
    }
    return render(request, 'restaurant/profile.html', context)



# ============================================================================
# MENU ITEMS API
# ============================================================================

class MenuItemsViewSet(viewsets.ModelViewSet):
    """ViewSet for managing menu items via REST API."""
    queryset = MenuItems.objects.all()
    serializer_class = MenuItemsSerializer


def menu_page(request):
    """Render menu page."""
    user = get_logged_in_user(request)
    items = MenuItems.objects.filter(is_available=1)
    return render(request, 'restaurant/menu.html', {'user': user, 'menu_items': items})


# ============================================================================
# CART VIEWS & APIs
# ============================================================================

def cart_page(request):
    """Render cart page."""
    user = get_logged_in_user(request)
    if not user:
        return redirect('restaurant:login')

    cart_items = Cart.objects.filter(user=user)
    total = sum(item.subtotal for item in cart_items)
    return render(request, 'restaurant/cart.html', {'user': user, 'cart_items': cart_items, 'total': total})


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


# ============================================================================
# ORDER PLACEMENT & TRACKING
# ============================================================================

import json
from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from .models import Orders, OrderItems, Cart, Deliveries, Payments

# -----------------------------
# PLACE ORDER API
# -----------------------------
@csrf_exempt
def place_order_api(request):
    """Place a new order from cart items."""
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

        # Calculate total
        subtotal = sum([ci.subtotal for ci in cart_items])
        shipping_fee = Decimal('40.00')
        total_amount = subtotal + shipping_fee

        now = timezone.localtime()

        # ---------------------
        # CREATE ORDER
        # ---------------------
        order = Orders.objects.create(
            user_id=user.user_id,
            total_amount=total_amount,
            order_date=now
        )

        # ---------------------
        # SAVE ORDER ITEMS
        # ---------------------
        for ci in cart_items:
            OrderItems.objects.create(
                order_id=order.order_id,
                item_id=ci.item.item_id,
                quantity=ci.quantity,
                subtotal=ci.subtotal
            )

        # ---------------------
        # SAVE PAYMENT
        # ---------------------
        Payments.objects.create(
            order=order,
            payment_method=data.get("payment_method", ""),
            payment_date=now
        )

        # ---------------------
        # SAVE DELIVERY
        # ---------------------
        Deliveries.objects.create(
            order=order,
            delivery_address=data.get("address", ""),
            contact_number=data.get("contact", ""),
            delivery_option=data.get("delivery_option", ""),
            notes=data.get("notes", ""),
            status="pending",          # Initial status
            confirmed_at=None,
            preparing_at=None,
            out_for_delivery_at=None,
            delivered_at=None
        )

        # ---------------------
        # CLEAR CART
        # ---------------------
        cart_items.delete()

        return JsonResponse({
            "detail": "Order placed successfully",
            "order_id": order.order_id
        }, status=201)

    except Exception as e:
        return JsonResponse({"detail": f"Error placing order: {str(e)}"}, status=500)


# -----------------------------
# ORDER VIEW (HTML PAGE)
# -----------------------------
def order_view(request):
    """Render order tracking page."""
    user = get_logged_in_user(request)
    if not user:
        return render(
            request,
            "restaurant/order.html",
            {"order": None, "order_id": None},
        )

    order = Orders.objects.filter(user=user).order_by("-order_date").first()

    return render(
        request,
        "restaurant/order.html",
        {
            "order": order,
            "order_id": order.order_id if order else None,
        },
    )


# -----------------------------
# TRACK ORDER API
# -----------------------------
@api_view(["GET"])
def track_order_api(request, order_id):
    """Return order status and tracking information from Deliveries table."""
    order = get_object_or_404(Orders, pk=order_id)
    delivery = Deliveries.objects.filter(order=order).first()

    # Demo map points
    START_COORDS = [14.6760, 121.0437]  # Quezon City
    END_COORDS = [14.5176, 121.0509]    # Paranaque

    steps = [
        "Order Confirmed",
        "Preparing Order",
        "Out for Delivery",
        "Delivered",
    ]

    def format_time(dt):
        return timezone.localtime(dt).strftime("%I:%M %p") if dt else None

    timestamps = {}
    status = "Pending"
    if delivery:
        timestamps = {
            "Order Confirmed": format_time(delivery.confirmed_at),
            "Preparing Order": format_time(delivery.preparing_at),
            "Out for Delivery": format_time(delivery.out_for_delivery_at),
            "Delivered": format_time(delivery.delivered_at),
        }
        status = delivery.status or "Pending"

    return Response(
        {
            "order_id": order.order_id,
            "status": status,
            "order_date": format_time(order.order_date),
            "total_amount": float(order.total_amount),
            "steps": steps,
            "timestamps": timestamps,
            "start_lat": START_COORDS[0],
            "start_lng": START_COORDS[1],
            "end_lat": END_COORDS[0],
            "end_lng": END_COORDS[1],
        }
    )


# -----------------------------
# MARK ORDER AS SEEN
# -----------------------------
@csrf_exempt
def mark_order_seen(request, order_id):
    """Mark an order as seen by user."""
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    try:
        order = Orders.objects.get(pk=order_id)
        delivery = Deliveries.objects.filter(order=order).first()
        if delivery:
            # Reset timestamps or seen status (assuming JSONField exists in Deliveries)
            delivery.timestamps = {}
            delivery.save()
        return JsonResponse({"detail": "Order marked as seen"})
    except Orders.DoesNotExist:
        return JsonResponse({"detail": "Order not found"}, status=404)

# ============================================================================
# CONTACT & FEEDBACK
# ============================================================================

class ContactMessageListCreateAPIView(generics.ListCreateAPIView):
    """API for listing and creating contact messages."""
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.AllowAny]  # or IsAuthenticated if you want

    def perform_create(self, serializer):
        # Replace this with how you identify the logged-in Users instance
        # For example, if you store `user_id` in session:
        user_id = self.request.session.get('user_id')  
        user_instance = Users.objects.filter(user_id=user_id).first() if user_id else None
        serializer.save(user=user_instance)


@api_view(['POST'])
def submit_feedback(request):
    """Submit user feedback."""
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


# ============================================================================
# ADMIN DASHBOARD
# ============================================================================

def admin_dashboard(request):
    """Render admin dashboard with statistics and summaries."""

    # Summary counts
    total_orders = Orders.objects.count()
    pending_orders = Deliveries.objects.filter(status='pending').count()
    total_menu = MenuItems.objects.count()
    total_users = Users.objects.count()

    # Last 10 orders with deliveries prefetched
    orders = Orders.objects.prefetch_related(
        Prefetch('deliveries_set', queryset=Deliveries.objects.all()),
        Prefetch('items', queryset=OrderItems.objects.select_related('item'))
    ).order_by('-order_date')[:10]

    # Best Sellers (top 5)
    best_sellers = (
        OrderItems.objects
        .values('item', 'item__name', 'item__image_url')
        .annotate(total_ordered=Sum('quantity'))
        .order_by('-total_ordered')[:5]
    )

    # Low Sellers (bottom 5)
    low_sellers = (
        OrderItems.objects
        .values('item', 'item__name', 'item__image_url')
        .annotate(total_ordered=Sum('quantity'))
        .order_by('total_ordered')[:5]
    )

    # Admin name
    try:
        admin_user = Users.objects.get(role='admin')
        admin_name = f"{admin_user.first_name} {admin_user.last_name}"
    except Users.DoesNotExist:
        admin_name = "Admin"

    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_menu': total_menu,
        'total_users': total_users,
        'orders': orders,
        'best_sellers': best_sellers,
        'low_sellers': low_sellers,
        'admin_name': admin_name,
    }

    return render(request, 'restaurant/admin_dashboard.html', context)
# ============================================================================
# ADMIN MENU MANAGEMENT
# ============================================================================

def admin_menu(request):
    """Display all menu items for admin."""
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


# ============================================================================
# ADMIN ORDER MANAGEMENT
# ============================================================================

from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Prefetch
from .models import Orders, OrderItems, Deliveries

from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Prefetch
from .models import Orders, OrderItems, Deliveries, Payments

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Prefetch
from django.utils import timezone

from .models import Orders, OrderItems, Deliveries, Payments

from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Prefetch
from .models import Orders, OrderItems, Deliveries, Payments

# -----------------------------
# ADMIN ORDERS VIEW
# -----------------------------
def admin_orders(request):
    """Display orders filtered by status for admin."""
    status_filter = request.GET.get('status', 'pending')

    # Base queryset with prefetch of order items and related deliveries/payments
    orders = Orders.objects.all().prefetch_related(
        Prefetch('items', queryset=OrderItems.objects.select_related('item')),
        Prefetch('deliveries_set', queryset=Deliveries.objects.all()),
        Prefetch('payments_set', queryset=Payments.objects.all())
    )

    # Apply status filter based on Deliveries
    if status_filter != 'all':
        orders = orders.filter(deliveries__status=status_filter)

    return render(
        request,
        "restaurant/admin_orders.html",
        {
            'orders': orders,
            'status_filter': status_filter
        }
    )


# -----------------------------
# UPDATE ORDER STATUS (ADMIN)
# -----------------------------
def admin_update_orders(request, order_id):
    """Update order status and sync Deliveries timestamps."""
    order = get_object_or_404(Orders, order_id=order_id)
    delivery = Deliveries.objects.filter(order=order).first()

    if request.method == "POST":
        new_status = request.POST.get("status")
        now = timezone.now()

        if delivery:
            if new_status == "preparing":
                delivery.status = "preparing"
                delivery.confirmed_at = delivery.confirmed_at or now
                delivery.preparing_at = now

            elif new_status == "out_for_delivery":
                delivery.status = "out_for_delivery"
                delivery.preparing_at = delivery.preparing_at or now
                delivery.out_for_delivery_at = now

            elif new_status == "delivered":
                delivery.status = "delivered"
                delivery.confirmed_at = delivery.confirmed_at or now
                delivery.preparing_at = delivery.preparing_at or now
                delivery.out_for_delivery_at = delivery.out_for_delivery_at or now
                delivery.delivered_at = now

            delivery.save()

        return redirect(f'/admin-orders/?status={new_status}')

    return redirect('/admin-orders/')


# -----------------------------
# CONFIRM ORDER (ADMIN)
# -----------------------------
def confirm_order(request, order_id):
    """Confirm order and move from pending to preparing status."""
    order = get_object_or_404(Orders, order_id=order_id)
    delivery = Deliveries.objects.filter(order=order).first()

    if request.method == "POST" and delivery:
        now = timezone.now()
        delivery.status = "preparing"
        delivery.confirmed_at = now
        delivery.preparing_at = now
        delivery.save()

    return redirect('/admin-orders/?status=preparing')





# ============================================================================
# ADMIN FEEDBACK MANAGEMENT
# ============================================================================

def admin_feedback(request):
    """Display all user feedback for admin."""
    # Fetch all feedback, newest first
    feedback_list = Feedback.objects.all().order_by('-date_submitted')
    context = {
        'feedback_list': feedback_list
    }
    return render(request, 'restaurant/admin_feedback.html', context)