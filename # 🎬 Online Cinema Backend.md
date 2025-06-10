# 🎬 Online Cinema Backend

Backend for an online cinema platform built with **FastAPI**, supporting features like:

- 🛒 Shopping cart and movie purchases  
- 💳 Stripe payments integration  
- 👤 Role-based access (User, Moderator, Admin)  
- 🔐 JWT Authentication  
- 🧪 Full testing with `pytest`  
- 📦 Containerized with Docker & Docker Compose  
- ⚙️ CI/CD with GitHub Actions  
- 📄 Auto-generated Swagger docs  

---

## 🚀 Features

### 🎥 Movies
- Browse, search, and filter movies by genre, year, rating
- Like/dislike, comment, and rate movies
- Moderators/Admins can create/edit/delete movies

### 🛍️ Shopping Cart
- Add/remove/clear movies in the cart
- Prevent duplicates or already purchased movies
- Pay for all movies in the cart in one go

### 📦 Orders
- Place and manage orders
- View order history, statuses, and details
- Cancel unpaid orders, request refunds for paid ones

### 💰 Payments
- Stripe checkout integration
- Store `external_payment_id` for audit/refunds
- Handle `webhooks` to verify payment status
- Payment history with full breakdown

---

## 🧱 Tech Stack

| Layer         | Tech                          |
|---------------|-------------------------------|
| Framework     | [FastAPI](https://fastapi.tiangolo.com/) |
| Auth          | JWT via `fastapi-jwt-auth`    |
| Database      | PostgreSQL + SQLAlchemy ORM   |
| Queue         | Celery + Redis                |
| File Storage  | MinIO (S3-compatible)         |
| Payments      | Stripe API + webhooks         |
| Container     | Docker + Docker Compose       |
| Dev Tools     | Poetry, pre-commit, GitHub Actions |
| Tests         | Pytest, httpx, coverage       |
| Docs          | Swagger (OpenAPI 3.0)         |

---

## 🐳 Docker Setup

```bash
# Build and run all services (FastAPI, Redis, Celery, MinIO, etc.)
docker-compose up --build
