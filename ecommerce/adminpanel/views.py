from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.views.decorators.cache import never_cache
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from accounts.models import Wallet, WalletTransaction
from product.models import Product, ProductVariant, Category, SubCategory, NestedCategory, Brand, Material,OfferBanner,Carousel,Wishlist,Review
from .forms import CarouselForm, OfferBannerForm,ProductForm
from orders.models import Order,OrderItem

# ==========================================
# 1. ADMIN DASHBOARD
# ==========================================

@staff_member_required(login_url='login')
@never_cache
def admin_dashboard(request):
    from product.models import ProductVariant
    low_stock_products = Product.objects.filter(stock__lt=10).count()
    low_stock_variants = ProductVariant.objects.filter(stock__lt=10).count()
    
    context = {
        
        'low_stock_count': low_stock_products + low_stock_variants,
        
    }
    return render(request, 'admin/dashboard.html', context)

# ==========================================
# 2. CATEGORY, SUB & NESTED MANAGEMENT
# ==========================================

@staff_member_required(login_url='login')
def category_management(request):
    from product.models import Category, SubCategory, NestedCategory, Material
    
    search_query = request.GET.get('search', '')
    
   
    categories = Category.objects.all().order_by('-id')
    subcategories = SubCategory.objects.all().order_by('-id')
    nested_categories = NestedCategory.objects.all().order_by('-id')
    materials = Material.objects.all().order_by('-id')
    
    if search_query:
        categories = categories.filter(name__icontains=search_query)
        subcategories = subcategories.filter(name__icontains=search_query)
        nested_categories = nested_categories.filter(name__icontains=search_query)
        materials = materials.filter(name__icontains=search_query) 

    context = {
        'categories': categories,
        'subcategories': subcategories,
        'nested_categories': nested_categories,
        'materials': materials, 
        'search_query': search_query,
    }
    return render(request, 'admin/category/category_list.html', context)
# --- Category ---
@staff_member_required(login_url='login')
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')
        is_active = request.POST.get('is_active') == 'on'
        Category.objects.create(name=name, image=image, is_active=is_active)
        messages.success(request, "Category added successfully")
        return redirect('category_list')
    return render(request, 'admin/category/add.html')




@staff_member_required(login_url='login')
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        if request.FILES.get('image'): category.image = request.FILES.get('image')
        category.is_active = request.POST.get('is_active') == 'on'
        category.save()
        messages.success(request, "Category updated")
        return redirect('category_list')
    return render(request, 'admin/category/edit.html', {'category': category})

@staff_member_required(login_url='login')
def delete_category(request, pk):
    get_object_or_404(Category, pk=pk).delete()
    messages.success(request, "Category deleted")
    return redirect('category_list')

@staff_member_required(login_url='login')
def toggle_category_status(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    cat.is_active = not cat.is_active
    cat.save()
    return redirect('category_list')

# --- Sub Category ---
@staff_member_required(login_url='login')
def add_subcategory(request):
    if request.method == 'POST':
        SubCategory.objects.create(name=request.POST.get('name'), category_id=request.POST.get('category'))
        messages.success(request, "Sub-category added")
        return redirect('category_list')
    return render(request, 'admin/category/add_subcategory.html', {'categories': Category.objects.all()})

@staff_member_required(login_url='login')
def edit_subcategory(request, pk):
    sub = get_object_or_404(SubCategory, pk=pk)
    if request.method == 'POST':
        sub.name = request.POST.get('name')
        sub.category_id = request.POST.get('category')
        sub.save()
        messages.success(request, "Sub-category updated")
        return redirect('category_list')
    return render(request, 'admin/category/edit_subcategory.html', {'subcategory': sub, 'categories': Category.objects.all()})

@staff_member_required(login_url='login')
def delete_subcategory(request, pk):
    get_object_or_404(SubCategory, pk=pk).delete()
    messages.success(request, "Sub-category deleted")
    return redirect('category_list')

# --- Nested Category ---
@staff_member_required(login_url='login')
def add_nested_category(request):
    if request.method == 'POST':
        NestedCategory.objects.create(name=request.POST.get('name'), subcategory_id=request.POST.get('subcategory'))
        messages.success(request, "Nested category added")
        return redirect('category_list')
    return render(request, 'admin/category/add_nested_category.html', {'subcategories': SubCategory.objects.all()})

@staff_member_required(login_url='login')
def edit_nested_category(request, pk):
    nested = get_object_or_404(NestedCategory, pk=pk)
    if request.method == 'POST':
        nested.name = request.POST.get('name')
        nested.subcategory_id = request.POST.get('subcategory')
        nested.save()
        messages.success(request, "Nested category updated")
        return redirect('category_list')
    return render(request, 'admin/category/edit_nested_category.html', {'nested': nested, 'subcategories': SubCategory.objects.all()})

@staff_member_required(login_url='login')
def delete_nested_category(request, pk):
    get_object_or_404(NestedCategory, pk=pk).delete()
    messages.success(request, "Nested category deleted")
    return redirect('category_list')


# ==========================================
# 3. PRODUCT MANAGEMENT (WITH SEARCH)
# ==========================================
@never_cache
@staff_member_required(login_url='login')
def product_list(request):
    search_query = request.GET.get('search', '')
    sort_filter = request.GET.get('sort', '') 

    products = Product.objects.all()

    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(brand__name__icontains=search_query) |
            Q(subcategory__name__icontains=search_query)
        )

  
    if sort_filter == 'low_stock':
        products = products.order_by('stock')  
    elif sort_filter == 'high_stock':
        products = products.order_by('-stock') 
    else:
        products = products.order_by('-created_at') 

    return render(request, 'admin/product_list.html', {
        'products': products, 
        'search_query': search_query,
        'sort_filter': sort_filter
    })


@staff_member_required(login_url='login')
def product_add(request):
    if request.method == 'POST':
       
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    product = form.save()
                    messages.success(request, f"Product '{product.name}' added successfully!")
                    return redirect('product_list')
            except Exception as e:
                messages.error(request, f"Error: {e}")
        else:
           
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'categories': Category.objects.filter(is_active=True),
        'subcategories': SubCategory.objects.all(),
        'nested_categories': NestedCategory.objects.all(),
        'materials': Material.objects.all(),
        'brands': Brand.objects.all(),
    }
    return render(request, 'admin/product_add.html', context)
@staff_member_required(login_url='login')
def update_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        
        form = ProductForm(request.POST, request.FILES, instance=product)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    
                    product = form.save()
                    
                    sizes = request.POST.getlist('variant_size[]')
                    prices = request.POST.getlist('variant_price[]')
                    stocks = request.POST.getlist('variant_stock[]')

                
                    product.variants.all().delete()
                    for i in range(len(sizes)):
                        if sizes[i].strip():
                            ProductVariant.objects.create(
                                product=product,
                                size_or_volume=sizes[i],
                                price=prices[i],
                                stock=stocks[i]
                            )
                    
                    messages.success(request, f"Product '{product.name}' updated successfully!")
                    return redirect('product_list')
            except Exception as e:
                messages.error(request, f"Error saving variants: {e}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
    else:
        form = ProductForm(instance=product)

    context = {
        'form': form,
        'product': product,
        'categories': Category.objects.filter(is_active=True),
        'subcategories': SubCategory.objects.all(),
        'nested_categories': NestedCategory.objects.all(), 
        'materials': Material.objects.all(),
        'brands': Brand.objects.all(),
    }
    return render(request, 'admin/product_update.html', context)
@staff_member_required(login_url='login')
def delete_product(request, pk):
    get_object_or_404(Product, pk=pk).delete()
    messages.success(request, "Product deleted")
    return redirect('product_list')

@staff_member_required(login_url='login')
def toggle_product_status(request, product_id):
    p = get_object_or_404(Product, id=product_id)
    p.is_active = not p.is_active
    p.save()
    return redirect('product_list')


# ==========================================
# 4. USER & BRAND MANAGEMENT
# ==========================================

@never_cache
@staff_member_required(login_url='login')
def user_list(request):
    search_query = request.GET.get('search', '')
    sort_filter = request.GET.get('status', '')
    users = User.objects.all().order_by('-date_joined')

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query)
        )

    if sort_filter == 'active':
        users = users.filter(is_active=True)
    elif sort_filter == 'blocked':
        users = users.filter(is_active=False)

    return render(request, 'admin/user_list.html', {
        'users': users, 
        'search_query': search_query,
        'sort_filter': sort_filter
    })

@staff_member_required(login_url='login')
def toggle_user_status(request, user_id):
    customer = get_object_or_404(User, id=user_id)
    if not customer.is_superuser:
        customer.is_active = not customer.is_active
        customer.save()
    return redirect('user_list')

@staff_member_required(login_url='login')
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if not user.is_superuser: user.delete()
    return redirect('user_list')

@staff_member_required(login_url='login')
def brand_list(request):
    search_query = request.GET.get('search', '')
    brands = Brand.objects.all().order_by('-id')
    
    if search_query:
        brands = brands.filter(name__icontains=search_query)

    if request.method == "POST":
        brand_name = request.POST.get('brand_name', '').strip()
        brand_logo = request.FILES.get('brand_logo') 

        if brand_name:
            if Brand.objects.filter(name__iexact=brand_name).exists():
                messages.warning(request, f"Brand '{brand_name}' already exists!")
            else:
                Brand.objects.create(
                    name=brand_name, 
                    logo=brand_logo
                )
                messages.success(request, "Brand added successfully!")
        else:
            messages.error(request, "Brand name is required!")
            
        return redirect('brand_list')
        
    return render(request, 'admin/brand_list.html', {
        'brands': brands, 
        'search_query': search_query
    })
@staff_member_required(login_url='login')
def delete_brand(request, brand_id):
    get_object_or_404(Brand, id=brand_id).delete()
    return redirect('brand_list')


# ==========================================
# 5. ORDERS & STATUS UPDATES (With Email Notification)
# ==========================================

@never_cache
@staff_member_required(login_url='login')
def admin_order_list(request):
    search_query = request.GET.get('search', '')
    orders = Order.objects.all().order_by('-created_at')
    if search_query:
        orders = orders.filter(Q(id__icontains=search_query) | Q(user__username__icontains=search_query))
    return render(request, 'admin/admin_orders.html', {'orders': orders})
@staff_member_required(login_url='login')
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        old_status = order.status 

        if old_status in ['Returned', 'Cancelled']:
             messages.warning(request, "This order is already finalized and cannot be changed.")
             return redirect('admin_orders')

        try:
            with transaction.atomic():
                refund_statuses = ['Returned', 'Cancelled']
                
                if new_status in refund_statuses and old_status not in refund_statuses:
                    should_refund = False
                    
                    
                    if new_status == 'Returned':
                        should_refund = True
                    elif new_status == 'Cancelled' and (order.is_paid or order.payment_method != 'COD'):
                        should_refund = True

                    if should_refund:
                        
                        active_items = order.order_items.filter(status='Placed')
                        refund_amount = sum(item.sub_total() for item in active_items)

                        if refund_amount > 0:
                            wallet, _ = Wallet.objects.get_or_create(user=order.user)
                            wallet.balance += refund_amount
                            wallet.save()

                            WalletTransaction.objects.create(
                                wallet=wallet,
                                amount=refund_amount,
                                transaction_type='CREDIT',
                                description=f"Full Order {new_status} refund for Order #{order.id}"
                            )
                            order.is_paid = True 
                            messages.success(request, f"Refund of ₹{refund_amount} added to user wallet.")

                   
                    for item in order.order_items.filter(status='Placed'):
                        if item.product: 
                            if item.variant:
                                item.variant.stock += item.quantity
                                item.variant.save()
                            else:
                                item.product.stock += item.quantity
                                item.product.save()
                        
                        item.status = new_status 
                        item.save()

                order.status = new_status
                order.save()
                messages.success(request, f"Order status updated to {new_status}.")

        except Exception as e:
            messages.error(request, f"Error occurred: {str(e)}")
            
    return redirect('admin_orders')
@staff_member_required(login_url='login')
def return_requests_list(request): 
    returns = Order.objects.filter(status='Return Requested').order_by('-created_at')
    return render(request, 'admin/return_requests.html', {'returns': returns})
# ==========================================
# 6. BANNERS, REVIEWS & WISHLIST
# ==========================================

@staff_member_required(login_url='login')
def banner_list(request):
    return render(request, 'admin/banner_list.html', {'carousels': Carousel.objects.all(), 'offers': OfferBanner.objects.all()})

@staff_member_required(login_url='login')
def admin_reviews(request):
    return render(request, 'admin/reviews.html', {'reviews': Review.objects.all().order_by('-created_at')})

@staff_member_required(login_url='login')
def delete_review(request, review_id):
    get_object_or_404(Review, id=review_id).delete()
    return redirect('admin_reviews')

@staff_member_required(login_url='login')
def admin_wishlist_view(request):
    return render(request, 'admin/wishlist.html', {'wishlists': Wishlist.objects.all()})


# ==========================================
# 7. CAROUSEL & BANNER MANAGEMENT (ADD, EDIT, DELETE)
# ==========================================

@staff_member_required(login_url='login')
def add_carousel(request):
    if request.method == 'POST':
        form = CarouselForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Carousel slide added successfully!")
            return redirect('banner_list')
    else:
        form = CarouselForm()
    return render(request, 'admin/banner_form.html', {'form': form, 'title': 'Add Carousel Slide'})

@staff_member_required(login_url='login')
def edit_carousel(request, pk):
    item = get_object_or_404(Carousel, pk=pk)
    if request.method == 'POST':
        form = CarouselForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Carousel slide updated successfully!")
            return redirect('banner_list')
    else:
        form = CarouselForm(instance=item)
    return render(request, 'admin/banner_form.html', {'form': form, 'title': 'Edit Carousel'})

@staff_member_required(login_url='login')
def delete_carousel(request, pk):
    item = get_object_or_404(Carousel, pk=pk)
    item.delete()
    messages.success(request, "Carousel slide deleted successfully!")
    return redirect('banner_list')

@staff_member_required(login_url='login')
def add_offer(request):
    if request.method == 'POST':
        form = OfferBannerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "New Offer Banner added successfully!")
            return redirect('banner_list')
    else:
        form = OfferBannerForm()
    return render(request, 'admin/banner_form.html', {'form': form, 'title': 'Add New Offer Banner'})

@staff_member_required(login_url='login')
def edit_offer(request, pk):
    offer = get_object_or_404(OfferBanner, pk=pk)
    if request.method == 'POST':
        form = OfferBannerForm(request.POST, request.FILES, instance=offer)
        if form.is_valid():
            form.save()
            messages.success(request, "Offer banner updated!")
            return redirect('banner_list')
    else:
        form = OfferBannerForm(instance=offer)
    return render(request, 'admin/banner_form.html', {'form': form, 'title': 'Edit Offer Banner'})

@staff_member_required(login_url='login')
def delete_offer(request, pk):
    offer = get_object_or_404(OfferBanner, pk=pk)
    offer.delete()
    messages.success(request, "Offer banner deleted!")
    return redirect('banner_list')

@staff_member_required(login_url='login')
def material_list(request):
    from product.models import Material
    materials = Material.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Material.objects.create(name=name)
            messages.success(request, f"Material '{name}' added successfully!")
            return redirect('category_list')
            
    return render(request, 'admin/category/category_list.html', {'materials': materials})

@staff_member_required(login_url='login')
def update_material(request, pk):
    from product.models import Material
    material = get_object_or_404(Material, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            material.name = name
            material.save()
            messages.success(request, "Material updated successfully!")
            return redirect('material_list')
            
    return render(request, 'admin/category/update_material.html', {'material': material})

@staff_member_required(login_url='login')
def delete_material(request, pk):
    from product.models import Material
    material = get_object_or_404(Material, pk=pk)
    material.delete()
    messages.success(request, "Material deleted!")
    return redirect('material_list')

@staff_member_required(login_url='login')
def add_material(request):
    from product.models import Material
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Material.objects.create(name=name)
            messages.success(request, f"Material '{name}' added successfully!")
            return redirect('material_list') 
            
    return render(request, 'admin/category/material_add.html')



@staff_member_required(login_url='login')
def approve_item_return(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)
    order = item.order
    
    if item.status == 'Return Requested':
        try:
            with transaction.atomic():
                item.status = 'Returned'
                item.save()
                wallet, _ = Wallet.objects.get_or_create(user=order.user)
                refund_amount = item.sub_total()
                wallet.balance += refund_amount
                wallet.save()

                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=refund_amount,
                    transaction_type='CREDIT',
                    description=f"Refund: Returned {item.product_name} (Order #{order.id})"
                )

               
                if item.variant:
                    item.variant.stock += item.quantity
                    item.variant.save()
                elif item.product: 
                    item.product.stock += item.quantity
                    item.product.save()

                
                active_items = order.order_items.exclude(status__in=['Returned', 'Cancelled'])
                if not active_items.exists():
                    order.status = 'Returned'
                    order.save()

                messages.success(request, f"Refund of ₹{refund_amount} processed successfully.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    else:
        messages.warning(request, "This item is not eligible for return approval.")
    return redirect('admin_order_detail', order_id=order.id)


@staff_member_required(login_url='login')
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'admin/admin_order_detail.html', {'order': order})

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

def cancel_item_admin(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)
    order = item.order

    if item.status != 'Cancelled':
       
        item.status = 'Cancelled'
        item.save()

        
        order.total_amount -= item.sub_total
        order.save()
        
        messages.success(request, f"Item {item.product_name} has been cancelled.")
    else:
        messages.warning(request, "This item is already cancelled.")
    
   
    return redirect('admin_order_detail', order_id=order.id)