from django.shortcuts import render, redirect, get_object_or_404
from .models import Category, Product, Comment
from django.core.paginator import Paginator
from django.db.models import Count
import random
from account_app.models import Favorite, Cart, CartItem
from django.db.models import Avg, Case, When
from .forms import CommentForm
from django.contrib import messages

def index(request):
    categories = Category.objects.all()

    
    if 'shuffled_products' not in request.session:
        product_list = Product.objects.all()  
        product_ids = list(product_list.values_list('id', flat=True))
        random.shuffle(product_ids)
   
        request.session['shuffled_products'] = product_ids
    else:
      
        shuffled_product_ids = request.session['shuffled_products']
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(shuffled_product_ids)])
        product_list = Product.objects.filter(pk__in=shuffled_product_ids).order_by(preserved)

   
    product_list = product_list.annotate(avg_rating=Avg('comments__rating'))

   
    selected_category = request.GET.get('category')
    if selected_category:
        product_list = product_list.filter(category__id=selected_category)

 
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price and max_price:
        product_list = product_list.filter(price__gte=min_price, price__lte=max_price)

  
    sort_by = request.GET.get('sort_by')
    if sort_by == 'price_asc':
        product_list = product_list.order_by('price')
    elif sort_by == 'price_desc':
        product_list = product_list.order_by('-price')
    elif sort_by == 'name_asc':
        product_list = product_list.order_by('name')
    elif sort_by == 'name_desc':
        product_list = product_list.order_by('-name')


    paginator = Paginator(product_list, 20) 
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    
    user_favorites = []
    cart_item_count = 0
    if request.user.is_authenticated:
        user_favorites = Favorite.objects.filter(user=request.user).values_list('product_id', flat=True)
        
       
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_item_count = cart.items.count()

    return render(request, 'index.html', {
        'categories': categories,
        'products': products,
        'selected_category': selected_category,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'user_favorites': user_favorites,
        'cart_item_count': cart_item_count,
    })

def product_detail(request, product_id):
    categories = Category.objects.all()
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.order_by('?')[:6] 

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
        
            existing_comment = Comment.objects.filter(product=product, email=email).exists()
            
            if existing_comment:
                messages.error(request, 'Bu email adresi ile bu ürüne zaten yorum yaptınız.')
            else:
                comment = form.save(commit=False)
                comment.product = product
                comment.save()
                messages.success(request, 'Yorumunuz başarıyla eklendi.')
                return redirect('product_detail', product_id=product.id)
        else:
            print(form.errors)  
    else:
        form = CommentForm()

    comments = product.comments.all()

    return render(request, 'product_detail.html', {
        'product': product,
        'related_products': related_products,
        'form': form,
        'comments': comments,
        'categories': categories
    })
def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    categories = Category.objects.all() 

    return render(request, 'category_products.html', {
        'category': category,
        'products': products,
        'categories': categories,
    })


def category_products(request, category_id):
    categories = Category.objects.all()
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category).annotate(avg_rating=Avg('comments__rating'))

   
    paginator = Paginator(products, 20)  
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    user_favorites = []
    cart_item_count = 0
    if request.user.is_authenticated:
        user_favorites = Favorite.objects.filter(user=request.user).values_list('product_id', flat=True)
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_item_count = cart.items.count()

    return render(request, 'category_products.html', {
        'category': category,
        'products': products,
        'user_favorites': user_favorites,
        'cart_item_count': cart_item_count,
        'categories': categories
    })
