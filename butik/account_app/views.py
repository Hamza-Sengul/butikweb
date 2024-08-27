from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
import random
from django.contrib.auth.decorators import login_required
from .models import Favorite, Product, CartItem, Cart
from django.http import JsonResponse
from django.contrib import messages

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
    favorites = Favorite.objects.filter(user=request.user).select_related('product')
    return render(request, 'account/favorites.html', {'favorites': favorites})

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
    cart = get_object_or_404(Cart, user=request.user)
    return render(request, 'account/cart_detail.html', {'cart': cart})

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

