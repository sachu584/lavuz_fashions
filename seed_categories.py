import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from store.models import Category

categories = [
    ('Kerala Wears',       'kerala-wears',       0),
    ('Sarees',             'sarees',             1),
    ('Churidar Materials', 'churidar-materials', 2),
    ('Kurthas',            'kurthas',            3),
    ('Western Wears',      'western-wears',      4),
    ('Kids Wears',         'kids-wears',         5),
    ('Cord-set',           'cord-set',           6),
    ('Mens Wears',         'mens-wears',         7),
]

created = 0
for name, slug, order in categories:
    obj, made = Category.objects.get_or_create(
        slug=slug,
        defaults={'name': name, 'order': order, 'is_active': True}
    )
    if made:
        print("[OK] Created category: " + name)
        created += 1
    else:
        print("[--] Already exists: " + name)

print("\n[DONE] " + str(created) + " categories created.")
print("Visit admin -> http://127.0.0.1:8000/admin/store/category/ to manage them.")
