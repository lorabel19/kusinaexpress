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

    # ✅ Add flattened image_url field for frontend
    image_url = serializers.CharField(source='item.image_url', read_only=True)

    class Meta:
        model = Cart
        fields = ['cart_id', 'user', 'item', 'item_id', 'quantity', 'subtotal', 'image_url']


# Serializer for Orders
class OrdersSerializer(serializers.ModelSerializer):
    # Use CartSerializer instead of OrderItemsSerializer
    order_items = CartSerializer(many=True, read_only=True, source='cart_set')

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
            'order_date'
        ]
