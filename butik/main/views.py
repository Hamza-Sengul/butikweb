from django.shortcuts import render, get_list_or_404, get_object_or_404
from .models import Category, Product
from django.core.paginator import Paginator
from django.db.models import Count
import random
from account_app.models import Favorite, Cart, CartItem
from django.db.models import Case, When

def index(request):
    categories = Category.objects.all()

    # Oturumda daha önce karıştırılmış bir liste olup olmadığını kontrol et
    if 'shuffled_products' not in request.session:
        product_list = list(Product.objects.all())
        random.shuffle(product_list)
        # Karıştırılmış listeyi oturuma kaydet
        request.session['shuffled_products'] = [product.id for product in product_list]
    else:
        # Oturumda kayıtlı olan karıştırılmış listeyi kullan
        shuffled_product_ids = request.session['shuffled_products']
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(shuffled_product_ids)])
        product_list = Product.objects.filter(pk__in=shuffled_product_ids).order_by(preserved)

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
        'cart_item_count': cart_item_count,  # Pass the cart item count to the template
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {'product': product})


def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    categories = Category.objects.all()  # To display in the navbar or footer

    return render(request, 'category_products.html', {
        'category': category,
        'products': products,
        'categories': categories,
    })