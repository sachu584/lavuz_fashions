import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from store.models import Product, Category

def assign_categories():
    # Get categories
    kerala = Category.objects.filter(slug='kerala-wears').first()
    kurthas = Category.objects.filter(slug='kurthas').first()
    western = Category.objects.filter(slug='western-wears').first()
    cord = Category.objects.filter(slug='cord-set').first()

    # Assign to sample products
    p1 = Product.objects.filter(name='Floral Wrap Dress').first()
    if p1 and western:
        p1.category = western
        p1.save()
        print(f"Assigned {p1.name} to {western.name}")

    p2 = Product.objects.filter(name='Classic White Kurta').first()
    if p2 and kurthas:
        p2.category = kurthas
        p2.save()
        print(f"Assigned {p2.name} to {kurthas.name}")

    p3 = Product.objects.filter(name='Boho Printed Co-ord Set').first()
    if p3 and cord:
        p3.category = cord
        p3.save()
        print(f"Assigned {p3.name} to {cord.name}")

    p4 = Product.objects.filter(name='Solid Linen Shirt Dress').first()
    if p4 and western:
        p4.category = western
        p4.save()
        print(f"Assigned {p4.name} to {western.name}")

    p5 = Product.objects.filter(name='Embroidered Anarkali Kurti').first()
    if p5 and kerala:
        p5.category = kerala
        p5.save()
        print(f"Assigned {p5.name} to {kerala.name}")

    p6 = Product.objects.filter(name='Stripe Oversized Tee').first()
    if p6 and western:
        p6.category = western
        p6.save()
        print(f"Assigned {p6.name} to {western.name}")

if __name__ == '__main__':
    assign_categories()
    print("Done assigning categories to sample products.")
