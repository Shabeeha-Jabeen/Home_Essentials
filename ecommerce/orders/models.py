from django.db import models
from django.contrib.auth.models import User
from product.models import Product, ProductVariant
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return sum(item.sub_total for item in self.cart_items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def sub_total(self):
        if self.variant:
            return self.variant.price * self.quantity
        return self.product.get_display_price() * self.quantity

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Return Requested', 'Return Requested'),
        ('Returned', 'Returned'),
    )

    PAYMENT_CHOICES = (
        ('COD', 'Cash on Delivery'),
        ('Online', 'Online Payment'),
        ('Wallet', 'Wallet Payment'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    address = models.TextField()
    landmark = models.CharField(max_length=255, blank=True, null=True) 
    city = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='COD')
    is_paid = models.BooleanField(default=False)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.full_name}"


    @property
    def get_items_total(self):
        """Delivery-um Tax-um illatha items-inte thuka mathram"""
        return sum(item.sub_total() for item in self.order_items.all())

    @property
    def delivery_fee(self):
        """Fixed delivery charge"""
        return Decimal('31.00')

    
    @property
    def is_returnable(self):
        if self.status == 'Delivered':
            expiry_date = self.created_at + timedelta(days=7)
            return timezone.now() <= expiry_date
        return False
class OrderItem(models.Model):
    ITEM_STATUS_CHOICES = (
        ('Placed', 'Placed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Return Requested', 'Return Requested'),
        ('Returned', 'Returned'),
    )
    status = models.CharField(max_length=20, choices=ITEM_STATUS_CHOICES, default='Placed')
    return_reason = models.TextField(null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    
    product_name = models.CharField(max_length=255) 
    variant_name = models.CharField(max_length=100, null=True, blank=True) 
    product_image = models.ImageField(upload_to='order_items/snapshots/', null=True, blank=True)
    
    price = models.DecimalField(max_digits=10, decimal_places=2) 
    quantity = models.PositiveIntegerField(default=1)

    status = models.CharField(max_length=20, choices=ITEM_STATUS_CHOICES, default='Placed')

    def sub_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product_name} ({self.quantity}) - {self.status}"