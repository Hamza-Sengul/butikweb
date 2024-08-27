from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
import random
from django.contrib.auth.decorators import login_required
from .models import Favorite, Product, CartItem, Cart, Profile, Order
from django.http import JsonResponse
from django.contrib import messages
from main.models import Category, Comment
from .forms import UserUpdateForm, ProfileUpdateForm, CustomPasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.db.models.signals import post_save
from django.dispatch import receiver

def login_request(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        try:
            user = User.objects.get(email=email)
            username = user.username
        except User.DoesNotExist:
            return render(request, "account/login.html", {"error": "Email veya parola yanlış"})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # Ensure the user has a profile
            Profile.objects.get_or_create(user=user)
            return redirect('home')
        else:
            return render(request, "account/login.html", {"error": "Email veya parola yanlış"})
    return render(request, "account/login.html")

# def register_request(request):
#     if request.user.is_authenticated:
#         return redirect("home")
#     if request.method == "POST":
#         username = request.POST["username"]
#         email = request.POST["email"]
#         firstname = request.POST["firstname"]
#         lastname = request.POST["lastname"]
#         password = request.POST["password"]
#         repassword = request.POST["repassword"]

#         if password == repassword:
#             if User.objects.filter(username=username).exists():
#                 return render(request, "account/register.html", {"error":"username zaten var"})

#             else:
#                 if User.objects.filter(email=email).exists():
#                     return render(request, "account/register.html", {"error":"email zaten var"})
#                 else:
#                     user = User.objects.create_user(username=username, email=email, first_name=firstname, last_name=lastname, password=password)
#                     user.save()
#                     return redirect('login')
#         else:
#             return render(request, "account/register.html", {"error":"parola eşleşmiyor"})

#     return render(request, "account/register.html")

def register_request(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        firstname = request.POST["firstname"]
        lastname = request.POST["lastname"]
        password = request.POST["password"]
        repassword = request.POST["repassword"]

        if password == repassword:
            if User.objects.filter(username=username).exists():
                return render(request, "account/register.html", {"error":"username zaten var"})
            elif User.objects.filter(email=email).exists():
                return render(request, "account/register.html", {"error":"email zaten var"})
            else:
                verification_code = random.randint(100000, 999999)
                # Store the verification code and user data in the session
                request.session['verification_code'] = verification_code
                request.session['user_data'] = {
                    'username': username,
                    'email': email,
                    'firstname': firstname,
                    'lastname': lastname,
                    'password': password
                }
                
                # Send the verification code to the user's email
                send_mail(
                    'Email Verification',
                    f'Your verification code is {verification_code}',
                    'your_email@example.com', # Replace with your email
                    [email],
                    fail_silently=False,
                )

                return redirect('verify_email')
        else:
            return render(request, "account/register.html", {"error":"parola eşleşmiyor"})

    return render(request, "account/register.html")


def verify_email(request):
    if request.method == "POST":
        verification_code = request.POST.get('verification_code')
        if verification_code == str(request.session.get('verification_code')):
            user_data = request.session.get('user_data')
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['firstname'],
                last_name=user_data['lastname'],
                password=user_data['password']
            )
            user.save()
            # Clear the session data after successful registration
            del request.session['verification_code']
            del request.session['user_data']
            return redirect('login')
        else:
            return render(request, "account/verify_email.html", {"error": "Doğrulama kodu geçersiz"})
    return render(request, "account/verify_email.html")


def logout_request(request):
    logout(request)
    return redirect("home")


@login_required
def add_to_favorites(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        favorite.delete()
        return JsonResponse({'status': 'removed', 'message': 'Ürün favorilerden çıkarıldı'})
    
    return JsonResponse({'status': 'added', 'message': 'Ürün favorilere eklendi'})

@login_required
def favorites(request):
    categories = Category.objects.all()
    favorites = Favorite.objects.filter(user=request.user).select_related('product')
    return render(request, 'account/favorites.html', {'favorites': favorites, 'categories': categories})

@login_required
def remove_from_favorites(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    favorite = get_object_or_404(Favorite, user=request.user, product=product)
    favorite.delete()
    return redirect('favorites')  # Redirect to favorites page after removing



@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Find or create the cart item and increment its quantity
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += 1
    
    cart_item.save()

    cart_item_count = cart.items.count()

    return JsonResponse({
        'cart_item_count': cart_item_count,
        'message': 'Ürün sepete eklendi'
    })


@login_required
def cart_detail(request):
    categories = Category.objects.all()
    cart, created = Cart.objects.get_or_create(user=request.user)
    profile, created = Profile.objects.get_or_create(user=request.user)

    address_form = ProfileUpdateForm(instance=profile)

    return render(request, 'account/cart_detail.html', {
        'cart': cart,
        'categories': categories,
        'address_form': address_form,
        'profile': profile,
    })
@login_required
def save_address(request):
    if request.method == 'POST':
        profile, created = Profile.objects.get_or_create(user=request.user)
        address_form = ProfileUpdateForm(request.POST, instance=profile)
        
        if address_form.is_valid():
            address_form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': address_form.errors})

    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def remove_from_cart(request, product_id):
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, cart=cart, product__id=product_id)
    cart_item.delete()
    return redirect('cart_detail')


@login_required
def update_cart_item(request, product_id):
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, cart=cart, product__id=product_id)

    if request.method == "POST":
        action = request.POST.get('action')

        if action == "increase":
            cart_item.quantity += 1
        elif action == "decrease":
            cart_item.quantity -= 1
            if cart_item.quantity <= 0:
                cart_item.delete()
                return redirect('cart_detail')

        cart_item.save()

    return redirect('cart_detail')



@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@login_required
def account_view(request):
    # Ensure the user has a profile
    profile, created = Profile.objects.get_or_create(user=request.user)

    # Determine which tab is active
    active_tab = request.GET.get('tab', 'orders')  # Default tab is 'orders'

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=profile)
        password_form = CustomPasswordChangeForm(request.user, request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('account')
        elif password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Important to keep the user logged in after password change
            messages.success(request, 'Your password was successfully updated!')
            return redirect('account')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)
        password_form = CustomPasswordChangeForm(request.user)

    # Fetch orders and comments based on the active tab
    if active_tab == 'reviews':
        comments = Comment.objects.filter(email=request.user.email)
        orders = None
    else:
        orders = Order.objects.filter(user=request.user)  # Adjust this query to your model structure
        comments = None

    return render(request, 'account/account.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form,
        'active_tab': active_tab,
        'orders': orders,
        'comments': comments,
    })


@login_required
def checkout_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'address_saved'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors})
    return redirect('cart_detail')

@login_required
def confirm_order_view(request):
    if request.method == 'POST':
        # Burada sipariş oluşturma ve ödeme işlemleri yapılır
        return JsonResponse({'status': 'order_confirmed'})
    return redirect('cart_detail')