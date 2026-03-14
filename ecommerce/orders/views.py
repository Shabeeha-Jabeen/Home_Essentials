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
import os
from django.core.files.base import ContentFile
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
            messages.info(request, f"Stock updated for {item.product.name} due to availability.")
            
    return render(request, 'orders/cart.html', {'cart': cart, 'cart_items': cart_items})

@login_required(login_url='login')
def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        variant_id = request.POST.get('variant_id') 
        variant = None

        stock = variant.stock if variant_id and (variant := get_object_or_404(ProductVariant, id=variant_id)) else product.stock

        if stock < 1:
            messages.warning(request, f"Sorry, {product.name} is out of stock.")
            return redirect(request.META.get('HTTP_REFERER', 'category_product_list'))

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, variant=variant)
        
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
    get_object_or_404(CartItem, id=item_id, cart__user=request.user).delete()
    return redirect('cart_view')

# ==========================================
# 2. CHECKOUT & ORDER (COD & ONLINE)
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

    delivery_charge = 31 
    product_total = sum(item.sub_total for item in cart_items)
    grand_total = product_total + delivery_charge

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'COD')
        full_name = request.POST.get('full_name')
        address_text = request.POST.get('address') 
        city = request.POST.get('city')
        pincode = request.POST.get('pincode')
        phone = request.POST.get('phone')

        try:
            with transaction.atomic():
                is_paid = False
                if payment_method == 'WALLET':
                    wallet = getattr(request.user, 'wallet', None)
                    if not wallet or wallet.balance < grand_total:
                        messages.error(request, "Insufficient wallet balance!")
                        return redirect('checkout')
                    
                    wallet.balance -= grand_total
                    wallet.save()
                    is_paid = True
                order = Order.objects.create(
                    user=request.user, 
                    total_amount=grand_total, 
                    payment_method=payment_method,
                    full_name=full_name,
                    address=address_text,
                    city=city,
                    pincode=pincode,
                    phone=phone,
                    is_paid=is_paid,
                    status='Confirmed'
                )

                for item in cart_items:
                    current_price = item.product.get_display_price()
                    order_item = OrderItem.objects.create(
                        order=order, 
                        product=item.product, 
                        variant=item.variant,
                        quantity=item.quantity, 
                        price=current_price,
                        product_name=item.product.name,
                        variant_name=item.variant.name if item.variant else None,
                    )

                    if item.product.image:
                        image_name = os.path.basename(item.product.image.name)
                        try:
                            order_item.product_image.save(image_name, item.product.image, save=True)
                        except Exception as img_err:
                            print(f"Image Save Error: {img_err}")
                    if item.variant:
                        item.variant.stock -= item.quantity
                        item.variant.save()
                    else:
                        item.product.stock -= item.quantity
                        item.product.save()
                
                cart_items.delete()
                
            messages.success(request, f"Order placed successfully using {payment_method}!")
            return redirect('order_success_view', order_id=order.id)
            
        except Exception as e:
            print(f"ORDER CREATION ERROR: {str(e)}")
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('checkout')

    context = {
        'cart': cart, 
        'cart_items': cart_items, 
        'saved_addresses': saved_addresses,
        'product_total': product_total,
        'delivery_charge': delivery_charge,
        'grand_total': grand_total
    }
    return render(request, 'orders/checkout.html', context)
@login_required
def create_checkout_session(request):
    if request.method == 'POST':
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.cart_items.all()
            if not cart_items: return redirect('cart_view')
            current_total = sum(item.product.get_display_price() * item.quantity for item in cart_items)
        
            delivery_charge = 31 
            final_total = current_total + delivery_charge

            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user, 
                    full_name=request.POST.get('full_name'),
                    address=request.POST.get('address'),
                    city=request.POST.get('city'),
                    pincode=request.POST.get('pincode'),
                    phone=request.POST.get('phone'),
                    total_amount=final_total,
                    payment_method='Online', 
                    status='Pending'
                )

                for item in cart_items:
                    OrderItem.objects.create(
                        order=order, product=item.product, variant=item.variant,
                        quantity=item.quantity, price=item.product.get_display_price(),
                        product_name=item.product.name,
                    )
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'inr',
                        'product_data': {'name': f'Order #{order.id} (Includes Delivery)'},
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
# ==========================================
# 3. PAYMENT SUCCESS & CANCEL
# ==========================================

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
                        order.is_paid, order.status, order.payment_method = True, 'Confirmed', 'Online'
                        order.save()
                        for item in order.order_items.all():
                            if item.variant:
                                item.variant.stock -= item.quantity
                                item.variant.save()
                            else:
                                item.product.stock -= item.quantity
                                item.product.save()
                        CartItem.objects.filter(cart__user=order.user).delete()
                        messages.success(request, f"Payment successful! Order #{order.id} is confirmed.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    return render(request, 'orders/payment_success.html', {'order': order})

# ==========================================
# 4. ORDER ACTIONS (CANCEL & RETURN)
# ==========================================

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status in ['Pending', 'Confirmed', 'Placed']:
        try:
            with transaction.atomic():
                for item in order.order_items.all():
                    if item.variant:
                        item.variant.stock += item.quantity
                        item.variant.save()
                    else:
                        item.product.stock += item.quantity
                        item.product.save()

                if order.is_paid or order.payment_method != 'COD':
                    wallet, _ = Wallet.objects.get_or_create(user=request.user)
                    wallet.balance += order.total_amount
                    wallet.save()
                    WalletTransaction.objects.create(
                        wallet=wallet, amount=order.total_amount,
                        transaction_type='CREDIT', description=f"Refund for Order #{order.id}"
                    )
                order.status = 'Cancelled'
                order.save()
                messages.success(request, "Order cancelled and amount refunded.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    return redirect('order_list')

@login_required
def cancel_order_item(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    order = item.order

    if order.status in ['Pending', 'Placed', 'Confirmed'] and item.status == 'Placed':
        with transaction.atomic():
            item.status = 'Cancelled'
            item.save()
            if item.variant:
                item.variant.stock += item.quantity
                item.variant.save()
            else:
                item.product.stock += item.quantity
                item.product.save()
            refund_amount = item.sub_total() 
            if order.is_paid or order.payment_method in ['Online', 'Wallet']:
                wallet, _ = Wallet.objects.get_or_create(user=request.user)
                wallet.balance += refund_amount
                wallet.save()
                WalletTransaction.objects.create(
                    wallet=wallet, amount=refund_amount,
                    transaction_type='CREDIT', description=f"Refund: {item.product_name}"
                )
            active_items = order.order_items.exclude(status='Cancelled')
            order.total_amount = sum(i.sub_total() for i in active_items)
            if not active_items.exists():
                order.status = 'Cancelled'
            order.save()
            messages.success(request, f"{item.product_name} cancelled and refunded.")
    return redirect('order_detail', order_id=order.id)




@login_required
def return_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.is_returnable:
        if request.method == 'POST':
            try:
                
                order.status = 'Return Requested'
                order.save()

                messages.success(request, f"Order #{order.id} return request submitted. Refund will be processed after admin approval.")
                return redirect('order_list')
            
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                return redirect('order_list')

        return render(request, 'orders/return_order_form.html', {'order': order})

    messages.error(request, "Return policy expired for this order.")
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



@login_required
def cancel_order_item(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    order = item.order
    if order.status in ['Pending', 'Placed', 'Confirmed']:
        if item.status == 'Placed':
            with transaction.atomic():
                item.status = 'Cancelled'
                item.save()

                
                if item.variant:
                    item.variant.stock += item.quantity
                    item.variant.save()
                elif item.product:
                    item.product.stock += item.quantity
                    item.product.save()

                
                refund_amount = item.sub_total() 

                if order.is_paid or order.payment_method in ['Online', 'Wallet']:
                    wallet, _ = Wallet.objects.get_or_create(user=request.user)
                    wallet.balance += refund_amount
                    wallet.save()
                    
                   
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=refund_amount,
                        transaction_type='CREDIT',
                        description=f"Refund for cancelled item: {item.product_name}"
                    )

               
                active_items = order.order_items.exclude(status='Cancelled')
                order.total_amount = sum(i.sub_total() for i in active_items)
                
                
                if not active_items.exists():
                    order.status = 'Cancelled'
                
                order.save()
                messages.success(request, f"{item.product_name} has been cancelled and refunded.")
        else:
            messages.warning(request, "This item is already processed or cancelled.")
    else:
        messages.error(request, "This order cannot be cancelled as it is already being shipped.")

    return redirect('order_detail', order_id=order.id)

@login_required
def return_order_item(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    order = item.order

    
    if order.status == 'Delivered' and order.is_returnable:
        if item.status == 'Placed':
            with transaction.atomic():
                item.status = 'Return Requested'
                item.save()
                
            messages.success(request, f"Return request for {item.product_name} submitted.")
        else:
            messages.warning(request, "This item is already returned or cancelled.")
    else:
        messages.error(request, "Return policy expired or order not delivered yet.")

    return redirect('order_detail', order_id=order.id)