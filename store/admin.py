from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, ProductVariant, Order, OrderItem, StoreSettings, SpecialOffer, Jewelry, JewelryMaterial


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
    fields = ('media_type', 'image', 'video', 'is_primary', 'order', 'preview')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.media_type == 'video' and obj.video:
            return format_html('<video src="{}" style="height:80px; border-radius:6px;" muted loop></video>', obj.video.url)
        if obj.image:
            return format_html('<img src="{}" style="height:80px; border-radius:6px;" />', obj.image.url)
        return "No Media"
    preview.short_description = 'Preview'


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 4
    fields = ('size', 'numeric_size', 'stock', 'is_available')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'name', 'category', 'price', 'offer_price', 'stock', 'is_free_shipping', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'is_free_shipping', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('offer_price', 'stock', 'is_free_shipping', 'is_active')
    fields = ('category', 'name', 'slug', 'price', 'offer_price', 'cost_price', 'description', 'size_chart', 'is_active', 'is_free_shipping')
    inlines = [ProductImageInline, ProductVariantInline]

    def thumbnail(self, obj):
        img = obj.get_primary_image()
        if img:
            return format_html('<img src="{}" style="height:50px; border-radius:4px;" />', img.image.url)
        return "—"
    thumbnail.short_description = 'Image'
    
    def has_size_chart(self, obj):
        return bool(obj.size_chart)
    has_size_chart.boolean = True
    has_size_chart.short_description = 'Size Chart'


@admin.register(JewelryMaterial)
class JewelryMaterialAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Jewelry)
class JewelryAdmin(ProductAdmin):
    list_display = ('thumbnail', 'name', 'material_obj', 'purity', 'price', 'offer_price', 'stock', 'is_free_shipping', 'is_active', 'created_at')
    list_filter = ('material_obj', 'is_active', 'is_exclusive', 'created_at')
    fields = (
        'category', 'name', 'slug', 'price', 'offer_price', 'cost_price', 
        'material_obj', 'purity', 'weight', 'stone_type', 'is_exclusive',
        'stock', 'description', 'size_chart', 'is_active', 'is_free_shipping'
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'media_type', 'is_primary', 'order', 'preview')
    list_filter = ('media_type', 'is_primary')

    def preview(self, obj):
        if obj.media_type == 'video' and obj.video:
            return format_html('<video src="{}" style="height:60px; border-radius:4px;" muted loop></video>', obj.video.url)
        if obj.image:
            return format_html('<img src="{}" style="height:60px; border-radius:4px;" />', obj.image.url)
        return "—"
    preview.short_description = 'Preview'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'size', 'stock', 'is_available')
    list_filter = ('size', 'is_available')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'phone', 'status', 'total_amount', 'get_product_ids', 'created_at')
    list_filter = ('status',)
    search_fields = ('customer_name', 'phone')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'shipping_charge', 'total_amount')
    
    def get_product_ids(self, obj):
        return ", ".join([f"#{item.product.id}" for item in obj.items.all() if item.product])
    get_product_ids.short_description = 'Product IDs'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('get_product_image', 'get_product_id', 'product', 'size', 'quantity', 'price', 'cost_price')
    can_delete = False

    def get_product_id(self, obj):
        return f"#{obj.product.id}" if obj.product else "N/A"
    get_product_id.short_description = 'Product ID'

    def get_product_image(self, obj):
        if obj.product:
            img = obj.product.get_primary_image()
            if img:
                return format_html('<img src="{}" style="height:50px; border-radius:4px;" />', img.image.url)
        return "—"
    get_product_image.short_description = 'Image'

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
