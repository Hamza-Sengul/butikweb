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

    # Oturumda daha önce karıştırılmış bir liste olup olmadığını kontrol et
    if 'shuffled_products' not in request.session:
        product_list = Product.objects.all()  # Bu noktada QuerySet olarak bırakın
        product_ids = list(product_list.values_list('id', flat=True))
        random.shuffle(product_ids)
        # Karıştırılmış listeyi oturuma kaydet
        request.session['shuffled_products'] = product_ids
    else:
        # Oturumda kayıtlı olan karıştırılmış listeyi kullan
        shuffled_product_ids = request.session['shuffled_products']
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(shuffled_product_ids)])
        product_list = Product.objects.filter(pk__in=shuffled_product_ids).order_by(preserved)

    # Ortalama yıldız puanlarını hesaplayalım
    product_list = product_list.annotate(avg_rating=Avg('comments__rating'))

    # Filtering by category
    selected_category = request.GET.get('category')
    if selected_category:
        product_list = product_list.filter(category__id=selected_category)

    # Filtering by price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price and max_price:
        product_list = product_list.filter(price__gte=min_price, price__lte=max_price)

    # Sorting
    sort_by = request.GET.get('sort_by')
    if sort_by == 'price_asc':
        product_list = product_list.order_by('price')
    elif sort_by == 'price_desc':
        product_list = product_list.order_by('-price')
    elif sort_by == 'name_asc':
        product_list = product_list.order_by('name')
    elif sort_by == 'name_desc':
        product_list = product_list.order_by('-name')

    # Pagination
    paginator = Paginator(product_list, 20)  # Show 20 products per page
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    # Check for favorite products if the user is authenticated
    user_favorites = []
    cart_item_count = 0
    if request.user.is_authenticated:
        user_favorites = Favorite.objects.filter(user=request.user).values_list('product_id', flat=True)
        
        # Get the cart item count
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
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.order_by('?')[:6]  # Rastgele 6 ürün

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # Aynı email adresiyle aynı ürün için daha önce yorum yapılmış mı kontrol et
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
            print(form.errors)  # Form hatalarını konsola yazdır
    else:
        form = CommentForm()

    comments = product.comments.all()

    return render(request, 'product_detail.html', {
        'product': product,
        'related_products': related_products,
        'form': form,
        'comments': comments,
    })
def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    categories = Category.objects.all()  # To display in the navbar or footer

    return render(request, 'category_products.html', {
        'category': category,
        'products': products,
        'categories': categories,
    })
