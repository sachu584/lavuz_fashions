import re
from store.models import ProductVariant

variants = ProductVariant.objects.all()
updated_count = 0

for v in variants:
    # Pattern to match Size(Numeric) e.g. XS(32)
    match = re.match(r'^([^(]+)\(([^)]+)\)$', v.size)
    if match:
        base_size = match.group(1).strip()
        numeric_val = match.group(2).strip()
        
        v.size = base_size
        v.numeric_size = numeric_val
        v.save()
        print(f"Split {v.product.name} variant: {base_size} + {numeric_val}")
        updated_count += 1

print(f"Cleanup complete. Total variants updated: {updated_count}")
