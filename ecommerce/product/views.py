from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category, Product, Carousel, OfferBanner, Brand, SubCategory, Wishlist,Review,Material ,NestedCategory
from django.views.decorators.cache import never_cache
from orders.models import Cart,CartItem
from django.db.models.functions import Coalesce
def get_wishlist_ids(request):
    if request.user.is_authenticated:
        return Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
    return []
@never_cache
def home(request):
   
    categories = Category.objects.filter(is_active=True)
    
    
    featured_products = Product.objects.filter(
        is_active=True, 
        is_featured=True, 
        stock__gt=0
    ).order_by('-id')[:8]
    
    
    new_arrivals = Product.objects.filter(
        is_active=True, 
        stock__gt=0
    ).order_by('-id')[:8]
    
    
    carousels = Carousel.objects.filter(is_active=True)
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'carousels': carousels,
        'wishlist_product_ids': get_wishlist_ids(request),
    }
    return render(request, 'product/home.html', context)
@never_cache
def offers(request):
   
    products = Product.objects.filter(is_offer=True, is_active=True)
    
    for product in products:
       
        if product.price and product.discount_price and product.price > product.discount_price:
            discount = product.price - product.discount_price
            percentage = (discount / product.price) * 100
            product.discount_percentage = round(percentage)
        else:
            product.discount_percentage = 0

    banner = OfferBanner.objects.filter(is_active=True).last() 
    
    context = {
        'products': products,
        'banner': banner,
        'wishlist_product_ids': get_wishlist_ids(request),
    }
    return render(request, 'product/offers.html', context)

def product_list_view(request):
    
    products = Product.objects.filter(is_active=True).select_related('brand', 'category')
    
    # URL Parameters fetching
    brand_id = request.GET.get('brand')
    cat_id = request.GET.get('category')
    sub_id = request.GET.get('subcategory')
    nest_id = request.GET.get('nested_category')
    mat_id = request.GET.get('material')
    
    # Price Filter Parameters
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    # 2. Category & Brand Filtering Logic
    if brand_id:
        products = products.filter(brand_id=brand_id)
    if cat_id:
        products = products.filter(category_id=cat_id)
    if sub_id:
        products = products.filter(subcategory_id=sub_id)
    if nest_id:
        products = products.filter(nested_category_id=nest_id)
    if mat_id:
        products = products.filter(material_id=mat_id)

   
    if min_price:
        products = products.filter(
            Q(is_offer=True, discount_price__gte=min_price) | 
            Q(is_offer=False, price__gte=min_price)
        )
    if max_price:
        products = products.filter(
            Q(is_offer=True, discount_price__lte=max_price) | 
            Q(is_offer=False, price__lte=max_price)
        )

    
    available_materials = None
    if nest_id:
        available_materials = Material.objects.filter(product__nested_category_id=nest_id).distinct()

    # 4. Wishlist Status Tracking
    wishlisted_product_ids = []
    if request.user.is_authenticated:
        
        wishlisted_product_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)

    # 5. Context Building
    context = {
        'products': products.distinct().order_by('-id'),
        'categories': Category.objects.filter(is_active=True),
        'sub_categories': SubCategory.objects.all(),
        'nested_categories': NestedCategory.objects.all(),
        'brands': Brand.objects.all(),
        'materials': available_materials,
        'wishlisted_products': list(wishlisted_product_ids), 
    }
    
    return render(request, 'product/products.html', context)


def product_search_view(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(is_active=True)
    
    # 1. Search Logic with Split words
    if query:
        query_words = query.split()
        search_filter = Q()
        for word in query_words:
            search_filter |= (
                Q(name__icontains=word) | 
                Q(description__icontains=word) |
                Q(brand__name__icontains=word) |
                Q(category__name__icontains=word) |
                Q(subcategory__name__icontains=word) |
                Q(material__name__icontains=word) 
            )
        
        products = products.filter(search_filter).distinct()
    
    # 2. Sorting Logic
    sort_by = request.GET.get('sort')
    
    products = products.annotate(effective_price=Coalesce('discount_price', 'price'))

    if sort_by == 'price_low':
        products = products.order_by('effective_price')
    elif sort_by == 'price_high':
        products = products.order_by('-effective_price')
    elif sort_by == 'new_arrivals':
        products = products.order_by('-created_at')
    else:
        # Default sorting by ID or Created At
        products = products.order_by('-id')

    # 3. Context Data
    context = {
        'products': products,
        'query': query,
        'is_search': True,
        'brands': Brand.objects.all(),
        'categories': Category.objects.filter(is_active=True),
        
        'materials': Material.objects.all() if 'Material' in globals() else [],
        'wishlist_product_ids': get_wishlist_ids(request) if 'get_wishlist_ids' in globals() else [],
    }

    return render(request, 'product/products.html', context)
@never_cache
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if not product.is_active:
        messages.warning(request, "This product is currently unavailable.")
        return redirect('product_list')

    
    variants = product.variants.all().order_by('price') 

    related_products = []
    if product.subcategory:
        related_products = Product.objects.filter(
            subcategory=product.subcategory, 
            is_active=True
        ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'variants': variants, 
        'related_products': related_products,
        'wishlist_product_ids': get_wishlist_ids(request),
    }
    return render(request, 'product/product_detail.html', context)

@login_required
def add_review(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        
        Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            comment=comment
        )
        
        messages.success(request, "Thank you! Your review has been submitted.")
    return redirect('product_detail', product_id=product_id)

# --- WISHLIST MANAGEMENT ---
@never_cache
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
def move_to_cart(request, item_id):
    wishlist_item = get_object_or_404(Wishlist, id=item_id, user=request.user)
    product = wishlist_item.product
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        
    wishlist_item.delete()
    
    messages.success(request, f"{product.name} moved to cart!")
    return redirect('cart_view')


@login_required
def wishlist_to_checkout(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
    else:
        cart_item.quantity = 1
    cart_item.save()
    
    return redirect('checkout')



@login_required
def move_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f"{product.name} moved to cart!")
    return redirect('cart_view')