import os
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from unittest.mock import patch, AsyncMock, Mock

from config import get_accounts_email_notificator
from main import app
from database import Base, get_db
from database.models.accounts import UserModel, UserGroupModel, UserGroupEnum
from database.models.movies import MovieModel, CertificationModel
from database.models.carts import CartModel, CartItemModel
from security.token_manager import JWTAuthManager

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine_test = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(bind=engine_test, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(autouse=True, scope="function")
async def mock_stripe():
    with patch("stripe.checkout.Session.create", new_callable=Mock) as mock_create:
        mock_session = Mock()
        mock_session.payment_intent = "pi_test"
        mock_session.url = "https://test-checkout-session.url/"
        mock_create.return_value = mock_session

        with patch("stripe.checkout.Session.retrieve", new_callable=Mock) as mock_retrieve:
            mock_retrieve_session = Mock()
            mock_retrieve_session.url = "https://test-checkout-session.url/"
            mock_retrieve.return_value = mock_retrieve_session

            yield


@pytest_asyncio.fixture(autouse=True, scope="function")
async def setup_database():
    os.environ["STRIPE_SECRET_KEY"] = "sk_test_dummy"
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_dummy"
    os.environ["SECRET_KEY_ACCESS"] = "838qKq7dGp34hWij3c8txA5ZD2qm9ybt"
    os.environ["SECRET_KEY_REFRESH"] = "cFzRk8kllHMW71wQKLXBqDzl24fkhisw"
    os.environ["JWT_SIGNING_ALGORITHM"] = "HS256"

    app.dependency_overrides[get_db] = override_get_db

    with patch("config.get_accounts_email_notificator", return_value=AsyncMock()):
        async with engine_test.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
        await engine_test.dispose()
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
def jwt_auth_manager():
    access_key = os.getenv("SECRET_KEY_ACCESS")
    refresh_key = os.getenv("SECRET_KEY_REFRESH")
    algorithm = os.getenv("JWT_SIGNING_ALGORITHM")
    return JWTAuthManager(access_key, refresh_key, algorithm)


@pytest_asyncio.fixture
async def auth_headers(jwt_auth_manager: JWTAuthManager, seed_user_movie_cart: UserModel):
    user = seed_user_movie_cart
    access_token = jwt_auth_manager.create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def seed_user_movie_cart(db_session: AsyncSession):
    user_group = await db_session.scalar(select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER))
    if not user_group:
        user_group = UserGroupModel(id=1, name=UserGroupEnum.USER)
        db_session.add(user_group)
        await db_session.flush()

    user = UserModel.create(email="test@example.com", raw_password="StrongPassword123!", group_id=user_group.id)
    user.is_active = True
    db_session.add(user)

    certification = CertificationModel(id=1, name="PG-13")
    db_session.add(certification)

    movie = MovieModel(
        id=1,
        name="Test Movie",
        year=2024,
        time=120,
        imdb=8.5,
        votes=1000,
        meta_score=80,
        gross=100.0,
        description="A test movie description.",
        price=9.99,
        certification_id=1,
        uuid="123e4567-e89b-12d3-a456-426614174000"
    )
    db_session.add(movie)
    await db_session.flush()

    cart = CartModel(user_id=user.id)
    db_session.add(cart)
    await db_session.flush()

    cart_item = CartItemModel(cart_id=cart.id, movie_id=movie.id)
    db_session.add(cart_item)

    await db_session.commit()
    await db_session.refresh(user)
    yield user


@pytest_asyncio.fixture
async def another_user(db_session: AsyncSession):
    user_group = await db_session.scalar(select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER))
    if not user_group:
        user_group = UserGroupModel(id=1, name=UserGroupEnum.USER)
        db_session.add(user_group)
        await db_session.flush()

    user = UserModel.create(email="another@example.com", raw_password="AnotherPassword123!", group_id=user_group.id)
    user.is_active = True
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def client():
    mock_email_sender = AsyncMock()
    app.dependency_overrides[get_accounts_email_notificator] = lambda: mock_email_sender

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
