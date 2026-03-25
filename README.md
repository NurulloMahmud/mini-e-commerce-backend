# Group Shop — E-Commerce Backend

A RESTful backend API for a mini e-commerce platform built with **Django** and **Django REST Framework**. Supports user authentication, product management, shopping cart, and order placement.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.9 |
| Framework | Django 4.2 |
| API | Django REST Framework |
| Auth | JWT (djangorestframework-simplejwt) |
| Database | SQLite (development) |
| Image handling | Pillow |
| CORS | django-cors-headers |

---

## Project Structure

```
e-commerce/
├── config/             # Project settings and root URL config
├── users/              # Custom user model, register, login
├── products/           # Product model and CRUD
├── cart/               # Cart model, add/update/remove items
├── orders/             # Order placement and history
├── requirements.txt
├── .env
└── manage.py
```

---

## Getting Started

### 1. Clone and set up environment

```bash
git clone https://github.com/NurulloMahmud/mini-e-commerce-backend.git
cd mini-e-commerce-backend

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Create an admin user

```bash
python manage.py createsuperuser
```

You will be prompted for a phone number, full name, and password. This account will have `is_staff: true` and can create/edit/delete products.

### 5. Start the development server

```bash
python manage.py runserver
```

API is available at `http://127.0.0.1:8000`

---

## Authentication

This API uses **JWT (JSON Web Tokens)**. After login or registration, you receive an `access` token and a `refresh` token.

Include the access token in the `Authorization` header for all protected endpoints:

```
Authorization: Bearer <access_token>
```

Access tokens expire after **1 day**. Use the refresh endpoint to get a new one without re-logging in.

---

## API Reference

### Base URL

```
http://127.0.0.1:8000/api
```

---

### Auth

#### `POST /auth/register/`

Register a new user. Returns JWT tokens immediately.

**Auth required:** No

**Request body:**

```json
{
  "fullname": "Ali Valiyev",
  "phone": "+998901234567",
  "password": "secret123"
}
```

**Response `201 Created`:**

```json
{
  "user": {
    "id": 1,
    "fullname": "Ali Valiyev",
    "phone": "+998901234567",
    "is_staff": false,
    "created_at": "2026-03-25T10:00:00Z"
  },
  "access": "<access_token>",
  "refresh": "<refresh_token>"
}
```

**Errors:**

| Status | Reason |
|---|---|
| `400` | Phone already registered |
| `400` | Password shorter than 6 characters |
| `400` | Missing required fields |

---

#### `POST /auth/login/`

Log in with phone and password.

**Auth required:** No

**Request body:**

```json
{
  "phone": "+998901234567",
  "password": "secret123"
}
```

**Response `200 OK`:**

```json
{
  "user": {
    "id": 1,
    "fullname": "Ali Valiyev",
    "phone": "+998901234567",
    "is_staff": false,
    "created_at": "2026-03-25T10:00:00Z"
  },
  "access": "<access_token>",
  "refresh": "<refresh_token>"
}
```

> **Frontend tip:** Store `is_staff` from the user object to conditionally show admin-only UI (product creation, admin panel link, etc.)

**Errors:**

| Status | Reason |
|---|---|
| `400` | Invalid phone or password |

---

#### `POST /auth/token/refresh/`

Get a new access token using a refresh token.

**Auth required:** No

**Request body:**

```json
{
  "refresh": "<refresh_token>"
}
```

**Response `200 OK`:**

```json
{
  "access": "<new_access_token>"
}
```

---

### Products

#### `GET /products/`

List all products. Supports optional search and category filter.

**Auth required:** No

**Query params:**

| Param | Type | Description |
|---|---|---|
| `search` | string | Filter by product name (case-insensitive) |
| `category` | string | Filter by exact category name (case-insensitive) |

**Examples:**
```
GET /api/products/
GET /api/products/?search=phone
GET /api/products/?category=Electronics
```

**Response `200 OK`:**

```json
[
  {
    "id": 1,
    "name": "iPhone 15",
    "price": "1299.99",
    "image": "http://127.0.0.1:8000/media/products/iphone.jpg",
    "category": "Electronics",
    "created_at": "2026-03-25T10:00:00Z"
  }
]
```

---

#### `POST /products/`

Create a new product.

**Auth required:** Yes — Admin only (`is_staff: true`)

**Request body** (multipart/form-data for image upload):

```
name        = "iPhone 15"
price       = "1299.99"
category    = "Electronics"
image       = <file>         (optional)
```

**Response `201 Created`:**

```json
{
  "id": 1,
  "name": "iPhone 15",
  "price": "1299.99",
  "image": "http://127.0.0.1:8000/media/products/iphone.jpg",
  "category": "Electronics",
  "created_at": "2026-03-25T10:00:00Z"
}
```

**Errors:**

| Status | Reason |
|---|---|
| `400` | Price is 0 or negative |
| `400` | Missing required fields |
| `401` | Not authenticated |
| `403` | Not an admin |

---

#### `GET /products/<id>/`

Get a single product by ID.

**Auth required:** No

**Response `200 OK`:** Same shape as a single product object above.

**Errors:**

| Status | Reason |
|---|---|
| `404` | Product not found |

---

#### `PUT /products/<id>/`

Update a product.

**Auth required:** Yes — Admin only

**Request body:** Same fields as POST.

**Response `200 OK`:** Updated product object.

---

#### `DELETE /products/<id>/`

Delete a product.

**Auth required:** Yes — Admin only

**Response `204 No Content`**

---

### Cart

All cart endpoints require authentication. Each user only sees and manages their own cart.

#### `GET /cart/`

Get the current user's cart with total price.

**Auth required:** Yes

**Response `200 OK`:**

```json
{
  "items": [
    {
      "id": 1,
      "product": {
        "id": 3,
        "name": "iPhone 15",
        "price": "1299.99",
        "image": "...",
        "category": "Electronics",
        "created_at": "..."
      },
      "quantity": 2,
      "subtotal": "2599.98",
      "created_at": "2026-03-25T10:00:00Z"
    }
  ],
  "total": "2599.98"
}
```

---

#### `POST /cart/`

Add a product to the cart. If the product is already in the cart, the quantity is incremented.

**Auth required:** Yes

**Request body:**

```json
{
  "product_id": 3,
  "quantity": 2
}
```

**Response `201 Created`** (new item) or **`200 OK`** (quantity incremented):

```json
{
  "id": 1,
  "product": { ... },
  "quantity": 2,
  "subtotal": "2599.98",
  "created_at": "..."
}
```

**Errors:**

| Status | Reason |
|---|---|
| `400` | `product_id` not provided |
| `400` | Quantity less than 1 |
| `404` | Product not found |

---

#### `PATCH /cart/<id>/`

Update the quantity of a specific cart item.

**Auth required:** Yes — must own the cart item

**Request body:**

```json
{
  "quantity": 5
}
```

**Response `200 OK`:** Updated cart item object.

**Errors:**

| Status | Reason |
|---|---|
| `400` | Quantity less than 1 |
| `404` | Item not found or belongs to another user |

---

#### `DELETE /cart/<id>/`

Remove an item from the cart.

**Auth required:** Yes — must own the cart item

**Response `204 No Content`**

**Errors:**

| Status | Reason |
|---|---|
| `404` | Item not found or belongs to another user |

---

### Orders

All order endpoints require authentication. Each user only sees their own orders.

#### `POST /orders/`

Place an order from the current cart. Calculates total automatically and clears the cart on success.

**Auth required:** Yes

**Request body:** None — order is built from the user's current cart.

**Response `201 Created`:**

```json
{
  "id": 1,
  "total": "2599.98",
  "status": "pending",
  "items": [
    {
      "id": 1,
      "product": 3,
      "product_name": "iPhone 15",
      "price": "1299.99",
      "quantity": 2,
      "subtotal": "2599.98"
    }
  ],
  "created_at": "2026-03-25T10:00:00Z"
}
```

> **Note:** `product_name` and `price` are captured at the time of order so the order history remains accurate even if the product is later changed or deleted.

**Errors:**

| Status | Reason |
|---|---|
| `400` | Cart is empty |
| `401` | Not authenticated |

---

#### `GET /orders/`

List all orders placed by the current user, newest first.

**Auth required:** Yes

**Response `200 OK`:** Array of order objects (same shape as above).

---

#### `GET /orders/<id>/`

Get a single order with all its items.

**Auth required:** Yes — must own the order

**Response `200 OK`:** Single order object.

**Errors:**

| Status | Reason |
|---|---|
| `404` | Order not found or belongs to another user |

---

## Order Status Values

| Value | Meaning |
|---|---|
| `pending` | Order placed, awaiting processing |
| `processing` | Order is being prepared |
| `shipped` | Order has been shipped |
| `delivered` | Order delivered to customer |
| `cancelled` | Order was cancelled |

Status is managed via the Django admin panel.

---

## Admin Panel

Django's built-in admin is available at:

```
http://127.0.0.1:8000/admin/
```

Log in with the superuser account created during setup. From the admin panel you can:

- Manage users and permissions
- Create, edit, and delete products
- View and update order statuses

---

## Running Tests

```bash
python manage.py test users products cart orders
```

The test suite has **44 tests** covering all endpoints, edge cases, and user isolation rules.

```
Ran 44 tests in ~16s ... OK
```

---

## CORS

The backend allows requests from the following origins by default (configurable in `settings.py`):

```
http://localhost:3000   (Create React App)
http://localhost:5173   (Vite)
```

To add more origins, update `CORS_ALLOWED_ORIGINS` in `config/settings.py`.

---

## Media Files

Product images are stored under the `media/products/` directory and served at `/media/` in development. Image URLs are returned as absolute URLs in API responses.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | Yes | — | Django secret key |
| `DEBUG` | No | `True` | Debug mode |
| `ALLOWED_HOSTS` | No | `localhost,127.0.0.1` | Comma-separated allowed hosts |
