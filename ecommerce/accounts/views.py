import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from orders.models  import Cart,OrderItem,Order,CartItem
from .models import UserProfile, Address, OTP, Wallet ,WalletTransaction
from .forms import SignupForm, OTPForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from django.views.decorators.cache import never_cache
from django.db import transaction
# --- SIGNUP VIEW ---
def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            full_name = form.cleaned_data['username']
            email = form.cleaned_data['email']
            p1 = form.cleaned_data['password']
            p2 = form.cleaned_data['confirm_password']

            if p1 != p2:
                messages.error(request, "Passwords do not match!")
                return render(request, 'signup.html', {'form': form})

            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                if existing_user.is_active:
                    messages.error(request, "Email already exists!")
                    return render(request, 'signup.html', {'form': form})
                else:
                    existing_user.delete()
           

            user = User.objects.create_user(username=email, email=email, password=p1)
            user.first_name = full_name
            user.is_active = False 
            user.save()

            otp_code = str(random.randint(100000, 999999))
            OTP.objects.create(user=user, code=otp_code)
            print(otp_code)
            
            try:
                send_mail(
                    'Your OTP Code',
                    f'Your OTP is {otp_code}. It will expire in 2 minutes.',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False
                )
                request.session['email'] = email
                return redirect('verify_otp')
            except Exception as e:
                user.delete() 
                messages.error(request, "Failed to send email. Check connection.")
                return render(request, 'signup.html', {'form': form})
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

# --- OTP VERIFICATION ---
def otp_verify_view(request):
    email = request.session.get('email')
    if not email:
        messages.error(request, "Session expired. Please signup again.")
        return redirect('signup')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return redirect('signup')

    if request.method == "POST":
        form = OTPForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            otp_obj = OTP.objects.filter(user=user, code=entered_otp).first()

            if otp_obj:
                if otp_obj.is_expired():
                    otp_obj.delete()
                    messages.error(request, "OTP expired. Please resend.")
                    return render(request, 'otp_verify.html', {'form': form, 'email': email})

                user.is_active = True
                user.save()

              
                UserProfile.objects.get_or_create(user=user)
                Wallet.objects.get_or_create(user=user) 

                
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                otp_obj.delete()
                request.session.pop('email', None)
                messages.success(request, f"Welcome {user.first_name}!")
                return redirect('home')
            else:
                messages.error(request, "Invalid OTP")
    else:
        form = OTPForm()
    return render(request, 'otp_verify.html', {'form': form, 'email': email})


# --- RESEND OTP ---
def resend_otp_view(request):
    email = request.session.get('email') or request.session.get('reset_email')
    if not email:
        messages.error(request, "Session expired.")
        return redirect('signup')

    user = User.objects.filter(email=email).first()
    if user:
        OTP.objects.filter(user=user).delete()
        otp_code = str(random.randint(100000, 999999))
        OTP.objects.create(user=user, code=otp_code)

        send_mail(
            'Your New OTP Code',
            f'Your new OTP is {otp_code}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False
        )
        messages.success(request, "A new OTP has been sent.")
    
    if request.session.get('reset_email'):
        return redirect('reset_password_otp')
    return redirect('verify_otp')


# --- LOGIN ---
@never_cache
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('home')

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                if not user.is_active:
                    messages.warning(request, "Please verify your email first.")
                    request.session['email'] = email
                    return redirect('verify_otp')
                
                UserProfile.objects.get_or_create(user=user)
                Wallet.objects.get_or_create(user=user)
                
                login(request, user)
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                if user.is_staff or user.is_superuser:
                    return redirect('admin_dashboard')
                return redirect('home')
            else:
                messages.error(request, "Invalid credentials")
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})
# --- FORGOT PASSWORD ---
def forgot_password_view(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                OTP.objects.filter(user=user).delete()
                otp_code = str(random.randint(100000, 999999))
                OTP.objects.create(user=user, code=otp_code)

                send_mail(
                    'Reset Password OTP',
                    f'Your OTP is {otp_code}. Valid for 2 minutes.',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False
                )
                request.session['reset_email'] = email
                messages.success(request, "OTP sent to your email")
                return redirect('reset_password_otp')
            except User.DoesNotExist:
                messages.error(request, "No user found with this email.")
    else:
        form = ForgotPasswordForm()
    return render(request, 'forgot_password.html', {'form': form})

def reset_password_otp_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')

    if request.method == "POST":
        form = OTPForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            user = User.objects.get(email=email)
            otp_obj = OTP.objects.filter(user=user, code=entered_otp).first()

            if otp_obj and not otp_obj.is_expired():
                request.session['allow_reset'] = True
                otp_obj.delete()
                return redirect('reset_password')
            else:
                messages.error(request, "Invalid or Expired OTP")
    else:
        form = OTPForm()
    return render(request, 'reset_password_otp.html', {'form': form, 'email': email})

def reset_password_view(request):
    email = request.session.get('reset_email')
    if not email or not request.session.get('allow_reset'):
        return redirect('forgot_password')

    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
            request.session.pop('allow_reset', None)
            request.session.pop('reset_email', None)
            messages.success(request, "Password updated!")
            return redirect('login')
    else:
        form = ResetPasswordForm()
    return render(request, 'reset_password.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# --- PROFILE & ADDRESS MANAGEMENT ---

@never_cache
@login_required
def profile_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    addresses = Address.objects.filter(user=request.user)
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    context = {
        'user_profile': user_profile, 
        'addresses': addresses,
        'wallet': wallet  
    }
    
    return render(request, 'profile.html', context)
@login_required
def edit_profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name')
        request.user.email = request.POST.get('email')
        request.user.save()

        user_profile.phone = request.POST.get('phone')
        user_profile.save()
        messages.success(request, "Profile updated!")
        return redirect('profile')
    return render(request, 'edit_profile.html', {'user_profile': user_profile})

@login_required
def add_address(request):
    if request.method == 'POST':
        Address.objects.create(
            user=request.user,
            full_name=request.POST.get('full_name'),
            street_address=request.POST.get('street_address'), 
            city=request.POST.get('city'),
            pincode=request.POST.get('pincode'),
            phone_number=request.POST.get('phone'), 
            landmark=request.POST.get('landmark') 
        )
        messages.success(request, "Address added successfully!")
        return redirect('profile')
    return render(request, 'add_address.html')

@login_required
def update_address_view(request, id):
    address = get_object_or_404(Address, id=id, user=request.user)
    if request.method == 'POST':
        address.full_name = request.POST.get('full_name')
        address.street_address = request.POST.get('street_address') 
        address.city = request.POST.get('city')
        address.pincode = request.POST.get('pincode')
        address.phone_number = request.POST.get('phone') 
        address.landmark = request.POST.get('landmark')
        address.save()
        messages.success(request, "Address updated!")
        return redirect('profile')
    return render(request, 'update_address.html', {'address': address})

@login_required
def delete_address(request, id):
    address = get_object_or_404(Address, id=id, user=request.user)
    address.delete()
    messages.success(request, "Address deleted!")
    return redirect('profile')


# --- WALLET VIEW ---

@never_cache
@login_required
def wallet_view(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')
    return render(request, 'wallet.html', {
        'wallet': wallet,
        'transactions': transactions
    })

@login_required
def wallet_payment(request):
    if request.method == 'POST':
        user = request.user
        cart = Cart.objects.get(user=user)
        cart_items = CartItem.objects.filter(cart=cart)
        
        
        total_amount = sum(item.product.get_display_price() * item.quantity for item in cart_items)

        try:
            with transaction.atomic():
                wallet = Wallet.objects.get(user=user)
                if wallet.balance >= total_amount:
                    wallet.balance -= total_amount
                    wallet.save()

                   
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=total_amount,
                        transaction_type='DEBIT',
                        description="Payment for Order"
                    )

                    
                    order = Order.objects.create(
                        user=user,
                        full_name=request.POST.get('full_name'),
                        address=request.POST.get('address'),
                        city=request.POST.get('city'),
                        pincode=request.POST.get('pincode'),
                        phone=request.POST.get('phone'),
                        total_amount=total_amount, 
                        payment_method='Wallet',
                        is_paid=True,
                        status='Confirmed'
                    )

                    for item in cart_items:
                        
                        current_price = item.product.get_display_price()
                        
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            variant=item.variant, 
                            quantity=item.quantity,
                            price=current_price, 
                            product_name=item.product.name,
                            product_image=item.product.image if item.product.image else None
                        )
                        if item.variant:
                            item.variant.stock -= item.quantity
                            item.variant.save()
                        else:
                            item.product.stock -= item.quantity
                            item.product.save()

                    cart_items.delete()
                    messages.success(request, "Order placed successfully using Wallet!")
                    return redirect('order_success_view', order_id=order.id)
                else:
                    messages.error(request, "Insufficient Wallet Balance.")
                    return redirect('checkout')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('checkout')

    return redirect('cart_view')
def contact_view(request):
    return render(request, 'contact.html')