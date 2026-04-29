import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from store.models import Product, ProductVariant

User = get_user_model()

# Superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@lavusfashions.com', 'admin123')
    print("[OK] Superuser created -> username: admin | password: admin123")
else:
    print("[--] Superuser 'admin' already exists.")

# Sample Products
sample_products = [
    {
        'name': 'Floral Wrap Dress',
        'price': 1299,
        'description': 'A beautiful floral wrap dress crafted from soft, breathable fabric. Perfect for brunch, outings, or casual evenings. The wrap silhouette flatters all body types with a relaxed yet stylish fit.',
        'sizes': ['S', 'M', 'L', 'XL'],
    },
    {
        'name': 'Classic White Kurta',
        'price': 899,
        'description': 'Timeless white kurta with delicate embroidery detailing on the neckline. Made from premium cotton fabric, ideal for festive occasions and everyday elegance.',
        'sizes': ['S', 'M', 'L', 'XL', 'XXL'],
    },
    {
        'name': 'Boho Printed Co-ord Set',
        'price': 1599,
        'description': 'Trendy boho-inspired printed co-ord set featuring wide-leg trousers and a matching crop top. Lightweight fabric, perfect for summers and vacation trips.',
        'sizes': ['S', 'M', 'L'],
    },
    {
        'name': 'Solid Linen Shirt Dress',
        'price': 1099,
        'description': 'Minimalist shirt dress in premium linen blend. Features button-down front, collar neckline and a relaxed knee-length silhouette. A wardrobe essential.',
        'sizes': ['XS', 'S', 'M', 'L', 'XL'],
    },
    {
        'name': 'Embroidered Anarkali Kurti',
        'price': 1799,
        'description': 'Elegant Anarkali kurti with intricate thread embroidery. Floor-length flare, comfortable cotton fabric. Perfect for festive and semi-formal occasions.',
        'sizes': ['S', 'M', 'L', 'XL'],
    },
    {
        'name': 'Stripe Oversized Tee',
        'price': 599,
        'description': 'Casual oversized tee in classic stripe pattern. Super soft cotton blend, relaxed fit. Pairs perfectly with jeans, palazzos, or shorts.',
        'sizes': ['S', 'M', 'L', 'XL', 'XXL'],
    },
]

created_count = 0
for data in sample_products:
    product, created = Product.objects.get_or_create(
        name=data['name'],
        defaults={
            'price': data['price'],
            'description': data['description'],
            'is_active': True,
        }
    )
    if created:
        for size in data['sizes']:
            ProductVariant.objects.create(product=product, size=size, stock=20)
        print("[OK] Created: " + product.name)
        created_count += 1
    else:
        print("[--] Already exists: " + product.name)

print("\n[DONE] " + str(created_count) + " new products created.")
print("Admin  -> http://127.0.0.1:8000/admin/  |  user: admin  |  pass: admin123")
print("Site   -> http://127.0.0.1:8000/")
