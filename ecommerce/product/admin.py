from django.contrib import admin
from .models import OfferBanner, Carousel,Wishlist

from .models import Category, Product,Brand,SubCategory,NestedCategory

admin.site.register([Category, Product,Brand,SubCategory,NestedCategory])

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_date') 
    list_filter = ('user', 'added_date')

@admin.register(OfferBanner)
class OfferBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'expiry_date', 'is_active')

@admin.register(Carousel)
class CarouselAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active')