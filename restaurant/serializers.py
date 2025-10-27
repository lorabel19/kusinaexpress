from rest_framework import serializers
from .models import MenuItems, OrderItems, Orders

# Serializer for Menu Items
class MenuItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItems
        fields = '__all__'


# Serializer for individual Order Items
class OrderItemsSerializer(serializers.ModelSerializer):
    # Include nested menu item details
    item = MenuItemsSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=MenuItems.objects.all(), source='item', write_only=True
    )

    class Meta:
        model = OrderItems
        fields = ['order_item_id', 'order', 'item', 'item_id', 'quantity', 'subtotal']


# Serializer for Orders
class OrdersSerializer(serializers.ModelSerializer):
    order_items = OrderItemsSerializer(many=True, read_only=True)

    class Meta:
        model = Orders
        fields = ['order_id', 'user', 'order_items', 'total', 'delivery_address', 
                  'contact_number', 'delivery_option', 'notes', 'payment_method', 'status', 'created_at']
