# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from decimal import Decimal


class Deliveries(models.Model):
    delivery_id = models.AutoField(primary_key=True)
    order = models.ForeignKey('Orders', models.DO_NOTHING)
    rider = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    delivery_address = models.CharField(max_length=255)
    delivery_status = models.CharField(max_length=10, blank=True, null=True)
    delivery_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
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
        managed = False  # ✅ keep False since database is manually managed
        db_table = 'cart'

    def __str__(self):
        return f"{self.user} - {self.item} (x{self.quantity})"


class Orders(models.Model):
    order_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    order_date = models.DateTimeField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=16, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders'


class Payments(models.Model):
    payment_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Orders, models.DO_NOTHING)
    payment_method = models.CharField(max_length=5, blank=True, null=True)
    payment_status = models.CharField(max_length=7, blank=True, null=True)
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
