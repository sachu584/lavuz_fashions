from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User

SIZE_ORDER = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'Free Size']


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0, help_text="Display order (lower = first)")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='products'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="If set, this will be the selling price. The regular price will be shown as a strikethrough.")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Used to calculate profit")
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    is_free_shipping = models.BooleanField(default=False)
    size_chart = models.ImageField(upload_to='size_charts/', null=True, blank=True, help_text="Size chart image for this product")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_primary_image(self):
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary
        return self.images.first()

    def __str__(self):
        return self.name

    @property
    def ordered_variants(self):
        """Returns variants sorted in correct clothing size order."""
        variants = list(self.variants.all())
        return sorted(variants, key=lambda v: SIZE_ORDER.index(v.size) if v.size in SIZE_ORDER else 99)

    @property
    def effective_price(self):
        if self.offer_price:
            return self.offer_price
        return self.price

    @property
    def discount_percentage(self):
        if self.offer_price and self.price > 0:
            discount = ((self.price - self.offer_price) / self.price) * 100
            return int(discount)
        return 0


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"


class ProductVariant(models.Model):
    SIZE_CHOICES = [
        ('XXS', 'XXS'),
        ('XS', 'XS'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
        ('Free Size', 'Free Size'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    numeric_size = models.CharField(max_length=20, blank=True, null=True, help_text="e.g. 34, 36-38 (optional)")
    stock = models.IntegerField(default=10)
    is_available = models.BooleanField(default=True)

    def reduce_stock(self, quantity=1):
        """Reduces stock and updates availability."""
        if self.stock >= quantity:
            self.stock -= quantity
            if self.stock <= 0:
                self.is_available = False
            self.save()
            return True
        return False

    class Meta:
        unique_together = ('product', 'size')
        ordering = ['size']

    @property
    def display_size(self):
        if self.numeric_size:
            return f"{self.size}({self.numeric_size})"
        return self.size

    def __str__(self):
        return f"{self.product.name} - {self.display_size}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ])
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    size = models.CharField(max_length=20, null=True, blank=True, default='Free Size')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) # price at the time of order
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # cost at the time of order

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'} (Order #{self.order.id})"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cart')
    session_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_total(self):
        return sum(item.get_subtotal() for item in self.items.all())

    def __str__(self):
        return f"Cart #{self.id}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def get_subtotal(self):
        return self.product.effective_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class StoreSettings(models.Model):
    SHIPPING_CHOICES = [
        ('fixed', 'Fixed Amount Per Order'),
        ('per_product', 'Per Product Amount'),
    ]
    shipping_type = models.CharField(max_length=20, choices=SHIPPING_CHOICES, default='fixed')
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Orders above this amount get free shipping. Set to 0 to disable.")

    def __str__(self):
        return "Store Settings"

    class Meta:
        verbose_name_plural = "Store Settings"


class SpecialOffer(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    discount_text = models.CharField(max_length=50, blank=True, help_text="e.g. 50% OFF")
    image = models.ImageField(upload_to='offers/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    link = models.CharField(max_length=255, blank=True, null=True, help_text="e.g. /shop/ or a full URL")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.is_active:
            # Ensure only one active offer
            SpecialOffer.objects.filter(is_active=True).exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Special Offers"
