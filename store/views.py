from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product, ProductImage, ProductVariant, Order, Cart, CartItem, OrderItem, StoreSettings, SpecialOffer, Jewelry, JewelryMaterial
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
    categories = Category.objects.filter(is_active=True).order_by('?')
    # Fetch clothing (products that are NOT jewelry)
    featured_products = Product.objects.filter(is_active=True).exclude(jewelry__isnull=False).order_by('?')[:8]
    # Fetch specialized jewelry
    featured_jewelry = Jewelry.objects.filter(is_active=True).order_by('?')[:4]
    
    active_offer = SpecialOffer.objects.filter(is_active=True).first()
    return render(request, 'home.html', {
        'categories': categories[:4],
        'featured_products': featured_products,
        'featured_jewelry': featured_jewelry,
        'active_offer': active_offer,
    })

def category_list(request):
    categories = Category.objects.filter(is_active=True).order_by('?')
    return render(request, 'store/category_list.html', {
        'categories': categories,
    })

def product_list(request):
    categories = Category.objects.filter(is_active=True)
    
    # Clothing (Exclude Jewelry) - Shop All now focuses on Clothing
    clothing_products = Product.objects.filter(is_active=True).exclude(jewelry__isnull=False).order_by('?')
    
    query = request.GET.get('q')
    if query:
        clothing_products = clothing_products.filter(name__icontains=query)
        
    return render(request, 'store/product_list.html', {
        'clothing_products': clothing_products,
        'categories': categories,
        'query': query,
    })

def category_detail(request, slug):
    active_category = get_object_or_404(Category, slug=slug, is_active=True)
    categories = Category.objects.filter(is_active=True)
    
    # Clothing and Jewelry in THIS category
    clothing_products = Product.objects.filter(category=active_category, is_active=True).exclude(jewelry__isnull=False).order_by('?')
    jewelry_products = Jewelry.objects.filter(category=active_category, is_active=True).order_by('?')
    
    query = request.GET.get('q')
    if query:
        clothing_products = clothing_products.filter(name__icontains=query)
        jewelry_products = jewelry_products.filter(name__icontains=query)

    return render(request, 'store/product_list.html', {
        'clothing_products': clothing_products,
        'jewelry_products': jewelry_products,
        'categories': categories,
        'active_category': active_category,
        'query': query,
    })

def jewelry_list(request):
    categories = Category.objects.filter(is_active=True)
    materials = JewelryMaterial.objects.all()
    jewelry_items = Jewelry.objects.filter(is_active=True).order_by('?')
    
    # Specific Jewelry Filters
    selected_material_id = request.GET.get('material')
    if selected_material_id:
        jewelry_items = jewelry_items.filter(material_obj_id=selected_material_id)
        
    query = request.GET.get('q')
    if query:
        jewelry_items = jewelry_items.filter(name__icontains=query)
        
    return render(request, 'store/jewelry_list.html', {
        'jewelry_items': jewelry_items,
        'categories': categories,
        'materials': materials,
        'query': query,
        'selected_material_id': selected_material_id,
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    images = product.images.all()
    variants = product.ordered_variants
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
        
        # Calculate total quantity if item already in cart
        current_cart_item = cart.items.filter(product=product, variant=variant).first()
        requested_total = quantity
        if current_cart_item:
            requested_total += current_cart_item.quantity

        # Stock Validation
        if variant:
            if requested_total > variant.stock:
                messages.error(request, f"Only {variant.stock} units of {product.name} ({size}) are available.")
                return redirect('product_detail', slug=product.slug)
        else:
            # Common Stock Fallback (if no variants exist)
            if requested_total > product.stock:
                messages.error(request, f"Only {product.stock} units of {product.name} are available.")
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
    
    # Calculate which items require shipping
    shipping_required_items = [item for item in cart_items if not item.product.is_free_shipping]
    
    if settings_obj and cart_items:
        # 1. Global Threshold check (Everything free if over Rs. X)
        if settings_obj.free_shipping_threshold > 0 and subtotal >= settings_obj.free_shipping_threshold:
            shipping_charge = 0
        # 2. Check if there are any items that actually require shipping
        elif not shipping_required_items:
            shipping_charge = 0
        # 3. Apply standard shipping for the remaining items
        else:
            if settings_obj.shipping_type == 'fixed':
                shipping_charge = settings_obj.shipping_amount
            elif settings_obj.shipping_type == 'per_product':
                # Only charge for items that are NOT marked as free shipping
                total_shipping_units = sum(item.quantity for item in shipping_required_items)
                shipping_charge = settings_obj.shipping_amount * total_shipping_units
            
    total_amount = subtotal + shipping_charge
    
    amount_to_free_shipping = 0
    if settings_obj and settings_obj.free_shipping_threshold > 0:
        amount_to_free_shipping = max(0, settings_obj.free_shipping_threshold - subtotal)
        
    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_charge': shipping_charge,
        'total_amount': total_amount,
        'categories': categories,
        'settings': settings_obj,
        'amount_to_free_shipping': amount_to_free_shipping,
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
    
    # Calculate which items require shipping
    shipping_required_items = [item for item in cart_items if not item.product.is_free_shipping]

    if settings_obj:
        # 1. Global Threshold check
        if settings_obj.free_shipping_threshold > 0 and subtotal >= settings_obj.free_shipping_threshold:
            shipping_charge = 0
        # 2. Check if there are any items that actually require shipping
        elif not shipping_required_items:
            shipping_charge = 0
        # 3. Apply standard shipping
        else:
            if settings_obj.shipping_type == 'fixed':
                shipping_charge = settings_obj.shipping_amount
            elif settings_obj.shipping_type == 'per_product':
                # Only charge for items that are NOT marked as free shipping
                total_shipping_units = sum(item.quantity for item in shipping_required_items)
                shipping_charge = settings_obj.shipping_amount * total_shipping_units
            
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
                price=item.product.effective_price,
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
            f"New Order - Lasaatelier\n"
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
            messages.success(request, "Registration successful! Welcome to Lasaatelier.")
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