from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='categories/')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.category.name} - {self.name}"

class NestedCategory(models.Model): 
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='nested_categories')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.subcategory.name} -> {self.name}"

# --- PRODUCT ATTRIBUTES ---
class Brand(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='brands/', null=True, blank=True)

    def __str__(self):
        return self.name

class Material(models.Model):
    
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    nested_category = models.ForeignKey(NestedCategory, on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True)
    
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    is_offer = models.BooleanField(default=False)
    offer_end_date = models.DateTimeField(null=True, blank=True)

    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    review_count = models.IntegerField(default=0)
    stock = models.PositiveIntegerField(default=10)

    image = models.ImageField(upload_to='products/')
    image_2 = models.ImageField(upload_to='products/', null=True, blank=True)
    image_3 = models.ImageField(upload_to='products/', null=True, blank=True)

    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_offer_active(self):
        """Checks if the offer is still valid based on date, checkbox, and price"""
        if self.is_offer and self.discount_price and self.offer_end_date:
            return timezone.now() < self.offer_end_date
        return False

    @property
    def current_price(self):
        """Returns discount price if offer is active, else normal price"""
        if self.is_offer_active:
            return self.discount_price
        return self.price

    @property
    def discount_percentage(self):
        """Calculates the percentage of discount"""
        if self.is_offer_active and self.price > 0:
            discount = self.price - self.discount_price
            percentage = (discount / self.price) * 100
            return round(percentage)
        return 0

    def __str__(self):
        return self.name

    def get_display_price(self):
        """Returns discount price if offer is active, else normal price"""
        if self.is_offer_active:
            return self.discount_price
        return self.price

    def __str__(self):
        return self.name
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size_or_volume = models.CharField(max_length=50, help_text="Example: 500ml, 1L, 5L, Small, Large")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} - {self.size_or_volume}"
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    comment = models.TextField(blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True)

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

class OfferBanner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300)
    image = models.ImageField(upload_to='offer_banners/')
    expiry_date = models.DateTimeField() 
    is_active = models.BooleanField(default=True)

class Carousel(models.Model):
    title = models.CharField(max_length=150, blank=True)
    subtitle = models.CharField(max_length=250, blank=True)
    image = models.ImageField(upload_to='carousel/')
    button_text = models.CharField(max_length=50, blank=True)
    button_link = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']