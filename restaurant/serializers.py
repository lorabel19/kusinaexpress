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

    #timestamps for order tracking
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
            'timestamps',  
        ]

    # SerializerMethodField function
    def get_timestamps(self, obj):
        return {
            "Order Confirmed": obj.confirmed_at.strftime("%I:%M %p") if obj.confirmed_at else None,
            "Preparing Order": obj.preparing_at.strftime("%I:%M %p") if obj.preparing_at else None,
            "Out for Delivery": obj.out_for_delivery_at.strftime("%I:%M %p") if obj.out_for_delivery_at else None,
            "Delivered": obj.delivered_at.strftime("%I:%M %p") if obj.delivered_at else None,
        }

from rest_framework import serializers
from django.utils import timezone
from .models import Feedback, Users  # import your custom Users model

class FeedbackSerializer(serializers.ModelSerializer):
    # Make user read-only; it will be set automatically
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Feedback
        fields = ['feedback_id', 'user', 'message', 'rating', 'date_submitted']
        read_only_fields = ['feedback_id', 'user', 'date_submitted']

    def create(self, validated_data):
        """
        Automatically set the user and date_submitted when creating a Feedback.
        """
        request = self.context.get('request')
        if request is None:
            raise serializers.ValidationError("Request context is required.")

        # Use your custom Users model
        user = getattr(request, 'user', None)
        if user is None or not user.is_authenticated:
            # If using session manually
            user_id = request.session.get('user_id')
            if not user_id:
                raise serializers.ValidationError("User must be logged in to submit feedback.")
            user = Users.objects.get(pk=user_id)

        validated_data['user'] = user
        validated_data['date_submitted'] = timezone.now()
        return super().create(validated_data)






