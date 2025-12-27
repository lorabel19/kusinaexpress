from django.db import models
from decimal import Decimal
from django.contrib.auth.hashers import make_password, check_password

class Deliveries(models.Model):
    delivery_id = models.AutoField(primary_key=True)
    order = models.ForeignKey('Orders', models.DO_NOTHING)

    delivery_address = models.TextField(blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    delivery_option = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    # Mirror Orders status/timestamps
    status = models.CharField(max_length=32, blank=True, null=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    preparing_at = models.DateTimeField(blank=True, null=True)
    out_for_delivery_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False  # kung gusto mong hindi i-migrate ng Django
        db_table = 'deliveries'




class Feedback(models.Model):
    feedback_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    message = models.TextField()
    rating = models.IntegerField(blank=True, null=True)
    date_submitted = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'feedback'


class MenuItems(models.Model):
    item_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=8, blank=True, null=True)
    image_url = models.CharField(max_length=255, blank=True, null=True)
    is_available = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'menu_items'


class Cart(models.Model):
    cart_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('Users', on_delete=models.DO_NOTHING)
    item = models.ForeignKey('MenuItems', on_delete=models.DO_NOTHING)
    quantity = models.IntegerField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        managed = False  
        db_table = 'cart'

    def __str__(self):
        return f"{self.user} - {self.item} (x{self.quantity})"


class Orders(models.Model):
    order_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    order_date = models.DateTimeField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'orders'



    
from django.db import models

class OrderItems(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(
        'Orders',  # Make sure you have an Orders model
        db_column='order_id',
        related_name='items',
        on_delete=models.DO_NOTHING
    )
    item = models.ForeignKey(
        'MenuItems',  # Make sure you have a MenuItems model
        db_column='item_id',
        on_delete=models.DO_NOTHING
    )
    quantity = models.IntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'OrderItems'  # This must match your MySQL table name
        managed = False


class Payments(models.Model):
    payment_id = models.AutoField(primary_key=True)
    order = models.ForeignKey('Orders', models.DO_NOTHING)

    payment_method = models.CharField(max_length=50, blank=True, null=True)
    payment_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'payments'



class Users(models.Model):
    user_id = models.AutoField(primary_key=True)
    email = models.CharField(unique=True, max_length=100)
    password = models.CharField(max_length=255)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    role = models.CharField(max_length=5, blank=True, null=True)
    date_joined = models.DateTimeField(blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'


class Admin(models.Model):
    admin_id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True, max_length=100)
    password = models.CharField(max_length=255)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin'   # IMPORTANT: existing table
        managed = False      # dahil gumawa ka na ng table sa MySQL

    def save(self, *args, **kwargs):
        # auto-hash kapag plain text pa ang password
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)


class ContactMessage(models.Model):
    message_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('Users', models.SET_NULL, null=True, blank=True)  
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    rating = models.IntegerField(null=True, blank=True)
    date_submitted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"

    class Meta:
        db_table = 'contact_message'  
        managed = False               

