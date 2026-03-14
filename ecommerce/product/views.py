from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, F, Case, When, DecimalField
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.db.models.functions import Coalesce

from .models import (
    Category, Product, Carousel, OfferBanner, Brand, 
    SubCategory, Wishlist, Review, Material, NestedCategory
)
from orders.models import Cart, CartItem

def get_wishlist_ids(request):
    """User-inte wishlist-il ulla product IDs return cheyyunnu"""
    if request.user.is_authenticated:
        return Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
    return []

@never_cache
def home(request):
    now = timezone.now() 
    context = {
        'categories': Category.objects.filter(is_active=True),
        'featured_products': Product.objects.filter(is_active=True, is_featured=True, stock__gt=0).order_by('-id')[:8],
        'new_arrivals': Product.objects.filter(is_active=True, stock__gt=0).order_by('-id')[:8],
        'carousels': Carousel.objects.filter(is_active=True),
        'wishlist_product_ids': get_wishlist_ids(request),
        'now': now,  
    }
    return render(request, 'product/home.html', context)

@never_cache
def product_list_view(request):
    now = timezone.now()
   
    products = Product.objects.filter(is_active=True).annotate(
        current_p=Case(
            When(is_offer=True, offer_end_date__gt=now, then=F('discount_price')),
            default=F('price'),
            output_field=DecimalField(),
        )
    ).select_related('brand', 'category')

    brand_id = request.GET.get('brand')
    cat_id = request.GET.get('category')
    sub_id = request.GET.get('subcategory')
    nest_id = request.GET.get('nested_category')
    mat_id = request.GET.get('material')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if brand_id: products = products.filter(brand_id=brand_id)
    if cat_id: products = products.filter(category_id=cat_id)
    if sub_id: products = products.filter(subcategory_id=sub_id)
    if nest_id: products = products.filter(nested_category_id=nest_id)
    if mat_id: products = products.filter(material_id=mat_id)

    if min_price: products = products.filter(current_p__gte=min_price)
    if max_price: products = products.filter(current_p__lte=max_price)

    sort_by = request.GET.get('sort')
    if sort_by == 'price_low':
        products = products.order_by('current_p')
    elif sort_by == 'price_high':
        products = products.order_by('-current_p')
    elif sort_by == 'new_arrivals':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('-id')

    context = {
        'products': products.distinct(),
        'categories': Category.objects.filter(is_active=True),
        'sub_categories': SubCategory.objects.all(),
        'nested_categories': NestedCategory.objects.all(),
        'brands': Brand.objects.all(),
        'materials': Material.objects.all(),
        'wishlisted_products': list(get_wishlist_ids(request)),
        'now': now,
    }
    return render(request, 'product/products.html', context)

@never_cache
def product_search_view(request):
    query = request.GET.get('q', '').strip()
    now = timezone.now()
    products = Product.objects.filter(is_active=True).annotate(
        current_p=Case(
            When(is_offer=True, offer_end_date__gt=now, then=F('discount_price')),
            default=F('price'),
            output_field=DecimalField(),
        )
    )
    
    if query:
        query_words = query.split()
        search_filter = Q()
        for word in query_words:
            search_filter |= (
                Q(name__icontains=word) | Q(description__icontains=word) |
                Q(brand__name__icontains=word) | Q(category__name__icontains=word)
            )
        products = products.filter(search_filter).distinct()
    
    sort_by = request.GET.get('sort')
    if sort_by == 'price_low': products = products.order_by('current_p')
    elif sort_by == 'price_high': products = products.order_by('-current_p')
    else: products = products.order_by('-id')

    context = {
        'products': products,
        'query': query,
        'is_search': True,
        'categories': Category.objects.filter(is_active=True),
        'wishlist_product_ids': get_wishlist_ids(request),
    }
    return render(request, 'product/products.html', context)

@never_cache
def offers(request):
    now = timezone.now()
    products = Product.objects.filter(is_offer=True, is_active=True, offer_end_date__gt=now)
    
    if not products.exists():
        return render(request, 'product/no_offers.html')

    banner = OfferBanner.objects.filter(is_active=True, expiry_date__gt=now).last()
    context = {
        'products': products,
        'banner': banner,
        'wishlist_product_ids': get_wishlist_ids(request),
    }
    return render(request, 'product/offers.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if not product.is_active:
        messages.warning(request, "This product is currently unavailable.")
        return redirect('product_list_view')

    context = {
        'product': product,
        'variants': product.variants.all().order_by('price'),
        'related_products': Product.objects.filter(subcategory=product.subcategory, is_active=True).exclude(id=product.id)[:4],
        'wishlist_product_ids': get_wishlist_ids(request),
    }
    return render(request, 'product/product_detail.html', context)



@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).order_by('-added_date')
    return render(request, 'product/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wish_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        wish_item.delete()
        messages.info(request, "Removed from wishlist.")
    else:
        messages.success(request, "Added to wishlist.")
    return redirect(request.META.get('HTTP_REFERER', 'wishlist_view'))

@login_required
def remove_from_wishlist(request, item_id):
    wishlist_item = get_object_or_404(Wishlist, id=item_id, user=request.user)
    wishlist_item.delete()
    messages.success(request, "Item removed from wishlist.")
    return redirect('wishlist_view')

@login_required
def move_to_cart(request, product_id):
    """Wishlist item-ne cart-ilekku move cheyyunnu"""
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    

    Wishlist.objects.filter(user=request.user, product=product).delete()
    
    messages.success(request, f"{product.name} moved to cart!")
    return redirect('cart_view')

@login_required
def wishlist_to_checkout(request, product_id):
    """Buy Now from Wishlist: Cart-il add cheythu direct checkout-ilekku"""
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    cart_item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    
    return redirect('checkout')

@login_required
def add_review(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)
        Review.objects.create(
            product=product,
            user=request.user,
            rating=request.POST.get('rating'),
            comment=request.POST.get('comment')
        )
        messages.success(request, "Thank you! Your review has been submitted.")
    return redirect('product_detail', product_id=product_id)