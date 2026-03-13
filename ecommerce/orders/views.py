import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.db import transaction
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .models import Cart, CartItem, Order, OrderItem
from product.models import Product,ProductVariant
from accounts.models import Address, Wallet, WalletTransaction
# Stripe API Key
stripe.api_key = settings.STRIPE_SECRET_KEY

# ==========================================
# 1. CART MANAGEMENT
# ==========================================

@never_cache
@login_required(login_url='login')
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cart_items.all()
    
    for item in cart_items:
        target_stock = item.variant.stock if item.variant else item.product.stock
        if item.quantity > target_stock:
            item.quantity = target_stock
            item.save()
            messages.info(request, f"Stock updated for {item.product.name}.")
            
    return render(request, 'orders/cart.html', {'cart': cart, 'cart_items': cart_items})

@login_required(login_url='login')
def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        variant_id = request.POST.get('variant_id') 
        variant = None

        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id)
            stock = variant.stock
        else:
            stock = product.stock

        if stock < 1:
            messages.warning(request, f"Sorry, {product.name} is out of stock.")
            return redirect(request.META.get('HTTP_REFERER', 'category_product_list'))

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, variant=variant
        )
        
        if not created:
            if cart_item.quantity < stock:
                cart_item.quantity += 1
                cart_item.save()
            else:
                messages.warning(request, "Maximum stock reached.")
        else:
            cart_item.quantity = 1
            cart_item.save()
            
        return redirect('cart_view')
    return redirect('category_product_list')

@login_required
def update_cart(request, item_id, action):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    available_stock = cart_item.variant.stock if cart_item.variant else cart_item.product.stock
    
    if action == 'add':
        if cart_item.quantity < available_stock:
            cart_item.quantity += 1
            cart_item.save()
        else:
            messages.warning(request, "Insufficient stock!")
    elif action == 'remove':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('cart_view')

@login_required(login_url='login')
def remove_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('cart_view')

# ==========================================
# 2. CHECKOUT & ORDER (COD Case)
# ==========================================

@never_cache
@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.cart_items.all()
        saved_addresses = Address.objects.filter(user=request.user)
    except Cart.DoesNotExist:
        return redirect('cart_view')
    
    if not cart_items:
        return redirect('cart_view')

    if request.method == 'POST':
        # Stock validation
        for item in cart_items:
            stock_check = item.variant.stock if item.variant else item.product.stock
            if stock_check < item.quantity:
                messages.error(request, f"Sorry, {item.product.name} is out of stock.")
                return redirect('cart_view')

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user, 
                total_amount=cart.total_price(),
                payment_method='COD',
                status='Confirmed'
            )

            for item in cart_items:
                current_price = item.variant.price if item.variant else item.product.price
                OrderItem.objects.create(
                    order=order, product=item.product, variant=item.variant,
                    quantity=item.quantity, price=current_price
                )
                
                # Stock Deduction
                if item.variant:
                    item.variant.stock -= item.quantity
                    item.variant.save()
                else:
                    item.product.stock -= item.quantity
                    item.product.save()
            
            cart_items.delete()
            
        messages.success(request, "Order placed successfully!")
        return redirect('order_success_view', order_id=order.id)

    return render(request, 'orders/checkout.html', {'cart': cart, 'cart_items': cart_items, 'saved_addresses': saved_addresses})

# ==========================================
# 3. STRIPE ONLINE PAYMENT
# ==========================================

@login_required
def create_checkout_session(request):
    if request.method == 'POST':
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.cart_items.all()
            if not cart_items: return redirect('cart_view')

            f_name = request.POST.get('full_name')
            addr = request.POST.get('address')
            cty = request.POST.get('city')
            pin = request.POST.get('pincode')
            ph = request.POST.get('phone')

            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user, full_name=f_name, address=addr,
                    city=cty, pincode=pin, phone=ph,
                    total_amount=cart.total_price(), payment_method='Online', status='Pending'
                )

                for item in cart_items:
                    price = item.variant.price if item.variant else item.product.price
                    OrderItem.objects.create(
                        order=order, product=item.product, variant=item.variant,
                        quantity=item.quantity, price=price
                    )

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'inr',
                        'product_data': {'name': f'Order #{order.id}'},
                        'unit_amount': int(order.total_amount * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                metadata={'order_id': order.id},
                success_url=request.build_absolute_uri('/orders/payment-success/') + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri('/orders/payment-cancel/'),
            )
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}")
    return redirect('checkout')

@never_cache
@login_required
def payment_success(request):
    session_id = request.GET.get('session_id')
    order = None
    
    if session_id:
        try:
           
            session = stripe.checkout.Session.retrieve(session_id)
            order_id = session.metadata.get('order_id')
            
            if order_id:
               
                order = get_object_or_404(Order, id=order_id)
                
                
                if not order.is_paid:
                    with transaction.atomic():
                       
                        order.is_paid = True
                        order.status = 'Confirmed'
                        order.payment_method = 'Online' 
                        order.save()

                        
                        for item in order.order_items.all():
                            if item.variant:
                                item.variant.stock -= item.quantity
                                item.variant.save()
                            else:
                                item.product.stock -= item.quantity
                                item.product.save()

                        
                        from .models import CartItem 
                        CartItem.objects.filter(cart__user=order.user).delete()
                        
                        messages.success(request, f"Payment successful! Your Order #{order.id} is confirmed.")
                else:
                    
                    messages.info(request, "This order has already been processed.")
            else:
                messages.error(request, "Order ID not found in payment metadata.")
                
        except stripe.error.StripeError as e:
            messages.error(request, f"Stripe Error: {str(e)}")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")
            print(f"Payment Success Logic Error: {e}")
            
    return render(request, 'orders/payment_success.html', {'order': order})

# ==========================================
# 4. ORDER VIEWS & ACTIONS
# ==========================================

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    
    if order.status in ['Pending', 'Confirmed', 'Placed']:
        try:
            with transaction.atomic():
                order.status = 'Cancelled'
                order.save()
                
                
                for item in order.order_items.all():
                    if item.variant:
                        item.variant.stock += item.quantity
                        item.variant.save()
                    else:
                        item.product.stock += item.quantity
                        item.product.save()

               
                if order.is_paid or order.payment_method != 'COD':
                    wallet, created = Wallet.objects.get_or_create(user=request.user)
                    wallet.balance += order.total_amount
                    wallet.save()

                    
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=order.total_amount,
                        transaction_type='CREDIT',
                        description=f"Refund for Cancelled Order #{order.id}"
                    )
                    messages.success(request, f"Order cancelled. ₹{order.total_amount} refunded to your wallet.")
                else:
                    messages.success(request, "Order cancelled successfully.")

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    else:
        messages.error(request, "This order cannot be cancelled at this stage.")

    return redirect('order_list')

@login_required
def return_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'Delivered':
        return_limit = timezone.now() - timedelta(days=7)
        if order.created_at >= return_limit:
            if request.method == 'POST':
                order.status = 'Return Requested'
                order.save()
                messages.success(request, "Return request submitted.")
                return redirect('order_list')
            return render(request, 'orders/return_order_form.html', {'order': order})
    messages.error(request, "Return period expired or not delivered.")
    return redirect('order_list')

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('order_items__product'), id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required
def order_success_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_success.html', {'order': order})

def payment_cancel(request):
    return render(request, 'orders/payment_cancel.html')