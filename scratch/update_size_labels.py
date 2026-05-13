from store.models import ProductVariant

mapping = {
    'XXS': 'XXS(30)',
    'XS': 'XS(32)',
    'S': 'S(34)',
    'M': 'M(36)',
    'L': 'L(38)',
    'XL': 'XL(40)',
    'XXL': 'XXL(42)',
}

updated_count = 0
for old, new in mapping.items():
    variants = ProductVariant.objects.filter(size=old)
    count = variants.count()
    if count > 0:
        variants.update(size=new)
        print(f"Updated {count} variants from {old} to {new}")
        updated_count += count

print(f"Update complete. Total variants updated: {updated_count}")
