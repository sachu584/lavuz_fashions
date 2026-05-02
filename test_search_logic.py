import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from store.views import product_list

factory = RequestFactory()

def test_query(q):
    print(f"\nTesting search for: '{q}'")
    request = factory.get('/products/', {'q': q})
    request.user = AnonymousUser()
    
    # We need to add session to the request as well because of context processors or middleware
    from django.contrib.sessions.middleware import SessionMiddleware
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()

    response = product_list(request)
    content = response.content.decode()
    
    found = []
    for name in ['Floral Wrap Dress', 'Classic White Kurta', 'Boho Printed Co-ord Set', 'Solid Linen Shirt Dress', 'Embroidered Anarkali Kurti', 'Stripe Oversized Tee']:
        if name in content:
            found.append(name)
    
    print(f"Products found in HTML: {found}")

test_query('Kurta')
test_query('white dress')
test_query('kerala')
test_query('churidar')
