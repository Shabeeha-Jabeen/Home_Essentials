from django import forms
from product.models import Category, Product, Carousel, OfferBanner

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'image', 'is_active']
from django import forms
from product.models import Product, Category, SubCategory, NestedCategory, Brand, Material

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'subcategory', 'nested_category', 
            'brand', 'material', 'description', 'price', 
            'discount_price', 'is_offer', 'offer_end_date', 
            'stock', 'image', 'image_2', 'image_3', 
            'is_featured', 'is_active'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'subcategory': forms.Select(attrs={'class': 'form-control'}),
            'nested_category': forms.Select(attrs={'class': 'form-control'}),
            'brand': forms.Select(attrs={'class': 'form-control'}),
            'material': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Product description...'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Original Price'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Offer Price'}),
            'offer_end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'image_2': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'image_3': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_offer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        is_offer = cleaned_data.get('is_offer')
        discount_price = cleaned_data.get('discount_price')
        offer_end_date = cleaned_data.get('offer_end_date')
        price = cleaned_data.get('price')

        
        if is_offer:
            if not discount_price:
                self.add_error('discount_price', "Offer active aakkanel Discount Price nirbandhamaanu.")
            if not offer_end_date:
                self.add_error('offer_end_date', "Offer eppo thirayum ennu (Expiry Date) select cheyyuka.")
            
            
            if discount_price and price and discount_price >= price:
                self.add_error('discount_price', "Discount price original price-inekkal kuravaayirikkanam.")

        return cleaned_data


class CarouselForm(forms.ModelForm):
    class Meta:
        model = Carousel
        fields = '__all__'

class OfferBannerForm(forms.ModelForm):
    class Meta:
        model = OfferBanner
        fields = '__all__'