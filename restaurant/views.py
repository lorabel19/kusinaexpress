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
    """Render user profile with order history."""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')

    user = Users.objects.filter(user_id=user_id).first()
    
    # Fetch delivered orders for this user
    orders = Orders.objects.filter(user=user, delivered_at__isnull=False).order_by('-delivered_at')

    context = {
        'user': user,
        'orders': orders,
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


@api_view(['GET'])
def track_order_api(request, order_id):
    """Return order status and timestamps for tracking with map coordinates."""
    order = get_object_or_404(Orders, pk=order_id)

    # Sample coordinates for demo (Quezon City as start)
    START_COORDS = [14.6760, 121.0437]
    
    # For demo, we convert delivery_address to coordinates manually (or just use a fixed point)
    # Example: Let's assume all deliveries go to Paranaque for demo
    end_coords = [14.5176, 121.0509]  # You can adjust per order.delivery_address

    steps = ["Order Confirmed", "Preparing Order", "Out for Delivery", "Delivered"]

    # Prepare order timestamps
    timestamps = {
        "Order Confirmed": timezone.localtime(order.confirmed_at).strftime("%I:%M %p") if order.confirmed_at else None,
        "Preparing Order": timezone.localtime(order.preparing_at).strftime("%I:%M %p") if order.preparing_at else None,
        "Out for Delivery": timezone.localtime(order.out_for_delivery_at).strftime("%I:%M %p") if order.out_for_delivery_at else None,
        "Delivered": timezone.localtime(order.delivered_at).strftime("%I:%M %p") if order.delivered_at else None,
    }

    data = {
        'order_id': order.order_id,
        'status': order.status or "Order Confirmed",
        'order_date': timezone.localtime(order.order_date).strftime('%Y-%m-%d %H:%M') if order.order_date else None,
        'total_amount': float(order.total_amount),
        'steps': steps,
        'timestamps': timestamps,
        "start_lat": START_COORDS[0],
        "start_lng": START_COORDS[1],
        "end_lat": end_coords[0],
        "end_lng": end_coords[1],
    }
    
    return Response(data)


@csrf_exempt
def mark_order_seen(request, order_id):
    """Mark an order as seen by user."""
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
    # Summary
    total_orders = Orders.objects.count()
    pending_orders = Orders.objects.filter(status='Pending').count()
    total_menu = MenuItems.objects.count()
    total_users = Users.objects.count()

    # Last 10 orders
    orders = Orders.objects.all().order_by('-order_date')[:10]

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

    # Get admin user (assuming role='admin')
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
        'admin_name': admin_name,  # Greeting name
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

def admin_orders(request):
    """Display orders filtered by status for admin."""
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


def admin_update_orders(request, order_id):
    """Update order status with timestamps."""
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


def confirm_order(request, order_id):
    """Confirm order and move from pending to preparing status."""
    order = get_object_or_404(Orders, order_id=order_id)

    if request.method == "POST":
        now = timezone.now()
        order.confirmed_at = now
        order.preparing_at = now
        order.status = "preparing"
        order.save()

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