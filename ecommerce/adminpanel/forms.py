from django import forms
from product.models import Category, Product, Carousel, OfferBanner

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'image', 'is_active']
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name',
            'category',
            'subcategory',
            'nested_category',
            'brand',
            'description',
            'price',
            'discount_price',
            'stock',
            'image',
            'image_2',
            'image_3',
            'is_offer',
            'is_featured',
            'is_active'
        ]



class CarouselForm(forms.ModelForm):
    class Meta:
        model = Carousel
        fields = '__all__'

class OfferBannerForm(forms.ModelForm):
    class Meta:
        model = OfferBanner
        fields = '__all__'