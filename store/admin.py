from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, ProductVariant, Order, OrderItem, StoreSettings, SpecialOffer


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    list_filter = ('is_active',)

    def product_count(self, obj):
        count = obj.products.filter(is_active=True).count()
        return format_html('<b>{}</b> products', count)
    product_count.short_description = 'Products'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ('image', 'is_primary', 'order', 'image_preview')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:80px; border-radius:6px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 4
    fields = ('size', 'stock', 'is_available')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'name', 'category', 'price', 'cost_price', 'is_active', 'created_at')
    list_filter = ('is_active', 'category')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)
    inlines = [ProductImageInline, ProductVariantInline]

    def thumbnail(self, obj):
        img = obj.get_primary_image()
        if img:
            return format_html('<img src="{}" style="height:50px; border-radius:4px;" />', img.image.url)
        return "—"
    thumbnail.short_description = 'Image'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_primary', 'order', 'image_preview')
    list_filter = ('is_primary',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px; border-radius:4px;" />', obj.image.url)
        return "—"
    image_preview.short_description = 'Preview'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'size', 'stock', 'is_available')
    list_filter = ('size', 'is_available')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'phone', 'status', 'total_amount', 'created_at')
    list_filter = ('status',)
    search_fields = ('customer_name', 'phone')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'shipping_charge', 'total_amount')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'size', 'quantity', 'price', 'cost_price')
    can_delete = False

# Add inline to OrderAdmin
OrderAdmin.inlines = [OrderItemInline]

@admin.register(SpecialOffer)
class SpecialOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'discount_text', 'is_active', 'created_at')
    list_editable = ('is_active',)


@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ('shipping_type', 'shipping_amount')

# Customize admin site
admin.site.site_header = "Lavauz Fashions Admin"
admin.site.site_title = "Lavauz Fashions"
admin.site.index_title = "Welcome to Lavauz Fashions Dashboard"
