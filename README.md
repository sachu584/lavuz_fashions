# Lavus Fashions — Django eCommerce

A minimal, modern fashion eCommerce website built with Django.

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install django pillow
```

### 2. Run migrations
```bash
python manage.py migrate
```

### 3. Seed sample data & create admin user
```bash
python seed.py
```

### 4. Start the server
```bash
python manage.py runserver
```

### 5. Open in browser
- 🌐 **Website**: http://127.0.0.1:8000/
- 🔐 **Admin Panel**: http://127.0.0.1:8000/admin/
  - Username: `admin`
  - Password: `admin123`

---

## 📁 Project Structure

```
lavus_fashions/
├── core/               # Django project settings & URLs
├── store/              # Main app (models, views, admin)
│   ├── models.py       # Product, ProductImage, ProductVariant, Order
│   ├── views.py        # Home, List, Detail, WhatsApp order
│   ├── admin.py        # Admin with image previews & inlines
│   └── urls.py
├── templates/          # HTML templates
│   ├── base.html       # Navbar + footer layout
│   ├── home.html       # Homepage
│   └── store/
│       ├── product_list.html
│       └── product_detail.html
├── static/
│   └── css/style.css   # Full custom CSS (Zara-inspired)
├── media/              # Uploaded product images
├── seed.py             # Sample data + superuser creator
└── manage.py
```

---

## ⚙️ Update WhatsApp Number

Open `core/settings.py` and change:
```python
WHATSAPP_NUMBER = '916235712129'  # Your number here (no + or spaces)
```

---

## 🛍️ Features

- Homepage with hero banner + product grid
- Product listing page
- Product detail with image gallery & thumbnails
- Size selector (S, M, L, XL, XXL)
- WhatsApp order integration (pre-filled message)
- Order saved to database
- Django Admin with image previews and inline management
- Mobile-first responsive design
- Gold/minimal Zara-inspired UI

---

## 🔐 Future Features (Phase 2)

- User registration & login
- Add to cart
- Online payment (Stripe / Razorpay)
- Order tracking
- Discount coupons
- Reviews & ratings
