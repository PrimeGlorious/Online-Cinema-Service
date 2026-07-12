## Online-Cinema-Service 🎬🍿

Welcome to **Online Cinema API** — your virtual cinema that lets you register, authenticate, and enjoy your favorite movies right from the browser. The main goal of this project is to build a fast, secure, and scalable service with a flexible access-control system and seamless payment integration.

In this project, you’ll find:

* 🔐 **User registration and account activation** with email confirmation and automatic removal of expired tokens via celery-beat.
* 🔑 **JWT authentication** (access and refresh tokens) with support for token refresh and revocation on logout.
* 👥 **Three user roles** (User, Moderator, Admin) with distinct permissions for managing movies, comments, and users.
* 🎞️ **Movie catalog** featuring search, filtering, sorting, ratings, likes, and comments.
* 🛒 **Shopping cart and checkout** with Stripe integration for secure payments.
* 🐳 **Containerization** using Docker Compose for quick setup of all services.
* 🤖 **CI/CD pipeline** powered by GitHub Actions for automated testing, linting, and deployment.

## Authorization & Authentication 🔐

Here’s how users securely sign up, log in, and manage their passwords:

* 🔐 **Register**
  `POST /api/v1/accounts/register/`
  Users submit email & password → we create an inactive account and send a 24-hour activation link.

* ✅ **Activate**
  `GET /api/v1/accounts/activate/{token}/`
  Clicking the link sets the account to active.

* 🔑 **Login & Logout**
  `POST /api/v1/accounts/login/` → returns `{ access_token, refresh_token }`
  `POST /api/v1/accounts/logout/` → revokes the refresh token.

* 🔄 **Refresh Token**
  `POST /api/v1/accounts/token/refresh/` → get a new access token using your refresh token.

* 🛡️ **Password Management**

  * **Change:** `POST /api/v1/accounts/change-password/` (old + new password)
  * **Reset:**

    1. `POST /api/v1/accounts/reset-password-request/` → sends a reset link.
    2. `POST /api/v1/accounts/reset-password/` (token + new password) → updates your password.

## Profiles 👤

Manage user profiles to store and update personal information:

* **Get My Profile**
  **GET** `/api/v1/profiles/me`
  Returns the profile of the authenticated user.

* **Create My Profile**
  **POST** `/api/v1/profiles/`

  ```json
  {
    "first_name": "John",
    "last_name": "Doe",
    "gender": "MAN",
    "date_of_birth": "1990-01-01",
    "info": "Short bio about me"
  }
  ```

  Creates and returns your profile.

* **Update My Profile**
  **PATCH** `/api/v1/profiles/me`

  ```json
  {
    "first_name": "Jane",
    "info": "Updated bio"
  }
  ```

  Updates fields in your profile and returns the updated data.

* **List All Profiles**
  **GET** `/api/v1/profiles/`
  Returns a list of all user profiles.

* **Get Profile by ID**
  **GET** `/api/v1/profiles/{profile_id}`
  Retrieves a specific user’s profile.

* **Update Profile by ID**
  **PATCH** `/api/v1/profiles/{profile_id}`

  ```json
  {
    "last_name": "Smith"
  }
  ```

  Updates another user’s profile (requires proper permissions) and returns the updated data.

* **Delete Profile**
  **DELETE** `/api/v1/profiles/{profile_id}`
  Deletes the specified profile and returns a confirmation message.


## Movies 🎞️

Work with the film catalog and favorites:

### List Movies

`GET /api/v1/theater/movies/`

* **Query params:**

  * `page` (int, default 1)
  * `per_page` (int, default 10, max 20)
  * Filter fields from `MovieListItemFiltersSchema` (e.g. `genre`, `year`, `min_imdb`, etc.)
* **Response:** `MovieListResponseSchema` with `items`, `total_pages`, `total_items`, `prev`, `next`.

### Get Movie Details

`GET /api/v1/theater/movies/{movie_id}/`

* Returns full movie info (`MovieDetailResponseSchema`).

### Create / Update / Delete (Moderator/Admin)

* **Create:** `POST /api/v1/theater/movies/` → `MovieCreateSchema` → `MovieDetailResponseSchema`
* **Update:** `PATCH /api/v1/theater/movies/{movie_id}/` → `MoviePatchSchema`
* **Delete:** `DELETE /api/v1/theater/movies/{movie_id}/` (204 No Content; blocked if already purchased)

### Favorites

* **Add:** `POST /api/v1/theater/favorites/{movie_id}/` → 201 Created
* **Remove:** `DELETE /api/v1/theater/favorites/{movie_id}/` → 204 No Content
* **List:** `GET /api/v1/theater/favorites/`

  * Supports same `page`, `per_page`, and filter params as movie list
  * Returns only your favorited movies

## Genres 🎭

Organize and manage movie categories:

* 📋 **List Genres**
  **GET** `/api/v1/theater/genres/`

  * **Query params:**

    * `page` (int, default 1)
    * `per_page` (int, default 10, max 50)
  * **Response:**

    ```json
    {
      "genres": [
        { "id": 1, "name": "Action" },
        { "id": 2, "name": "Drama" }
      ],
      "total": 25,
      "prev_page": "/api/v1/theater/genres/?page=1&per_page=10",
      "next_page": "/api/v1/theater/genres/?page=3&per_page=10"
    }
    ```
  * **404:** if no genres found.

* 🔍 **Get Genre Details**
  **GET** `/api/v1/theater/genres/{genre_id}/`

  * **Response:**

    ```json
    { "id": 1, "name": "Action" }
    ```
  * **404:** if genre not found.

* ➕ **Create Genre**
  **POST** `/api/v1/theater/genres/`

  ```json
  { "name": "Sci-Fi" }
  ```

  * **Response:** returns the new genre object.
  * **400:** if a genre with that name already exists.

* ✏️ **Update Genre**
  **PUT** `/api/v1/theater/genres/{genre_id}/`

  ```json
  { "name": "Science Fiction" }
  ```

  * **Response:** returns the updated genre.
  * **404:** if genre not found.
  * **400:** if the new name conflicts with an existing genre.

* 🗑️ **Delete Genre**
  **DELETE** `/api/v1/theater/genres/{genre_id}/`

  * **Response:** `{ "detail": "Genre deleted successfully" }`
  * **404:** if genre not found.

## Stars 🌟

Manage actors/actresses featured in movies:

* 📋 **List Stars**
  **GET** `/api/v1/theater/stars/?page={page}&per_page={per_page}`

  * **Query params:**

    * `page` (int, default 1)
    * `per_page` (int, max 50)
  * **Response:**

    ```json
    {
      "stars": [
        { "id": 1, "name": "Robert Downey Jr." },
        { "id": 2, "name": "Scarlett Johansson" }
      ],
      "total_items": 100,
      "total_pages": 10,
      "prev_page": "/api/v1/theater/stars/?page=1&per_page=10",
      "next_page": "/api/v1/theater/stars/?page=3&per_page=10"
    }
    ```
  * **404 Not Found** if no stars exist.

* 🔍 **Get Star Details**
  **GET** `/api/v1/theater/stars/{star_id}/`

  * **Response:**

    ```json
    { "id": 1, "name": "Robert Downey Jr." }
    ```
  * **404 Not Found** if the star isn’t found.

* ➕ **Create Star**
  **POST** `/api/v1/theater/stars/`

  ```json
  { "name": "Chris Evans" }
  ```

  * **Response:** returns the new star object (`StarDetailSchema`).
  * **400 Bad Request** if a star with that name already exists.

* ✏️ **Update Star**
  **PUT** `/api/v1/theater/stars/{star_id}/`

  ```json
  { "name": "Chris Hemsworth" }
  ```

  * **Response:** returns the updated star.
  * **404 Not Found** if the star isn’t found.
  * **400 Bad Request** if the new name conflicts.

* 🗑️ **Delete Star**
  **DELETE** `/api/v1/theater/stars/{star_id}/`

  * **204 No Content** on success.
  * **404 Not Found** if the star isn’t found.


## Shopping Cart 🛒

Easily manage your movie picks before checkout:

* ✏️ **Create Cart**
  **POST** `/api/v1/theater/carts/create/`

  ```json
  { "user_id": 1 }
  ```

  Creates a new cart for the given user.
  • **409 Conflict** if a cart already exists for this user.

* ➕ **Add Movie**
  **POST** `/api/v1/theater/carts/add/`

  ```json
  { "cart_id": 10, "movie_id": 123 }
  ```

  Adds the specified movie to the cart.
  • **400 Bad Request** if the cart or movie doesn’t exist.
  • **409 Conflict** if the movie is already in the cart.

* ➖ **Remove Movie**
  **POST** `/api/v1/theater/carts/remove/`

  ```json
  { "cart_id": 10, "movie_id": 123 }
  ```

  Removes the specified movie from the cart.
  • **400 Bad Request** if the cart is empty or item not found.

* 🧹 **Clear Cart**
  **POST** `/api/v1/theater/carts/clear/`

  ```json
  { "cart_id": 10 }
  ```

  Empties all items from the cart.
  • **400 Bad Request** if there are no items in the cart.

* 📋 **List Cart Items**
  **POST** `/api/v1/theater/carts/cart_item_list/`

  ```json
  { "cart_id": 10 }
  ```

  Returns a list of movies in the cart, each with title, price, genre, and release year.
  • **404 Not Found** if the cart has no items.

## Orders 📦

Place orders from your cart and track their status:

* 📝 **Create Order**
  **POST** `/api/v1/theater/orders/`

  ```json
  { "movie_ids": [123, 456] }
  ```

  • Converts the specified cart items into a **PENDING** order.
  • Validates that each movie is in your cart, not already purchased, and no duplicates in pending orders.
  • Calculates `total_amount` and returns full order details, including `order_items`.

* 👤 **List My Orders**
  **GET** `/api/v1/theater/orders/`
  **Optional query:** `?status=PENDING|PAID|CANCELED`
  • Retrieves all orders for the current user, filtered by status if provided.

* 🔍 **Get Order**
  **GET** `/api/v1/theater/orders/{order_id}/`
  • Returns the details of one of your orders.
  • Returns 403 if you try to access another user’s order.

* 🛠️ **Admin: List All Orders**
  **GET** `/api/v1/theater/admin/orders/`
  **Query filters:** `?status=&user_id=&from_date=&to_date=`
  • Allows admins to view and filter every user’s orders by status, user, or date range.

## Payments 💳

Handle secure transactions via Stripe and track payment history:

* 🔗 **Create Checkout Session**
  **POST** `/api/v1/theater/payments/create-session/{order_id}`
  • Fetches your pending order and verifies the total.
  • If a session already exists, returns its URL and status.
  • Otherwise, creates a new `Payment` record (PENDING), initializes a Stripe Checkout session, saves its `payment_intent_id`, and returns:

  ```json
  {
    "payment_id": 42,
    "checkout_url": "https://checkout.stripe.com/…",
    "status": "PENDING"
  }
  ```

* 🔔 **Stripe Webhook**
  **POST** `/api/v1/theater/payments/webhook`
  • Listens for `checkout.session.completed` → marks `Payment` as SUCCESSFUL & `Order` as PAID, then emails confirmation.
  • Listens for `checkout.session.expired` → marks PENDING payments as CANCELED.

* 👥 **List My Payments**
  **GET** `/api/v1/theater/payments/`
  **Optional query:** `?status=PENDING|SUCCESSFUL|CANCELED`
  • Returns all your payments with order details.

* 🛠️ **Admin: List All Payments**
  **GET** `/api/v1/theater/admin/payments/`
  **Filters:** `?status=&user_id=&from_date=&to_date=`
  • View and filter every user’s transactions by status, user, or date range.

* ✅ **Success & Cancel Redirects**
  **GET** `/api/v1/theater/payments/success`
  **GET** `/api/v1/theater/payments/cancel`
  • Simple JSON responses indicating payment outcome.

---

## Running the Project 🚀

This section will help you quickly get your Online-Cinema-Service project up and running on your local machine. We use **Docker Compose** for easy setup of all necessary services.

### Prerequisites

Before you begin, ensure you have the following installed on your system:

* **Docker:** [Official Documentation](https://docs.docker.com/get-docker/)
* **Docker Compose:** Usually installed automatically with Docker Desktop.

### Steps to Run

1.  **Clone the Repository:**
    First, clone the project repository to your local computer:

    ```bash
    git clone <YOUR_REPOSITORY_URL>
    cd Online-Cinema-Service # Navigate to the project's root directory
    ```

2.  **Configure Environment Variables:**
    The project uses environment variables for configuration. You need to create a `.env` file in the project's root directory.

    ```bash
    cp .env.example .env # If you have a .env.example file
    ```

    Open the **.env** file and fill in the required data. **Important:** Replace placeholder values with your own. Do not use real production keys in a testing environment.

    *Example `.env` content:*

    ```ini
    # PostgreSQL
    POSTGRES_DB=movies_db
    POSTGRES_DB_PORT=5432
    POSTGRES_USER=your_postgres_user
    POSTGRES_PASSWORD=your_postgres_password
    POSTGRES_HOST=db # For Docker Compose

    # pgAdmin
    PGADMIN_DEFAULT_EMAIL=your_email@example.com
    PGADMIN_DEFAULT_PASSWORD=your_pgadmin_password

    # JWT keys (Generate your own, e.g., using Python `secrets.token_urlsafe(32)`)
    SECRET_KEY_ACCESS=your_jwt_access_secret_key
    SECRET_KEY_REFRESH=your_jwt_refresh_secret_key
    JWT_SIGNING_ALGORITHM=HS256

    # MailHog (for development/testing emails)
    MAILHOG_USER=your_mailhog_user
    MAILHOG_PASSWORD=your_mailhog_password

    # Email (for sending activation and password reset emails)
    EMAIL_HOST=mailhog # Points to the MailHog service in Docker Compose
    EMAIL_PORT=1025
    EMAIL_HOST_USER=testuser # Can be anything for MailHog
    EMAIL_HOST_PASSWORD=test_password # Can be anything for MailHog
    EMAIL_USE_TLS=False

    # MinIO (local S3-compatible object storage)
    MINIO_ROOT_USER=your_minio_root_user
    MINIO_ROOT_PASSWORD=your_minio_root_password
    MINIO_HOST=minio # Points to the MinIO service in Docker Compose
    MINIO_PORT=9000
    MINIO_STORAGE=theater-storage

    # Stripe (use test keys for development)
    STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
    STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
    STRIPE_WEBHOOK_SECRET=whsec_your_stripe_webhook_secret

    # Redis
    REDIS_HOST=redis
    REDIS_PORT=6379
    REDIS_DB=0
    ```

3.  **Choose and Run Your Environment:**
    You can run the project in different configurations: for development, for testing, or for production.

    ---

    ### **Run for Development (dev)**

    This configuration includes all services necessary for local development, such as the database, pgAdmin, MailHog (for viewing outgoing emails), MinIO (for files), and Celery.

    From the project's root directory, execute:

    ```bash
    docker compose -f docker-compose.dev.yml up --build -d
    ```

    * `docker compose -f docker-compose.dev.yml`: Specifies which Docker Compose file to use.
    * `up`: Starts the services.
    * `--build`: Rebuilds container images (recommended for the first run or after code changes).
    * `-d`: Runs containers in detached (background) mode.

    ---

    ### **Run for Production (prod)**

    This configuration is optimized for production. However, note that in your `prod` file, the `web` service still uses the `run_web_server_dev.sh` command and mounts the source code. For true production, you'll likely need Gunicorn/Uvicorn for WSGI/ASGI, and static files served via Nginx.

    To run the production version (using your current `prod` file):

    ```bash
    docker compose -f docker-compose.prod.yml up --build -d
    ```

    **Important:** For a real production setup, you should:
    * Change the `web` service command to use a production-ready server (e.g., Uvicorn with Gunicorn workers).
    * Avoid mounting `./src` as a volume; instead, copy the code during image build.
    * Configure Nginx for proxying and serving static files.
    * Set up SSL certificates.
    * Ensure `LOG_LEVEL` is not `debug` in production.

    ---

    ### **Run for Tests (tests)**

    This configuration is exclusively for running automated tests. It sets up an isolated environment with MailHog, MinIO, and Redis specifically for test runs.

    To run the tests:

    ```bash
    docker compose -f docker-compose.tests.yml up --build --abort-on-container-exit
    ```

    * `--abort-on-container-exit`: Stops all containers if one of them (in this case, `web`, which runs `pytest`) exits.
    * After the tests complete, you'll see the results in the console.

    ---

4.  **Execute Database Migrations (for `dev` and `prod`):**
    After starting the containers (`dev` or `prod`), you need to apply database migrations to create the necessary tables and schemas.

    ```bash
    docker compose -f docker-compose.dev.yml exec migrator /commands/run_migration.sh
    # Or for prod:
    # docker compose -f docker-compose.prod.yml exec migrator /commands/run_migration.sh
    ```

    Note that your `docker-compose.dev.yml` (and `prod.yml`) includes a separate `migrator` service responsible for running migrations. It starts, executes migrations, and then exits.

5.  **Create a Superuser (Admin) (for `dev` and `prod`):**
    If you want to access the admin panel or test administrator functionality, create a superuser:

    ```bash
    docker compose -f docker-compose.dev.yml exec web python -m src.commands.create_superuser
    # Or for prod:
    # docker compose -f docker-compose.prod.yml exec web python -m src.commands.create_superuser
    ```

    Follow the prompts in your terminal to set a username, email address, and password.

6.  **Verify Service Operation:**
    Once running (in `dev` or `prod` mode), your Online Cinema API should be accessible at: `http://localhost:8000`.

    * **API:** `http://localhost:8000/api/v1/...`
    * **pgAdmin:** `http://localhost:3333` (Use the email and password from your `.env` for login).
    * **MailHog:** `http://localhost:8025` (Here you'll see all outgoing emails).
    * **MinIO Console:** `http://localhost:9001` (For managing objects).

---

### Removing Running Containers and Volumes

To stop and remove all running services, as well as their associated data volumes (database, pgAdmin, MinIO), execute:

```bash
docker compose -f docker-compose.dev.yml down -v
# Or for prod:
# docker compose -f docker-compose.prod.yml down -v
# Or for tests:
# docker compose -f docker-compose.tests.yml down -v
```

* `down`: Stops and removes containers, networks, and images.
* `-v`: Also removes anonymous volumes. **Be careful, this will delete your data!** If you want to preserve your data, just omit `-v`.

---

## Key Technologies 🚀
This project leverages a modern and powerful stack to deliver a fast, secure, and scalable online cinema service. Here are some of the core technologies that make it all work:

### FastAPI: 
Our API's backbone. FastAPI is a high-performance Python web framework known for its incredible speed, modern asynchronous capabilities, and excellent developer experience thanks to standard Python type hints. It allows us to build robust API endpoints quickly and efficiently.

### SQLAlchemy & Alembic: 
For robust data management. We use SQLAlchemy as our powerful Object-Relational Mapper (ORM), which provides a flexible and efficient way to interact with our PostgreSQL database. To manage database schema changes and ensure smooth updates, Alembic handles our database migrations. This combination ensures data integrity and simplifies database evolution.

### Celery & Redis: 
Powering background tasks. Celery is an asynchronous task queue that handles long-running operations like email confirmations for account activation and automated token cleanup. Redis serves as our high-performance message broker, ensuring these tasks are processed quickly and reliably without blocking the main application.

### Stripe: 
For secure payments. We've integrated Stripe to provide a secure and seamless payment processing experience. This allows users to easily manage their transactions and ensures all financial operations are handled with industry-leading security standards.

### Docker & Docker Compose: 
Simplifying development and deployment. The entire application stack, including the API, database, and background services, is containerized using Docker. Docker Compose orchestrates these containers, making it incredibly easy to set up, run, and manage the project across different environments (development, testing, and production) with consistent results.