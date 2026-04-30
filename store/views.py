from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product, ProductImage, ProductVariant, Order, Cart, CartItem, OrderItem, StoreSettings, SpecialOffer
from django.conf import settings
from urllib.parse import quote
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.utils import timezone
import razorpay
from django.views.decorators.csrf import csrf_exempt
import json

def home(request):
    categories = Category.objects.filter(is_active=True)
    featured_products = Product.objects.filter(is_active=True).order_by('?')[:8]
    active_offer = SpecialOffer.objects.filter(is_active=True).first()
    return render(request, 'home.html', {
        'categories': categories,
        'featured_products': featured_products,
        'active_offer': active_offer,
    })

def product_list(request):
    categories = Category.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True).order_by('?')
    return render(request, 'store/product_list.html', {
        'products': products,
        'categories': categories,
    })

def category_detail(request, slug):
    active_category = get_object_or_404(Category, slug=slug, is_active=True)
    categories = Category.objects.filter(is_active=True)
    products = Product.objects.filter(category=active_category, is_active=True).order_by('?')
    return render(request, 'store/product_list.html', {
        'products': products,
        'categories': categories,
        'active_category': active_category,
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    images = product.images.all()
    variants = product.variants.all()
    related = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id).order_by('?')[:4]
    categories = Category.objects.filter(is_active=True)
    return render(request, 'store/product_detail.html', {
        'product': product,
        'images': images,
        'variants': variants,
        'related': related,
        'categories': categories,
    })

def _merge_cart(request, user):
    session_id = request.session.session_key
    if session_id:
        try:
            session_cart = Cart.objects.get(session_id=session_id)
            user_cart, created = Cart.objects.get_or_create(user=user)
            
            # Move items from session cart to user cart
            for item in session_cart.items.all():
                # Check if product already exists in user cart
                existing_item = user_cart.items.filter(
                    product=item.product, 
                    variant=item.variant
                ).first()
                if existing_item:
                    existing_item.quantity += item.quantity
                    existing_item.save()
                    item.delete()
                else:
                    item.cart = user_cart
                    item.save()
            
            # Delete empty session cart
            session_cart.delete()
        except Cart.DoesNotExist:
            pass

def _get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_id=session_id)
    return cart

def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        size = request.POST.get('size')
        quantity = int(request.POST.get('quantity', 1))
        
        cart = _get_or_create_cart(request)
        # Validation: If product has variants, size must be selected
        if product.variants.exists() and not size:
            messages.error(request, "Please select a size.")
            return redirect('product_detail', slug=product.slug)
            
        if not size: size = 'Free Size'
            
        cart = _get_or_create_cart(request)
        variant = product.variants.filter(size=size).first()
        
        # Stock Validation
        if variant:
            # Calculate total quantity if item already in cart
            current_cart_item = cart.items.filter(product=product, variant=variant).first()
            requested_total = quantity
            if current_cart_item:
                requested_total += current_cart_item.quantity
                
            if requested_total > variant.stock:
                messages.error(request, f"Sorry, only {variant.stock} units of {product.name} ({size}) are available.")
                return redirect('product_detail', slug=product.slug)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
            
        messages.success(request, f"{product.name} added to cart.")
        return redirect('view_cart')
    return redirect('home')

def view_cart(request):
    cart = _get_or_create_cart(request)
    cart_items = cart.items.all()
    categories = Category.objects.filter(is_active=True)
    
    subtotal = cart.get_total()
    
    settings_obj = StoreSettings.objects.first()
    shipping_charge = 0
    if settings_obj and cart_items:
        if settings_obj.shipping_type == 'fixed':
            shipping_charge = settings_obj.shipping_amount
        elif settings_obj.shipping_type == 'per_product':
            total_items = sum(item.quantity for item in cart_items)
            shipping_charge = settings_obj.shipping_amount * total_items
            
    total_amount = subtotal + shipping_charge
    
    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'categories': categories,
        'subtotal': subtotal,
        'shipping_charge': shipping_charge,
        'total_amount': total_amount,
    })

def remove_from_cart(request, item_id):
    cart = _get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('view_cart')

def update_cart(request, item_id):
    if request.method == 'POST':
        cart = _get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            # Stock Validation
            if cart_item.variant:
                if quantity > cart_item.variant.stock:
                    messages.error(request, f"Sorry, only {cart_item.variant.stock} units available.")
                    return redirect('view_cart')
            
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, "Cart updated.")
        else:
            cart_item.delete()
            messages.success(request, "Item removed from cart.")
    return redirect('view_cart')

def checkout(request):
    cart = _get_or_create_cart(request)
    cart_items = cart.items.all()
    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')

    categories = Category.objects.filter(is_active=True)
    
    subtotal = cart.get_total()
    settings_obj = StoreSettings.objects.first()
    shipping_charge = 0
    if settings_obj:
        if settings_obj.shipping_type == 'fixed':
            shipping_charge = settings_obj.shipping_amount
        elif settings_obj.shipping_type == 'per_product':
            total_items = sum(item.quantity for item in cart_items)
            shipping_charge = settings_obj.shipping_amount * total_items
            
    total_amount = subtotal + shipping_charge

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer_name=customer_name,
            phone=phone,
            address=address,
            shipping_charge=shipping_charge,
            total_amount=total_amount,
        )
        
        items_details = []
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                size=item.variant.size if item.variant else 'Free Size',
                quantity=item.quantity,
                price=item.product.price,
                cost_price=item.product.cost_price
            )
            if item.variant:
                item.variant.reduce_stock(item.quantity)
            else:
                v = item.product.variants.first()
                if v:
                    v.reduce_stock(item.quantity)
            items_details.append(f"{item.quantity}x {item.product.name} ({item.variant.size if item.variant else 'Free Size'}) - Rs.{item.get_subtotal()}")
        
        cart.items.all().delete()
        
        items_str = "\n".join(items_details)
        message = (
            f"New Order - Lavauz Fashions\n"
            f"Order ID: #{order.id}\n\n"
            f"Items:\n{items_str}\n\n"
            f"Subtotal: Rs.{subtotal}\n"
            f"Shipping: Rs.{shipping_charge}\n"
            f"Total: Rs.{total_amount}\n\n"
            f"Customer: {customer_name}\n"
            f"Phone: {phone}\n"
            f"Address: {address}\n\n"
            f"I would like to pay via Google Pay / UPI. Please confirm my order. Thank you!"
        )
        
        wa_number = getattr(settings, 'WHATSAPP_NUMBER', '919999999999')
        wa_url = f"https://wa.me/{wa_number}?text={quote(message)}"
        return redirect(wa_url)

    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'categories': categories,
        'subtotal': subtotal,
        'shipping_charge': shipping_charge,
        'total_amount': total_amount,
    })

# Commenting out payment_success for now
"""
@csrf_exempt
def payment_success(request):
    ...
"""

@staff_member_required
def owner_dashboard(request):
    # Stats
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    
    # Current Month Sales and Profit
    now = timezone.localtime(timezone.now())
    current_month = now.month
    current_year = now.year
    month_name = now.strftime('%B')
    
    month_orders = Order.objects.filter(
        created_at__year=current_year,
        created_at__month=current_month
    ).exclude(status='cancelled')
    
    current_month_sales = month_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Cost = Sum of (quantity * cost_price) for items in month_orders
    month_items = OrderItem.objects.filter(order__in=month_orders)
    current_month_cost = month_items.aggregate(
        total_cost=Sum(F('quantity') * F('cost_price'))
    )['total_cost'] or 0
    
    current_month_profit = current_month_sales - current_month_cost
    
    # Recent data
    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    recent_products = Product.objects.all().order_by('-created_at')[:5]
    
    # Category stats
    category_stats = Category.objects.annotate(prod_count=Count('products'))
    categories = Category.objects.filter(is_active=True)

    return render(request, 'store/dashboard.html', {
        'total_products': total_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
        'recent_products': recent_products,
        'category_stats': category_stats,
        'categories': categories,
        'current_month_name': month_name,
        'current_month_sales': current_month_sales,
        'current_month_cost': current_month_cost,
        'current_month_profit': current_month_profit,
    })

@staff_member_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
    return redirect('owner_dashboard')

def about_us(request):
    categories = Category.objects.filter(is_active=True)
    return render(request, 'store/about.html', {
        'categories': categories,
    })

# --- Authentication Views ---

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            _merge_cart(request, user)
            login(request, user)
            messages.success(request, "Registration successful! Welcome to Lavauz Fashions.")
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                _merge_cart(request, user)
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect('home')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_user(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('home')

# --- Order Tracking Views ---

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    categories = Category.objects.filter(is_active=True)
    return render(request, 'store/my_orders.html', {
        'orders': orders,
        'categories': categories
    })

def track_order(request):
    order = None
    phone = request.GET.get('phone')
    order_id = request.GET.get('order_id')
    
    if phone and order_id:
        try:
            # Try to find specific order by ID and Phone
            order = Order.objects.get(id=order_id, phone=phone)
        except (Order.DoesNotExist, ValueError):
            messages.error(request, "Order not found. Please check your details.")
    
    categories = Category.objects.filter(is_active=True)
    return render(request, 'store/track_order.html', {
        'order': order,
        'categories': categories,
        'phone': phone,
        'order_id': order_id
    })