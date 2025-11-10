from rest_framework import serializers
from .models import MenuItems, Cart, Orders

# Serializer for Menu Items
class MenuItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItems
        fields = '__all__'


# Serializer for individual Cart Items
class CartSerializer(serializers.ModelSerializer):
    # Include nested menu item details
    item = MenuItemsSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=MenuItems.objects.all(), source='item', write_only=True
    )

    # Add flattened image_url field for frontend
    image_url = serializers.CharField(source='item.image_url', read_only=True)

    class Meta:
        model = Cart
        fields = ['cart_id', 'user', 'item', 'item_id', 'quantity', 'subtotal', 'image_url']


# Serializer for Orders
class OrdersSerializer(serializers.ModelSerializer):
    # Use CartSerializer for order items
    order_items = CartSerializer(many=True, read_only=True, source='cart_set')

    # ✅ Add timestamps for order tracking
    timestamps = serializers.SerializerMethodField()

    class Meta:
        model = Orders
        fields = [
            'order_id',
            'user',
            'order_items',
            'total_amount',
            'delivery_address',
            'contact_number',
            'delivery_option',
            'notes',
            'payment_method',
            'status',
            'order_date',
            'timestamps',  # include timestamps
        ]

    # SerializerMethodField function
    def get_timestamps(self, obj):
        return {
            "Order Confirmed": obj.confirmed_at.strftime("%I:%M %p") if obj.confirmed_at else None,
            "Preparing Order": obj.preparing_at.strftime("%I:%M %p") if obj.preparing_at else None,
            "Out for Delivery": obj.out_for_delivery_at.strftime("%I:%M %p") if obj.out_for_delivery_at else None,
            "Delivered": obj.delivered_at.strftime("%I:%M %p") if obj.delivered_at else None,
        }
