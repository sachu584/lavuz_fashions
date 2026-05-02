import os
import django
from django.test import RequestFactory
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from store.views import search_suggestions

factory = RequestFactory()
request = factory.get('/search-suggestions/', {'q': 'ku'})
response = search_suggestions(request)

print(f"Status Code: {response.status_code}")
print(f"Content: {response.content.decode()}")
