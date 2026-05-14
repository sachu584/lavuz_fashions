from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('jewelry/', views.jewelry_list, name='jewelry_list'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('categories/', views.category_list, name='category_list'),
    path('dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('order/update-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    # path('payment-success/', views.payment_success, name='payment_success'),
    path('about/', views.about_us, name='about_us'),
    
    # Auth
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    
    # Orders
    path('my-orders/', views.my_orders, name='my_orders'),
    path('track-order/', views.track_order, name='track_order'),
]
