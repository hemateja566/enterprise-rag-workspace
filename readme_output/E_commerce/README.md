# E-Commerce Platform

Full-stack e-commerce web application built with Flask, featuring product catalog, shopping cart, user authentication, and admin panel.

## Features

- **Product Catalog**: Browse, search, filter products
- **Shopping Cart**: Add/remove items, quantity management
- **User Authentication**: Register, login, logout, sessions
- **Checkout Process**: Shipping, payment, order confirmation
- **Order History**: View past orders and status
- **Admin Panel**: Product CRUD, order management, user management
- **Responsive Design**: Mobile-friendly templates
- **Image Upload**: Product image management

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.10+, Flask, SQLAlchemy |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Frontend | Jinja2 Templates, Bootstrap 5, Vanilla JS |
| Auth | Flask-Login, Werkzeug Security |
| Deployment | Gunicorn, Nginx, Docker |
| Process Manager | Procfile (Heroku/Render) |

## Project Structure

```
E_commerce/
├── app.py                  # Flask application factory
├── requirements.txt        # Python dependencies
├── Procfile                # Process definition
├── .env                    # Environment variables (local only)
├── config.py               # Configuration
├── models.py               # SQLAlchemy models
├── forms.py                # WTForms
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── images/
│       └── products/
├── templates/
│   ├── base.html           # Base template
│   ├── index.html          # Home page
│   ├── products/
│   │   ├── list.html       # Product grid
│   │   └── detail.html     # Product detail
│   ├── cart/
│   │   └── cart.html       # Shopping cart
│   ├── checkout/
│   │   └── checkout.html   # Checkout flow
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── orders/
│   │   ├── history.html
│   │   └── detail.html
│   └── admin/
│       ├── dashboard.html
│       ├── products.html
│       └── orders.html
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- pip
- SQLite (included) or PostgreSQL

### Installation

```bash
git clone https://github.com/hemateja566/E_commerce.git
cd E_commerce

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Configuration

Create `.env` file:
```env
SECRET_KEY=your-super-secret-key-change-in-production
DATABASE_URL=sqlite:///ecommerce.db
FLASK_ENV=development
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Database Setup

```bash
# Tables created automatically on first run
# Or initialize manually:
flask shell
>>> from app import db
>>> db.create_all()
>>> exit()
```

### Run Development Server

```bash
flask run
# Or: python app.py
```

Runs at `http://localhost:5000`

## Key Models

### User
```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Product
```python
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String(500))
    stock = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Order
```python
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(20), default='pending')  # pending, paid, shipped, delivered, cancelled
    shipping_address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

## Admin Panel

Access at `/admin` (requires admin user).

Features:
- Dashboard with sales metrics
- Product management (CRUD)
- Order management (status updates)
- User management
- Category management

Create admin user:
```bash
flask shell
>>> from app import db, User
>>> from werkzeug.security import generate_password_hash
>>> admin = User(email='admin@example.com', password_hash=generate_password_hash('admin123'), is_admin=True)
>>> db.session.add(admin)
>>> db.session.commit()
```

## Deployment

### Heroku / Render / Railway

1. Create `Procfile`:
```
web: gunicorn app:app
```

2. Set environment variables in platform dashboard

3. Use managed PostgreSQL:
```env
DATABASE_URL=postgresql://user:pass@host/db
```

4. Deploy

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "app:app"]
```

## Security Checklist

- ✅ Password hashing (Werkzeug)
- ✅ CSRF protection (Flask-WTF)
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ XSS prevention (Jinja2 auto-escape)
- ✅ Secure session cookies
- 🔄 Add: Rate limiting, HTTPS enforcement, Content Security Policy

## Future Enhancements

- [ ] Payment integration (Stripe/Razorpay)
- [ ] Email notifications (order confirmations)
- [ ] Product reviews & ratings
- [ ] Wishlist/favorites
- [ ] Coupon/discount codes
- [ ] Inventory tracking with low-stock alerts
- [ ] Multi-currency support
- [ ] API for mobile app
- [ ] Analytics dashboard

## License

MIT License