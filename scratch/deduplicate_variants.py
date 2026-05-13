from store.models import ProductVariant
from django.db.models import Count

duplicates = ProductVariant.objects.values('product', 'size').annotate(count=Count('id')).filter(count__gt=1)

for d in duplicates:
    variants = ProductVariant.objects.filter(product_id=d['product'], size=d['size'])
    # Keep the first one, delete the rest
    for v in variants[1:]:
        print(f"Deleting duplicate variant ID {v.id} for Product {v.product_id} Size {v.size}")
        v.delete()

print("Deduplication complete.")
