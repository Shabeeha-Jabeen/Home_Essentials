from django.db import models
from django.contrib.auth.models import User
from product.models import Product

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return sum(item.sub_total() for item in self.cart_items.all())

from product.models import Product, ProductVariant 

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def sub_total(self):
        if self.variant:
            return self.variant.price * self.quantity
        
        price = self.product.discount_price if self.product.discount_price else self.product.price
        return price * self.quantity



class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
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

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
   
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    variant_name = models.CharField(max_length=50, null=True, blank=True) 
    
    product_name = models.CharField(max_length=255) 
    product_image = models.ImageField(upload_to='order_items/', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def sub_total(self):
        return self.price * self.quantity